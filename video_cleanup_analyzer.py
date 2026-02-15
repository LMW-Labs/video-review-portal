"""
Video Categorization Cleanup Analyzer
=====================================
Analyzes categorized_videos.csv and generates a review spreadsheet
for manual reviewers to clean up the training data.

Usage:
    python video_cleanup_analyzer.py [--skip-drive]

Options:
    --skip-drive    Skip Google Drive link fetching (use if no API access)

Output:
    - videos_for_review.csv: Videos needing manual review
    - videos_clean.csv: Videos that passed automated checks
    - cleanup_summary.txt: Statistics and summary

Google Drive Setup:
    1. Enable Google Drive API in Google Cloud Console
    2. Create OAuth 2.0 credentials (Desktop app)
    3. Download credentials.json to this directory
    4. First run will open browser for authentication
"""

import csv
import re
import sys
import pickle
from pathlib import Path
from collections import Counter

# Configuration
INPUT_FILE = "categorized_videos.csv"
REVIEW_OUTPUT = "videos_for_review.csv"
CLEAN_OUTPUT = "videos_clean.csv"
SUMMARY_OUTPUT = "cleanup_summary.txt"

# Google Drive configuration
DRIVE_FOLDER_ID = "1xOxVmoddh6gBoywrrva2M5VWKwaFMmji"  # Training videos folder
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.pickle"

# Valid drill types for auto-suggestion
VALID_DRILL_TYPES = [
    "Route Running",
    "Footwork",
    "Release Moves",
    "Speed/Conditioning",
    "Agility",
    "Catching/Hands",
    "Body Control"
]

# Keyword patterns for auto-categorization suggestions
CATEGORY_KEYWORDS = {
    "Route Running": [
        r"route", r"stick", r"outside", r"inside", r"cut", r"break",
        r"slant", r"post", r"corner", r"dig", r"out route", r"in route",
        r"get there", r"not back here"
    ],
    "Footwork": [
        r"feet", r"foot", r"shuffle", r"hip", r"step", r"stance",
        r"balance", r"plant", r"wider", r"footwork"
    ],
    "Release Moves": [
        r"release", r"push away", r"punch", r"drive", r"off the line",
        r"get away", r"separation", r"hands? with it", r"swap"
    ],
    "Speed/Conditioning": [
        r"go go go", r"push push", r"speed", r"fast", r"sprint",
        r"accelerat", r"burst", r"explosive", r"conditioning"
    ],
    "Agility": [
        r"agility", r"lateral", r"change of direction", r"quick",
        r"stopping", r"starting"
    ],
    "Catching/Hands": [
        r"catch", r"hands", r"ball", r"grip", r"receiving"
    ]
}

# Patterns that indicate garbage transcripts
GARBAGE_PATTERNS = [
    r"[\u4e00-\u9fff]",  # Chinese characters
    r"[\u3040-\u309f\u30a0-\u30ff]",  # Japanese hiragana/katakana
    r"[\uac00-\ud7af]",  # Korean characters
    r"[\u0400-\u04ff]",  # Cyrillic
    r"^(go|good|yep|yes|ok|okay|bye|thank you|thanks)\.?$",  # Single word responses
    r"^[a-z]{1,3}$",  # Very short single words
    r"(.)\1{5,}",  # Repeated characters (e.g., "aaaaa")
    r"^[\W\s]*$",  # Only punctuation/whitespace
]

# Patterns indicating non-drill content
NON_DRILL_PATTERNS = [
    r"bye bye",
    r"show this to you guys",
    r"i'?m sorry",
    r"thank you\. thank you",
    r"celebration",
    r"what is she doing",
    r"fucking hell",
    r"水邊",  # "waterside" in Chinese
]


def detect_issues(row):
    """Analyze a video row and return list of issues found."""
    issues = []
    transcript = row.get("transcript", "").strip()
    drill_type = row.get("drill_type", "").strip()
    description = row.get("description", "").strip()

    # Check for empty/short transcript
    if len(transcript) < 5:
        issues.append("EMPTY_TRANSCRIPT")
    elif len(transcript) < 20:
        issues.append("SHORT_TRANSCRIPT")

    # Check for garbage patterns
    for pattern in GARBAGE_PATTERNS:
        if re.search(pattern, transcript, re.IGNORECASE):
            issues.append("GARBAGE_TRANSCRIPT")
            break

    # Check for non-drill content
    for pattern in NON_DRILL_PATTERNS:
        if re.search(pattern, transcript, re.IGNORECASE):
            issues.append("NON_DRILL_CONTENT")
            break

    # Check if categorized as "Other"
    if drill_type.lower() == "other":
        issues.append("UNCATEGORIZED")

    # Check for duplicate filename pattern (indicates re-processed video)
    filename = row.get("filename", "")
    if re.search(r"\(\d+\)\.MOV$", filename, re.IGNORECASE):
        issues.append("POSSIBLE_DUPLICATE")

    return issues


