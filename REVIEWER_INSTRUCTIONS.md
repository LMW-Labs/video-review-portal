# Video Categorization Review Guide

## Overview

You've been given a spreadsheet (`videos_for_review.csv`) containing training videos that need manual review. Each video has been flagged by our automated system for one or more issues. Your job is to make decisions about each video to ensure our training dataset is clean and accurate.

**Time estimate**: ~2-3 minutes per video, depending on whether you need to watch it.

---

## Getting Started

1. Open `videos_for_review.csv` in Excel or Google Sheets
2. Videos are sorted by priority - start from the top
3. For each row, you'll fill in THREE columns:
   - `reviewer_decision`
   - `reviewer_category`
   - `reviewer_notes` (optional but helpful)

---

## Understanding the Columns

| Column | Description |
|--------|-------------|
| `filename` | The video file name |
| `video_link` | **Click to watch the video in Google Drive** |
| `current_category` | What the AI originally classified this as |
| `suggested_category` | What our keyword analysis suggests it might be |
| `confidence` | 0-100 score. Lower = more likely to be wrong |
| `action` | Recommended action (see below) |
| `issues` | What problems were detected |
| `difficulty` | Beginner/Intermediate/Advanced |
| `transcript_preview` | First 100 characters of the audio transcript |

**Tip**: The `video_link` column contains clickable Google Drive links. Just click to watch the video in your browser.

---

## Understanding Actions

The `action` column tells you what the system recommends:

| Action | Meaning | What You Do |
|--------|---------|-------------|
| **REMOVE** | Video isn't a drill (celebration, goodbye, etc.) | Confirm removal or override if it's actually useful |
| **RE_TRANSCRIBE** | Audio transcript is garbage/corrupted | Flag for re-transcription, or remove if video is unusable |
| **RE_CATEGORIZE** | Marked "Other" but might be a real drill | Watch video or read transcript, assign correct category |
| **REVIEW** | Low confidence, needs human eyes | Review and confirm or correct the category |
| **CHECK_DUPLICATE** | Filename suggests it might be a duplicate | Check if it's truly a duplicate or a different take |

---

## Valid Categories

When filling in `reviewer_category`, use one of these exact values:

| Category | Description |
|----------|-------------|
| `Route Running` | Running specific routes (slants, posts, outs, etc.) |
| `Footwork` | Foot placement, shuffling, hip movement, stance work |
| `Release Moves` | Getting off the line, beating press coverage, hand fighting |
| `Speed/Conditioning` | Sprints, acceleration drills, conditioning work |
| `Agility` | Lateral movement, change of direction, cone drills |
| `Catching/Hands` | Ball catching, hand positioning, grip work |
| `Body Control` | Balance, body positioning, spatial awareness |

---

## Valid Decisions

When filling in `reviewer_decision`, use one of these exact values:

| Decision | When to Use |
|----------|-------------|
| `KEEP` | Video is correctly categorized, keep as-is |
| `RECATEGORIZE` | Video is good but needs different category (fill in `reviewer_category`) |
| `REMOVE` | Video should be removed from training data |
| `RE_TRANSCRIBE` | Video is good but needs audio re-transcribed |
| `DUPLICATE` | This is a duplicate of another video, remove it |
| `SKIP` | You can't determine - flag for someone else to review |

---

## Understanding Issues

The `issues` column may contain one or more of these flags:

| Issue | Meaning |
|-------|---------|
| `EMPTY_TRANSCRIPT` | No audio transcript at all |
| `SHORT_TRANSCRIPT` | Very short transcript (< 20 characters) |
| `GARBAGE_TRANSCRIPT` | Transcript contains nonsense, foreign characters, or corruption |
| `NON_DRILL_CONTENT` | Content appears to be celebration, intro/outro, casual chat |
| `UNCATEGORIZED` | Was marked as "Other" - needs proper category |
| `POSSIBLE_DUPLICATE` | Filename has (1), (2), etc. suggesting duplicate |

---

## Quick Decision Guide

### If `action` = REMOVE:
1. Read the `transcript_preview`
2. If it's clearly not a drill → `reviewer_decision` = `REMOVE`
3. If it might be useful → watch the video, then decide

### If `action` = RE_TRANSCRIBE:
1. Look at `transcript_preview` - is it garbage?
2. If garbage but video might be good → `reviewer_decision` = `RE_TRANSCRIBE`
3. If video is also bad → `reviewer_decision` = `REMOVE`

### If `action` = RE_CATEGORIZE:
1. Read the `transcript_preview` carefully
2. Check `suggested_category` - does it make sense?
3. If yes → `reviewer_decision` = `RECATEGORIZE`, `reviewer_category` = (the suggested one)
4. If no → watch video, pick correct category
5. If not a real drill → `reviewer_decision` = `REMOVE`

### If `action` = REVIEW:
1. Compare `current_category` with `suggested_category`
2. Read transcript
3. If current seems right → `reviewer_decision` = `KEEP`
4. If suggested seems better → `reviewer_decision` = `RECATEGORIZE`
5. If unsure → watch the video

### If `action` = CHECK_DUPLICATE:
1. Look for the base filename (without the number)
2. If both exist and are identical → `reviewer_decision` = `DUPLICATE`
3. If they're different takes → `reviewer_decision` = `KEEP`

---

## Examples

### Example 1: Clear removal
```
filename: IMG_0627.MOV
transcript_preview: "celebrationじゃあ"
action: REMOVE
```
**Decision**: This is a celebration clip with garbage transcript
- `reviewer_decision` = `REMOVE`
- `reviewer_category` = (leave blank)
- `reviewer_notes` = "Celebration clip, not a drill"

### Example 2: Needs recategorization
```
filename: IMG_2077.MOV
current_category: Other
suggested_category: Route Running
transcript_preview: "Ready, go! Good, you're straight, good."
action: RE_CATEGORIZE
```
**Decision**: Transcript suggests route running drill
- `reviewer_decision` = `RECATEGORIZE`
- `reviewer_category` = `Route Running`
- `reviewer_notes` = "Straight line route drill"

### Example 3: Garbage transcript, good video
```
filename: IMG_0628.MOV
current_category: Other
transcript_preview: "Katsuma Annに、任務に einenがある"
action: RE_TRANSCRIBE
issues: GARBAGE_TRANSCRIPT
```
**Decision**: Need to watch video to know if it's worth keeping
- If video shows clear drill → `reviewer_decision` = `RE_TRANSCRIBE`
- If video is useless → `reviewer_decision` = `REMOVE`

### Example 4: Correctly categorized
```
filename: IMG_5067.MOV
current_category: Release Moves
suggested_category: Release Moves
confidence: 85
transcript_preview: "I want you to punch on that bat..."
action: REVIEW
```
**Decision**: Current category looks correct
- `reviewer_decision` = `KEEP`
- `reviewer_category` = (leave blank)
- `reviewer_notes` = (leave blank)

---

## Tips for Faster Review

1. **Trust high confidence scores** (70+) - they're usually right
2. **Check `suggested_category` first** - it's often correct
3. **Read transcripts before watching videos** - often you can decide without watching
4. **Watch videos only when**:
   - Transcript is garbage
   - Transcript is ambiguous
   - You're genuinely unsure
5. **Use the notes column** for anything unusual - helps the next person

---

## When You're Done

1. Save your reviewed CSV
2. Make sure every row has a `reviewer_decision` value
3. Hand off to the person running `apply_review_decisions.py`

---

## Questions?

If you encounter videos you can't categorize or have questions about the process, add a note in `reviewer_notes` and set `reviewer_decision` = `SKIP`. Someone else can review these later.
