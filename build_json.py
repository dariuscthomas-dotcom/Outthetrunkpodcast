import os
import re
import json

MOVIES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies")
OUTPUT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.json")

movies = []

if os.path.exists(MOVIES_DIR):
    for filename in os.listdir(MOVIES_DIR):
        if filename.endswith(".html"):
            file_path = os.path.join(MOVIES_DIR, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract Title & Year
            title_match = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.IGNORECASE)
            raw_title = title_match.group(1).strip() if title_match else filename.replace(".html", "")
            
            year_match = re.search(r"\((\d{4})\)", raw_title)
            year = year_match.group(1) if year_match else ""
            title = re.sub(r"\s*\(\d{4}\)", "", raw_title).strip()

            # Extract YouTube ID if present
            yt_match = re.search(r'youtube\.com/embed/([a-zA-Z0-9_-]+)', content)
            youtube_id = yt_match.group(1) if yt_match else ""

            # Extract Show Notes text
            notes_match = re.search(r'Show Notes & Highlights</h2>\s*(.*?)\s*<a', content, re.DOTALL)
            raw_notes = notes_match.group(1).strip() if notes_match else ""

            # Extract Letterboxd Link
            lb_match = re.search(r'href="([^"]*letterboxd[^"]*)"', content)
            letterboxd_url = lb_match.group(1) if lb_match else "#"

            movies.append({
                "title": title,
                "year": year,
                "youtube_id": youtube_id,
                "notes_text": raw_notes,
                "letterboxd_url": letterboxd_url
            })

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(movies, f, indent=4)

print(f"Rebuilt movies.json with {len(movies)} entries!")