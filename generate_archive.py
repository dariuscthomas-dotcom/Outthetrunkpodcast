import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOVIES_DIR = os.path.join(BASE_DIR, "movies")
TEMPLATE_PATH = os.path.join(BASE_DIR, "movie-template.html")

os.makedirs(MOVIES_DIR, exist_ok=True)

# Master Data List
MOVIES_DATA = [
    {
        "title": "Arrival",
        "year": "2016",
        "youtube_id": "",  # Empty hides the video player cleanly
        "jordan_rating": "5.0",
        "darius_rating": "4.0",
        "best_question": "If you could press a button and see the rest of your life, would you want to know?",
        "jordan_insight": "Choose love over fear; the ending is about accepting joy even knowing grief is coming.",
        "darius_insight": "The filler episodes of life are what make life feel alive.",
        "major_themes": "Fate; language; love; grief; randomness; choice",
        "letterboxd_url": "https://letterboxd.com/film/arrival-2016/"
    }
    # Future movies go here as simple dictionaries
]

def generate_pages():
    if not os.path.exists(TEMPLATE_PATH):
        print("Error: movie-template.html not found!")
        return

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template_content = f.read()

    for movie in MOVIES_DATA:
        title = movie["title"]
        year = movie.get("year", "").strip()
        display_title = f"{title} ({year})" if year else title
        
        youtube_id = movie.get("youtube_id", "").strip()
        video_html = f'''<div class="video-container"><iframe src="https://www.youtube.com/embed/{youtube_id}" frameborder="0" allowfullscreen></iframe></div>''' if youtube_id else ""

        # Build clean show notes HTML block
        notes_html = ""
        if movie.get("best_question"):
            notes_html += f'<div class="note-block"><h3>Best Question</h3><p>{movie["best_question"]}</p></div>'
        if movie.get("jordan_insight"):
            notes_html += f'<div class="note-block"><h3>Jordan Insight</h3><p>{movie["jordan_insight"]}</p></div>'
        if movie.get("darius_insight"):
            notes_html += f'<div class="note-block"><h3>Darius Insight</h3><p>{movie["darius_insight"]}</p></div>'
        if movie.get("major_themes"):
            notes_html += f'<div class="note-block"><h3>Major Themes</h3><p>{movie["major_themes"]}</p></div>'

        # Replace placeholders matching movie-template.html
        page_html = template_content
        page_html = page_html.replace("{{DISPLAY_TITLE}}", display_title)
        page_html = page_html.replace("{{JORDAN_RATING}}", movie.get("jordan_rating", "N/A"))
        page_html = page_html.replace("{{DARIUS_RATING}}", movie.get("darius_rating", "N/A"))
        page_html = page_html.replace("{{VIDEO_EMBED}}", video_html)
        page_html = page_html.replace("{{SHOW_NOTES}}", notes_html)
        page_html = page_html.replace("{{LETTERBOXD_URL}}", movie.get("letterboxd_url", "#"))

        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        output_file = os.path.join(MOVIES_DIR, f"{slug}.html")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(page_html)

    print(f"Successfully generated {len(MOVIES_DATA)} movie pages.")

if __name__ == "__main__":
    generate_pages()