def suggest_category(transcript):
    """Suggest a category based on transcript keywords."""
    transcript_lower = transcript.lower()
    scores = Counter()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if re.search(keyword, transcript_lower):
                scores[category] += 1

    if scores:
        best_match = scores.most_common(1)[0]
        if best_match[1] >= 1:  # At least one keyword match
            return best_match[0]

    return ""


def calculate_confidence(row, issues, suggested_category):
    """Calculate confidence score for the current categorization."""
    score = 100

    # Deduct for issues
    issue_penalties = {
        "EMPTY_TRANSCRIPT": 40,
        "SHORT_TRANSCRIPT": 20,
        "GARBAGE_TRANSCRIPT": 35,
        "NON_DRILL_CONTENT": 30,
        "UNCATEGORIZED": 25,
        "POSSIBLE_DUPLICATE": 10,
    }

    for issue in issues:
        score -= issue_penalties.get(issue, 10)

    # Bonus if suggested category matches current
    if suggested_category and suggested_category == row.get("drill_type"):
        score += 10

    return max(0, min(100, score))


def determine_action(issues, confidence):
    """Determine recommended action based on issues and confidence."""
    if "NON_DRILL_CONTENT" in issues:
        return "REMOVE"
    if "EMPTY_TRANSCRIPT" in issues or "GARBAGE_TRANSCRIPT" in issues:
        return "RE_TRANSCRIBE"
    if "UNCATEGORIZED" in issues:
        return "RE_CATEGORIZE"
    if confidence < 50:
        return "REVIEW"
    if "POSSIBLE_DUPLICATE" in issues:
        return "CHECK_DUPLICATE"
    return "KEEP"


