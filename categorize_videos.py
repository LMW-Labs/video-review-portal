#!/usr/bin/env python3
"""
Video Categorization Script for Training Videos
Uses Whisper for transcription + OpenAI for categorization
"""

import os
import json
import csv
import subprocess
from pathlib import Path
from openai import OpenAI

# ============ CONFIGURATION ============
VIDEO_FOLDER = r"G:\My Drive\New folder"  # Your Google Drive sync folder
OUTPUT_CSV = "categorized_videos.csv"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Set this in your environment

# Categories for WR training
CATEGORIES = {
    "drill_types": ["Route Running", "Release Moves", "Hands/Catching", "Footwork", "Speed/Conditioning", "Film Study", "Full Workout", "Other"],
    "difficulty": ["Beginner", "Intermediate", "Advanced", "Pro"],
    "equipment": ["None", "Cones", "Football", "Resistance Bands", "Ladder", "Other"],
    "focus_area": ["Speed", "Agility", "Technique", "Strength", "Explosiveness", "Body Control"]
}

def extract_audio(video_path, audio_path):
    """Extract audio from video using ffmpeg"""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        "-y", audio_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper (local)"""
    try:
        import whisper
        model = whisper.load_model("base")  # Use "small" or "medium" for better accuracy
        result = model.transcribe(audio_path)
        return result["text"]
    except ImportError:
        print("Whisper not installed. Run: pip install openai-whisper")
        return None

def transcribe_with_api(audio_path, client):
    """Transcribe using OpenAI Whisper API (costs ~$0.006/min)"""
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcript.text

def categorize_with_gpt(transcript, filename, client):
    """Use GPT to categorize based on transcript"""
    prompt = f"""Analyze this football/WR training video transcript and categorize it.

Filename: {filename}
Transcript: {transcript}

Respond in JSON format:
{{
    "drill_type": one of {CATEGORIES['drill_types']},
    "difficulty": one of {CATEGORIES['difficulty']},
    "equipment": list from {CATEGORIES['equipment']},
    "focus_area": list from {CATEGORIES['focus_area']},
    "description": "Brief 1-2 sentence description of the drill",
    "coaching_cues": ["key coaching point 1", "key coaching point 2"]
}}

If transcript is empty or unclear, make best guess from filename or mark as "Other"."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Cheap and fast
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def process_videos(use_api_whisper=False):
    """Main processing loop"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    video_folder = Path(VIDEO_FOLDER)
    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".MP4", ".MOV"}
    
    results = []
    videos = [f for f in video_folder.iterdir() if f.suffix in video_extensions]
    
    print(f"Found {len(videos)} videos to process\n")
    
    for i, video_path in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] Processing: {video_path.name}")
        
        # Extract audio
        audio_path = video_path.with_suffix(".wav")
        if not extract_audio(str(video_path), str(audio_path)):
            print(f"  ⚠ Could not extract audio, skipping...")
            continue
        
        # Transcribe
        if use_api_whisper:
            transcript = transcribe_with_api(str(audio_path), client)
        else:
            transcript = transcribe_audio(str(audio_path))
        
        if transcript is None:
            transcript = ""
        
        print(f"  📝 Transcript: {transcript[:100]}..." if transcript else "  📝 No speech detected")
        
        # Categorize
        try:
            category = categorize_with_gpt(transcript, video_path.name, client)
            print(f"  ✓ Categorized as: {category['drill_type']} ({category['difficulty']})")
        except Exception as e:
            print(f"  ⚠ Categorization failed: {e}")
            category = {
                "drill_type": "Other",
                "difficulty": "Unknown",
                "equipment": [],
                "focus_area": [],
                "description": "Could not categorize",
                "coaching_cues": []
            }
        
        results.append({
            "filename": video_path.name,
            "transcript": transcript,
            **category
        })
        
        # Clean up temp audio
        if audio_path.exists():
            audio_path.unlink()
    
    # Write CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["filename", "drill_type", "difficulty", "equipment", "focus_area", "description", "coaching_cues", "transcript"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            r["equipment"] = ", ".join(r.get("equipment", []))
            r["focus_area"] = ", ".join(r.get("focus_area", []))
            r["coaching_cues"] = " | ".join(r.get("coaching_cues", []))
            writer.writerow(r)
    
    print(f"\n✅ Done! Results saved to {OUTPUT_CSV}")
    return results

if __name__ == "__main__":
    # Check requirements
    if not OPENAI_API_KEY:
        print("ERROR: Set OPENAI_API_KEY environment variable")
        print("  Windows: set OPENAI_API_KEY=sk-your-key-here")
        print("  Mac/Linux: export OPENAI_API_KEY=sk-your-key-here")
        exit(1)
    
    # Run with local Whisper (free) or API ($0.006/min)
    process_videos(use_api_whisper=False)
