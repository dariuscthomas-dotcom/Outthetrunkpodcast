import os
import re
from docx import Document

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOVIES_DIR = os.path.join(BASE_DIR, "movies")

# Raw Source Folders
SHOW_NOTES_DIR = r"E:\Creative\Podcasts\Show Notes"
TRANSCRIPTS_DIR = r"E:\Creative\Podcasts\Transcripts\Movie_Reviews"

os.makedirs(MOVIES_DIR, exist_ok=True)

def read_docx(file_path):
    """Extracts all text lines from a .docx file."""
    if not os.path.exists(file_path):
        return ""
    try:
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def find_matching_file(folder_path, movie_name):
    """Finds a .docx file in folder_path matching the movie name."""
    if not os.path.exists(folder_path):
        return None
    
    clean_target = re.sub(r'[^a-zA-Z0-9]', '', movie_name.lower())
    for f in os.listdir(folder_path):
        if f.endswith(".docx") and not f.startswith("~$"):
            clean_file = re.sub(r'[^a-zA-Z0-9]', '', f.lower())
            if clean_target in clean_file:
                return os.path.join(folder_path, f)
    return None

def build_all_movies():
    if not os.path.exists(SHOW_NOTES_DIR):
        print(f"Error: Could not find Show Notes folder at: {SHOW_NOTES_DIR}")
        return

    # Find all .docx files in Show Notes folder
    show_note_files = [f for f in os.listdir(SHOW_NOTES_DIR) if f.endswith(".docx") and not f.startswith("~$")]
    print(f"Found {len(show_note_files)} show notes files. Processing...")

    for file_name in show_note_files:
        notes_path = os.path.join(SHOW_NOTES_DIR, file_name)
        raw_notes = read_docx(notes_path)

        # Determine Movie Name from Filename
        movie_title = os.path.splitext(file_name)[0].replace("_", " ").replace("-", " ").title()

        # Extract Release Year if present in text or title
        year_match = re.search(r"\((\d{4})\)", raw_notes) or re.search(r"\b(19\d\d|20\d\d)\b", movie_title)
        year = year_match.group(1) if year_match else ""
        
        # Clean title for display
        clean_title = re.sub(r"\s*\(\d{4}\)", "", movie_title).strip()
        display_title = f"{clean_title} ({year})" if year else clean_title

        # Extract Ratings
        j_match = re.search(r"Jordan['’]?s?\s*Rating:?\s*([\d\.]+)", raw_notes, re.IGNORECASE)
        d_match = re.search(r"Darius['’]?s?\s*Rating:?\s*([\d\.]+)", raw_notes, re.IGNORECASE)
        
        jordan_rating = j_match.group(1) if j_match else "N/A"
        darius_rating = d_match.group(1) if d_match else "N/A"

        # Extract Show Notes Sections
        best_q = re.search(r"Best Question:?\s*(.*?)(?=\s*(Jordan Insight|Darius Insight|$))", raw_notes, re.IGNORECASE | re.DOTALL)
        j_insight = re.search(r"Jordan Insight:?\s*(.*?)(?=\s*(Darius Insight|Major Themes|$))", raw_notes, re.IGNORECASE | re.DOTALL)
        d_insight = re.search(r"Darius Insight:?\s*(.*?)(?=\s*(Major Themes|Out The Trunk Verdict|$))", raw_notes, re.IGNORECASE | re.DOTALL)
        themes = re.search(r"Major Themes:?\s*(.*?)(?=\s*(Out The Trunk Verdict|$))", raw_notes, re.IGNORECASE | re.DOTALL)

        best_q_str = best_q.group(1).strip() if best_q else ""
        j_insight_str = j_insight.group(1).strip() if j_insight else ""
        d_insight_str = d_insight.group(1).strip() if d_insight else ""
        themes_str = themes.group(1).strip() if themes else ""

        notes_html = ""
        if best_q_str:
            notes_html += f'<div style="margin-bottom: 15px;"><strong>Best Question:</strong> <p style="margin: 5px 0 0 0; color: #4a5568;">{best_q_str}</p></div>'
        if j_insight_str:
            notes_html += f'<div style="margin-bottom: 15px;"><strong>Jordan Insight:</strong> <p style="margin: 5px 0 0 0; color: #4a5568;">{j_insight_str}</p></div>'
        if d_insight_str:
            notes_html += f'<div style="margin-bottom: 15px;"><strong>Darius Insight:</strong> <p style="margin: 5px 0 0 0; color: #4a5568;">{d_insight_str}</p></div>'
        if themes_str:
            notes_html += f'<div style="margin-bottom: 15px;"><strong>Major Themes:</strong> <p style="margin: 5px 0 0 0; color: #4a5568;">{themes_str}</p></div>'

        if not notes_html:
            notes_html = f'<p style="color: #4a5568;">{raw_notes}</p>'

        # Extract Transcript from matching docx file in Transcripts folder
        transcript_file = find_matching_file(TRANSCRIPTS_DIR, clean_title)
        transcript_text = read_docx(transcript_file) if transcript_file else "Transcript coming soon."

        # Format transcript paragraphs
        if transcript_text != "Transcript coming soon.":
            formatted_transcript = "".join([f"<p>{p.strip()}</p>" for p in transcript_text.split("\n") if p.strip()])
        else:
            formatted_transcript = "<p>Transcript coming soon.</p>"

        # Build Clean HTML Output
        slug = re.sub(r'[^a-z0-9]+', '-', clean_title.lower()).strip('-')
        output_path = os.path.join(MOVIES_DIR, f"{slug}.html")

        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_title} - Out The Trunk Podcast</title>
    <link rel="stylesheet" href="../styles.css">
    <style>
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; font-family: sans-serif; }}
        .movie-title {{ text-align: center; font-size: 2.5rem; color: #1a0b2e; margin-bottom: 25px; }}
        .ratings-grid {{ display: flex; gap: 20px; justify-content: center; margin-bottom: 30px; }}
        .rating-card {{ flex: 1; max-width: 250px; border: 1px solid #e2e8f0; border-radius: 8px; text-align: center; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .rating-card h3 {{ margin: 0 0 10px 0; font-size: 0.85rem; color: #4a5568; letter-spacing: 0.05em; }}
        .rating-card p {{ margin: 0; font-size: 1.8rem; font-weight: bold; color: #1a0b2e; }}
        .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 25px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .card h2 {{ margin-top: 0; color: #1a0b2e; border-bottom: 2px solid #edf2f7; padding-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <p style="text-align: center; font-weight: bold; color: #00b074; margin-bottom: 5px; text-transform: uppercase;">Movie Review & Show Notes</p>
        <h1 class="movie-title">{display_title}</h1>

        <div class="ratings-grid">
            <div class="rating-card">
                <h3>JORDAN'S RATING</h3>
                <p>{jordan_rating} / 5</p>
            </div>
            <div class="rating-card">
                <h3>DARIUS'S RATING</h3>
                <p>{darius_rating} / 5</p>
            </div>
        </div>

        <div class="card">
            <h2>Show Notes & Highlights</h2>
            {notes_html}
        </div>

        <div class="card">
            <h2>Full Episode Transcript</h2>
            <div style="line-height: 1.6; color: #4a5568;">
                {formatted_transcript}
            </div>
        </div>
    </div>
</body>
</html>'''

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    print(f"Finished! Generated {len(show_note_files)} clean movie pages in /movies/")

if __name__ == "__main__":
    build_all_movies()