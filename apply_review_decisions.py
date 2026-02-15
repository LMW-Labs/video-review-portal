"""
Apply Review Decisions
======================
Takes the reviewed CSV and generates the final clean dataset.

Usage:
    python apply_review_decisions.py

Input:
    - videos_for_review.csv (with reviewer columns filled in)
    - videos_clean.csv (videos that passed automated checks)

Output:
    - categorized_videos_final.csv: Clean training dataset
    - videos_removed.csv: Log of removed videos
    - videos_to_retranscribe.csv: Videos needing re-transcription
    - apply_summary.txt: Summary of changes made
"""

import csv
from pathlib import Path
from collections import Counter

# Configuration
REVIEW_INPUT = "videos_for_review.csv"
CLEAN_INPUT = "videos_clean.csv"
FINAL_OUTPUT = "categorized_videos_final.csv"
REMOVED_OUTPUT = "videos_removed.csv"
RETRANSCRIBE_OUTPUT = "videos_to_retranscribe.csv"
SUMMARY_OUTPUT = "apply_summary.txt"


def main():
    # Check input files exist
    if not Path(REVIEW_INPUT).exists():
        print(f"Error: {REVIEW_INPUT} not found")
        return
    if not Path(CLEAN_INPUT).exists():
        print(f"Error: {CLEAN_INPUT} not found")
        return

    # Read reviewed videos
    with open(REVIEW_INPUT, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        reviewed_rows = list(reader)

    # Read clean videos
    with open(CLEAN_INPUT, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        clean_rows = list(reader)

    print(f"Loaded {len(reviewed_rows)} reviewed videos")
    print(f"Loaded {len(clean_rows)} pre-approved clean videos")

    # Process reviewed videos
    final_rows = []
    removed_rows = []
    retranscribe_rows = []
    stats = Counter()

    # Check for missing decisions
    missing_decisions = [r for r in reviewed_rows if not r.get("reviewer_decision", "").strip()]
    if missing_decisions:
        print(f"\nWARNING: {len(missing_decisions)} videos have no reviewer_decision!")
        print("These will be SKIPPED. Please review:")
        for r in missing_decisions[:10]:
            print(f"  - {r.get('filename', 'unknown')}")
        if len(missing_decisions) > 10:
            print(f"  ... and {len(missing_decisions) - 10} more")
        print()

    for row in reviewed_rows:
        decision = row.get("reviewer_decision", "").strip().upper()
        new_category = row.get("reviewer_category", "").strip()
        notes = row.get("reviewer_notes", "").strip()

        if not decision:
            stats["SKIPPED_NO_DECISION"] += 1
            continue

        if decision == "KEEP":
            final_rows.append({
                "filename": row["filename"],
                "drill_type": row["current_category"],
                "difficulty": row["difficulty"],
                "transcript": row.get("full_transcript", row.get("transcript_preview", "")),
                "review_notes": notes,
            })
            stats["KEPT"] += 1

        elif decision == "RECATEGORIZE":
            if not new_category:
                print(f"WARNING: RECATEGORIZE without new category: {row['filename']}")
                stats["RECATEGORIZE_NO_CATEGORY"] += 1
                continue
            final_rows.append({
                "filename": row["filename"],
                "drill_type": new_category,
                "difficulty": row["difficulty"],
                "transcript": row.get("full_transcript", row.get("transcript_preview", "")),
                "review_notes": notes,
            })
            stats["RECATEGORIZED"] += 1

        elif decision == "REMOVE" or decision == "DUPLICATE":
            removed_rows.append({
                "filename": row["filename"],
                "original_category": row["current_category"],
                "reason": decision,
                "notes": notes,
            })
            stats["REMOVED"] += 1

        elif decision == "RE_TRANSCRIBE" or decision == "RETRANSCRIBE":
            retranscribe_rows.append({
                "filename": row["filename"],
                "current_category": row["current_category"],
                "suggested_category": row.get("suggested_category", ""),
                "notes": notes,
            })
            stats["NEEDS_RETRANSCRIBE"] += 1

        elif decision == "SKIP":
            stats["SKIPPED_BY_REVIEWER"] += 1

        else:
            print(f"WARNING: Unknown decision '{decision}' for {row['filename']}")
            stats["UNKNOWN_DECISION"] += 1

    # Add clean videos (already passed automated checks)
    for row in clean_rows:
        final_rows.append({
            "filename": row["filename"],
            "drill_type": row["current_category"],
            "difficulty": row["difficulty"],
            "transcript": row.get("full_transcript", ""),
            "review_notes": "Auto-approved",
        })
        stats["AUTO_APPROVED"] += 1

    # Write final output
    final_fields = ["filename", "drill_type", "difficulty", "transcript", "review_notes"]
    with open(FINAL_OUTPUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=final_fields)
        writer.writeheader()
        writer.writerows(final_rows)
    print(f"Wrote {len(final_rows)} videos to {FINAL_OUTPUT}")

    # Write removed videos log
    if removed_rows:
        removed_fields = ["filename", "original_category", "reason", "notes"]
        with open(REMOVED_OUTPUT, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=removed_fields)
            writer.writeheader()
            writer.writerows(removed_rows)
        print(f"Wrote {len(removed_rows)} removed videos to {REMOVED_OUTPUT}")

    # Write retranscribe list
    if retranscribe_rows:
        retranscribe_fields = ["filename", "current_category", "suggested_category", "notes"]
        with open(RETRANSCRIBE_OUTPUT, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=retranscribe_fields)
            writer.writeheader()
            writer.writerows(retranscribe_rows)
        print(f"Wrote {len(retranscribe_rows)} videos to {RETRANSCRIBE_OUTPUT}")

    # Write summary
    summary = f"""
APPLY REVIEW DECISIONS SUMMARY
==============================

STATISTICS
----------
"""
    for stat, count in stats.most_common():
        summary += f"  {stat}: {count}\n"

    summary += f"""
FINAL COUNTS
------------
  Videos in final dataset: {len(final_rows)}
  Videos removed: {len(removed_rows)}
  Videos needing re-transcription: {len(retranscribe_rows)}

OUTPUT FILES
------------
  {FINAL_OUTPUT} - Use this for training
  {REMOVED_OUTPUT} - Log of removed videos
  {RETRANSCRIBE_OUTPUT} - Videos to re-process

CATEGORY DISTRIBUTION IN FINAL DATASET
--------------------------------------
"""
    category_counts = Counter(r["drill_type"] for r in final_rows)
    for category, count in category_counts.most_common():
        pct = 100 * count / len(final_rows) if final_rows else 0
        summary += f"  {category}: {count} ({pct:.1f}%)\n"

    with open(SUMMARY_OUTPUT, "w", encoding="utf-8") as f:
        f.write(summary)

    print(summary)


if __name__ == "__main__":
    main()
