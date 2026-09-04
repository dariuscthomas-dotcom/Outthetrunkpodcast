import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOVIES_DIR = os.path.join(BASE_DIR, "movies")

def clean_and_rebuild_all_movies():
    if not os.path.exists(MOVIES_DIR):
        print("Error: /movies/ directory not found!")
        return

    html_files = [f for f in os.listdir(MOVIES_DIR) if f.endswith(".html")]
    print(f"Processing {len(html_files)} movie pages...")

    for filename in html_files:
        file_path = os.path.join(MOVIES_DIR, filename)
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Extract Title & Year
        title_match = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.IGNORECASE | re.DOTALL)
        if title_match:
            raw_title = title_match.group(1).strip()
            # Strip out raw {{MOVIE_TITLE}} tags if present
            raw_title = raw_title.replace("{{MOVIE_TITLE}}", "").replace("{{MOVIE_YEAR}}", "").strip()
            if not raw_title:
                raw_title = filename.replace(".html", "").replace("-", " ").title()
        else:
            raw_title = filename.replace(".html", "").replace("-", " ").title()

        # Extract Year if formatted like "Arrival (2016)"
        year_match = re.search(r"\((\d{4})\)", raw_title)
        year = year_match.group(1) if year_match else ""
        clean_title = re.sub(r"\s*\(\d{4}\)", "", raw_title).strip()
        display_title = f"{clean_title} ({year})" if year else clean_title

        # 2. Extract Ratings
        j_match = re.search(r"Jordan's Rating.*?([\d\.]+)", content, re.IGNORECASE | re.DOTALL)
        d_match = re.search(r"Darius's Rating.*?([\d\.]+)", content, re.IGNORECASE | re.DOTALL)
        
        jordan_rating = j_match.group(1) if j_match else "N/A"
        darius_rating = d_match.group(1) if d_match else "N/A"

        # 3. Extract YouTube ID
        yt_match = re.search(r'youtube\.com/embed/([a-zA-Z0-9_-]+)', content)
        youtube_id = yt_match.group(1) if yt_match else ""
        
        video_html = f'''
        <div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; margin-bottom: 30px; border-radius: 8px;">
            <iframe src="https://www.youtube.com/embed/{youtube_id}" style="position: absolute; top:0; left:0; width:100%; height:100%;" frameborder="0" allowfullscreen></iframe>
        </div>
        ''' if youtube_id and "V07yaP" not in youtube_id else ""

        # 4. Parse Show Notes Sections (Best Question, Jordan Insight, Darius Insight, Major Themes)
        best_q = re.search(r"Best Question:\s*(.*?)(?=\s*(Jordan Insight:|Darius Insight:|$))", content, re.IGNORECASE | re.DOTALL)
        j_insight = re.search(r"Jordan Insight:\s*(.*?)(?=\s*(Darius Insight:|Major Themes:|$))", content, re.IGNORECASE | re.DOTALL)
        d_insight = re.search(r"Darius Insight:\s*(.*?)(?=\s*(Major Themes:|Out The Trunk Verdict:|$))", content, re.IGNORECASE | re.DOTALL)
        themes = re.search(r"Major Themes:\s*(.*?)(?=\s*(Out The Trunk Verdict:|Full Episode Transcript:|$))", content, re.IGNORECASE | re.DOTALL)

        # Clean raw extraction strings
        best_q_str = best_q.group(1).strip() if best_q and "{{" not in best_q.group(1) else ""
        j_insight_str = j_insight.group(1).strip() if j_insight and "{{" not in j_insight.group(1) else ""
        d_insight_str = d_insight.group(1).strip() if d_insight and "{{" not in d_insight.group(1) else ""
        themes_str = themes.group(1).strip() if themes and "{{" not in themes.group(1) else ""

        # Build clean Show Notes HTML (Verdict intentionally excluded)
        notes_html = ""
        if best_q_str:
            notes_html += f'<div style="margin-bottom: 15px;"><strong>Best Question:</strong> <p style="margin: 5px 0 0 0;">{best_q_str}</p></div>'
        if j_insight_str:
            notes_html += f'<div style="margin-bottom: 15px;"><strong>Jordan Insight:</strong> <p style="margin: 5px 0 0 0;">{j_insight_str}</p></div>'
        if d_insight_str:
            notes_html += f'<div style="margin-bottom: 15px;"><strong>Darius Insight:</strong> <p style="margin: 5px 0 0 0;">{d_insight_str}</p></div>'
        if themes_str:
            notes_html += f'<div style="margin-bottom: 15px;"><strong>Major Themes:</strong> <p style="margin: 5px 0 0 0;">{themes_str}</p></div>'

        if not notes_html:
            notes_html = "<p>Show notes available in full podcast audio.</p>"

        # 5. Extract Full Transcript Text
        transcript_match = re.search(r"Full Episode Transcript</h3>\s*<div[^>]*>(.*?)</div>", content, re.IGNORECASE | re.DOTALL)
        transcript_text = transcript_match.group(1).strip() if transcript_match and "{{" not in transcript_match.group(1) else "Transcript coming soon."

        # Extract Letterboxd URL
        lb_match = re.search(r'href="([^"]*letterboxd[^"]*)"', content)
        letterboxd_url = lb_match.group(1) if lb_match else "#"

        # Construct Updated Page HTML
        updated_html = f'''<!DOCTYPE html>
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
        .letterboxd-link {{ display: inline-block; font-weight: bold; color: #00b074; text-decoration: none; margin-top: 15px; }}
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

        {video_html}

        <div class="card">
            <h2>Show Notes & Highlights</h2>
            {notes_html}
            <a href="{letterboxd_url}" target="_blank" class="letterboxd-link">View on Letterboxd →</a>
        </div>

        <div class="card">
            <h2>Full Episode Transcript</h2>
            <div style="line-height: 1.6; color: #4a5568;">{transcript_text}</div>
        </div>
    </div>
</body>
</html>'''

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_html)

    print(f"Successfully automated and updated all {len(html_files)} movie pages!")

if __name__ == "__main__":
    clean_and_rebuild_all_movies()