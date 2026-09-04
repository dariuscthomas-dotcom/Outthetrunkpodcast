import os
import re
import json

# Define directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOVIES_DIR = os.path.join(BASE_DIR, "movies")
TEMPLATE_PATH = os.path.join(BASE_DIR, "movie-template.html")

os.makedirs(MOVIES_DIR, exist_ok=True)

def parse_ratings_and_notes(raw_notes):
    """Extracts Jordan/Darius ratings and structures text blocks cleanly."""
    if not raw_notes:
        return "N/A", "N/A", "<p>No episode notes available.</p>"

    # 1. Extract Ratings via Regex
    j_match = re.search(r"Jordan\s*([\d\.]+)", raw_notes, re.IGNORECASE)
    d_match = re.search(r"Darius\s*([\d\.]+)", raw_notes, re.IGNORECASE)

    jordan_rating = j_match.group(1) if j_match else "N/A"
    darius_rating = d_match.group(1) if d_match else "N/A"

    # 2. Extract Key Sections cleanly using Regex
    summary = re.search(r"Summary:\s*(.*?)(?=\s*(Act /|AFTER:|$))", raw_notes, re.DOTALL)
    best_q = re.search(r"Best Question:\s*(.*?)(?=\s*(Jordan Insight:|$))", raw_notes, re.DOTALL)
    j_insight = re.search(r"Jordan Insight:\s*(.*?)(?=\s*(Darius Insight:|$))", raw_notes, re.DOTALL)
    d_insight = re.search(r"Darius Insight:\s*(.*?)(?=\s*(Major Themes:|$))", raw_notes, re.DOTALL)
    themes = re.search(r"Major Themes:\s*(.*?)(?=\s*($))", raw_notes, re.DOTALL)

    formatted_html = ""
    
    if summary and summary.group(1).strip():
        formatted_html += f'<div class="note-block"><h3>Summary</h3><p>{summary.group(1).strip()}</p></div>'
    if best_q and best_q.group(1).strip():
        formatted_html += f'<div class="note-block"><h3>Best Question</h3><p>{best_q.group(1).strip()}</p></div>'
    if j_insight and j_insight.group(1).strip():
        formatted_html += f'<div class="note-block"><h3>Jordan Insight</h3><p>{j_insight.group(1).strip()}</p></div>'
    if d_insight and d_insight.group(1).strip():
        formatted_html += f'<div class="note-block"><h3>Darius Insight</h3><p>{d_insight.group(1).strip()}</p></div>'
    if themes and themes.group(1).strip():
        formatted_html += f'<div class="note-block"><h3>Major Themes</h3><p>{themes.group(1).strip()}</p></div>'

    # Fallback if structure isn't detected
    if not formatted_html:
        formatted_html = f'<div class="note-block"><p>{raw_notes.strip()}</p></div>'

    return jordan_rating, darius_rating, formatted_html


def generate_pages():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Load your movie data source (e.g., movies.json or python dictionary list)
    data_path = os.path.join(BASE_DIR, "movies.json")
    if not os.path.exists(data_path):
        print("Error: movies.json not found!")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        movies = json.load(f)

    for movie in movies:
        title = movie.get("title", "Untitled")
        year = str(movie.get("year", "")).strip()
        youtube_id = movie.get("youtube_id", "").strip()
        raw_notes = movie.get("notes_text", "")
        letterboxd_url = movie.get("letterboxd_url", "#")

        # 1a Fix: Only show year inside parens if year exists
        display_title = f"{title} ({year})" if year else title

        # 1b Fix: Hide embed block if YouTube ID is missing/blank
        if youtube_id:
            video_html = f'''
            <div class="video-container">
                <iframe src="https://www.youtube.com/embed/{youtube_id}" 
                        frameborder="0" allowfullscreen></iframe>
            </div>
            '''
        else:
            video_html = ""

        # 1c & 2a Fixes: Parse ratings & formatted show notes
        jordan_rating, darius_rating, formatted_notes = parse_ratings_and_notes(raw_notes)

        # Replace placeholders in template
        page_html = template_content
        page_html = page_html.replace("{{DISPLAY_TITLE}}", display_title)
        page_html = page_html.replace("{{JORDAN_RATING}}", jordan_rating)
        page_html = page_html.replace("{{DARIUS_RATING}}", darius_rating)
        page_html = page_html.replace("{{VIDEO_EMBED}}", video_html)
        page_html = page_html.replace("{{SHOW_NOTES}}", formatted_notes)
        page_html = page_html.replace("{{LETTERBOXD_URL}}", letterboxd_url)

        # File slug generator
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        output_file = os.path.join(MOVIES_DIR, f"{slug}.html")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(page_html)

    print(f"Successfully generated {len(movies)} movie pages in /movies/")

if __name__ == "__main__":
    generate_pages()