def get_google_drive_service():
    """Authenticate and return Google Drive API service."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("Google API libraries not installed. Run:")
        print("  pip install google-auth google-auth-oauthlib google-api-python-client")
        return None

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    creds = None

    # Load existing token
    if Path(TOKEN_FILE).exists():
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(CREDENTIALS_FILE).exists():
                print(f"Error: {CREDENTIALS_FILE} not found.")
                print("Download OAuth credentials from Google Cloud Console.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)


def get_base_filename(filename):
    """Extract base filename without duplicate suffix like ' (1)', ' (2)', etc."""
    # Match pattern like "IMG_5121 (2).MOV" -> "IMG_5121.MOV"
    match = re.match(r'^(.+?)\s*\(\d+\)(\.[^.]+)$', filename)
    if match:
        return match.group(1) + match.group(2)
    return filename


def fetch_drive_links(filenames):
    """Fetch Google Drive shareable links for a list of filenames."""
    service = get_google_drive_service()
    if not service:
        return {}

    print(f"Fetching Google Drive links for {len(filenames)} files...")
    links = {}
    drive_file_map = {}  # Maps drive filename -> link

    # Query Drive for video files in folder
    query = f"'{DRIVE_FOLDER_ID}' in parents" if DRIVE_FOLDER_ID else "mimeType contains 'video/'"

    page_token = None
    while True:
        try:
            results = service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name)',
                pageToken=page_token,
                pageSize=100
            ).execute()
        except Exception as e:
            print(f"Error querying Drive: {e}")
            break

        for file in results.get('files', []):
            name = file.get('name', '')
            file_id = file['id']
            drive_file_map[name] = f"https://drive.google.com/file/d/{file_id}/view"

        page_token = results.get('nextPageToken')
        if not page_token:
            break

    print(f"  Found {len(drive_file_map)} files in Drive folder")

    # Map CSV filenames to Drive links (handling duplicates like "IMG_5121 (2).MOV")
    for filename in filenames:
        if filename in drive_file_map:
            # Exact match
            links[filename] = drive_file_map[filename]
        else:
            # Try base filename (without duplicate suffix)
            base = get_base_filename(filename)
            if base in drive_file_map:
                links[filename] = drive_file_map[base]

    # Check for missing files
    not_found = [f for f in filenames if f not in links]
    if not_found:
        print(f"Warning: {len(not_found)} files not found in Drive")
        if len(not_found) <= 10:
            for f in not_found:
                print(f"  - {f}")

    print(f"Found Drive links for {len(links)} / {len(filenames)} files")
    return links


def main():
    # Check for --skip-drive flag
    skip_drive = "--skip-drive" in sys.argv

    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        print(f"Error: {INPUT_FILE} not found in current directory")
        return

    # Read input CSV
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} videos from {INPUT_FILE}")

    # Fetch Google Drive links
    drive_links = {}
    if not skip_drive:
        all_filenames = [row.get("filename", "") for row in rows]
        drive_links = fetch_drive_links(all_filenames)
    else:
        print("Skipping Google Drive link fetching (--skip-drive flag)")


    # Analyze each video
    review_rows = []
    clean_rows = []
    stats = {
        "total": len(rows),
        "clean": 0,
        "needs_review": 0,
        "issues": Counter(),
        "actions": Counter(),
        "by_category": Counter(),
    }

    for row in rows:
        issues = detect_issues(row)
        suggested = suggest_category(row.get("transcript", ""))
        confidence = calculate_confidence(row, issues, suggested)
        action = determine_action(issues, confidence)

        # Track stats
        stats["by_category"][row.get("drill_type", "Unknown")] += 1
        stats["actions"][action] += 1
        for issue in issues:
            stats["issues"][issue] += 1

        # Get Drive link for this video
        filename = row.get("filename", "")
        video_link = drive_links.get(filename, "")

        # Create enriched row
        enriched_row = {
            "filename": filename,
            "video_link": video_link,
            "current_category": row.get("drill_type", ""),
            "suggested_category": suggested,
            "confidence": confidence,
            "action": action,
            "issues": "; ".join(issues) if issues else "None",
            "difficulty": row.get("difficulty", ""),
            "transcript_preview": row.get("transcript", "")[:100] + "..." if len(row.get("transcript", "")) > 100 else row.get("transcript", ""),
            "full_transcript": row.get("transcript", ""),
            "description": row.get("description", ""),
            "coaching_cues": row.get("coaching_cues", ""),
            "equipment": row.get("equipment", ""),
            "focus_area": row.get("focus_area", ""),
            # Reviewer fields
            "reviewer_decision": "",
            "reviewer_category": "",
            "reviewer_notes": "",
        }

        if issues or confidence < 70:
            review_rows.append(enriched_row)
            stats["needs_review"] += 1
        else:
            clean_rows.append(enriched_row)
            stats["clean"] += 1

    # Sort review rows by action priority and confidence
    action_priority = {"REMOVE": 0, "RE_TRANSCRIBE": 1, "RE_CATEGORIZE": 2, "REVIEW": 3, "CHECK_DUPLICATE": 4, "KEEP": 5}
    review_rows.sort(key=lambda x: (action_priority.get(x["action"], 5), x["confidence"]))

    # Write review CSV
    review_fields = [
        "filename", "video_link", "current_category", "suggested_category", "confidence",
        "action", "issues", "difficulty", "transcript_preview",
        "reviewer_decision", "reviewer_category", "reviewer_notes"
    ]

    with open(REVIEW_OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=review_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(review_rows)

    print(f"Wrote {len(review_rows)} videos to {REVIEW_OUTPUT}")

    # Write clean CSV (in original format for training)
    clean_fields = [
        "filename", "video_link", "current_category", "suggested_category", "confidence",
        "difficulty", "equipment", "focus_area", "description",
        "coaching_cues", "full_transcript"
    ]

    with open(CLEAN_OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=clean_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(clean_rows)

    print(f"Wrote {len(clean_rows)} videos to {CLEAN_OUTPUT}")

    # Write summary
    summary = f"""
VIDEO CATEGORIZATION CLEANUP SUMMARY
====================================
Generated by video_cleanup_analyzer.py

OVERVIEW
--------
Total videos analyzed: {stats['total']}
Videos passing checks: {stats['clean']} ({100*stats['clean']/stats['total']:.1f}%)
Videos needing review: {stats['needs_review']} ({100*stats['needs_review']/stats['total']:.1f}%)

RECOMMENDED ACTIONS
-------------------
"""
    for action, count in stats["actions"].most_common():
        summary += f"  {action}: {count} videos\n"

    summary += f"""
ISSUES DETECTED
---------------
"""
    for issue, count in stats["issues"].most_common():
        summary += f"  {issue}: {count} videos\n"

    summary += f"""
CURRENT CATEGORY DISTRIBUTION
-----------------------------
"""
    for category, count in stats["by_category"].most_common():
        summary += f"  {category}: {count} videos\n"

    summary += f"""
OUTPUT FILES
------------
1. {REVIEW_OUTPUT} - Videos requiring manual review
2. {CLEAN_OUTPUT} - Videos that passed automated checks
3. {SUMMARY_OUTPUT} - This summary file

NEXT STEPS
----------
1. Open {REVIEW_OUTPUT} in Excel or Google Sheets
2. Follow the REVIEWER_INSTRUCTIONS.md guide
3. Fill in reviewer_decision, reviewer_category, and reviewer_notes columns
4. Run the apply_review_decisions.py script to generate final clean dataset
"""

    with open(SUMMARY_OUTPUT, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Wrote summary to {SUMMARY_OUTPUT}")
    print("\n" + summary)


if __name__ == "__main__":
    main()
