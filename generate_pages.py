import os
import re
import pandas as pd

# Paths
EXCEL_PATH = "Movie Archive Inputs.xlsx"
OUTPUT_DIR = "movies"
ARCHIVE_PATH = "movies-archive.html"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def normalize_title(title):
    """Converts 'Best Man, The' to 'The Best Man'."""
    title = str(title).strip()
    match = re.match(r"^(.*?),\s*(The|A|An)$", title, re.IGNORECASE)
    if match:
        return f"{match.group(2)} {match.group(1)}"
    return title

def get_youtube_id(url):
    """Extracts YouTube ID from link."""
    if not isinstance(url, str):
        return None
    url = url.strip()
    if not url or ("youtube.com" not in url and "youtu.be" not in url):
        return None
    match = re.search(r"(?:v=|\/embed\/|\/1\/|\/v\/|https:\/\/youtu\.be\/|\/e\/|watch\?v=|^)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def clean_slug(title):
    """Generates URL slug like 'the-best-man'."""
    normalized = normalize_title(title)
    filename = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
    return re.sub(r"[-\s]+", "-", filename)

def format_rating(val):
    """Formats ratings cleanly without trailing decimals."""
    if pd.isna(val) or str(val).strip().lower() in ["nan", "n/a", ""]:
        return "N/A"
    try:
        num = float(val)
        return f"{int(num)} / 5" if num.is_integer() else f"{num} / 5"
    except ValueError:
        return "N/A"

# Read master data
df = pd.read_excel(EXCEL_PATH)

archive_cards = []

for idx, row in df.iterrows():
    raw_title = str(row.get("movie_title", "")).strip()
    if not raw_title or raw_title == "nan":
        continue

    clean_title = normalize_title(raw_title)
    slug = clean_slug(raw_title)

    year_val = row.get("movie_year")
    if pd.notna(year_val) and str(year_val).strip() not in ["nan", ""]:
        year_str = str(int(float(year_val)))
        display_title = f"{clean_title} ({year_str})"
    else:
        display_title = clean_title

    jordan_rating = format_rating(row.get('jordan_rating'))
    darius_rating = format_rating(row.get('darius_rating'))

    best_question = str(row.get("best_question", "")).strip() if pd.notna(row.get("best_question")) else ""
    major_themes = str(row.get("major_themes", "")).strip() if pd.notna(row.get("major_themes")) else ""

    # YouTube embed handling
    yt_id = get_youtube_id(row.get("youtube_link"))
    if yt_id:
        embed_html = f'''
        <div class="video-container" style="margin-bottom: 2rem; position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 8px;">
            <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;"
                src="https://www.youtube-nocookie.com/embed/{yt_id}" 
                title="{display_title}" frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                referrerpolicy="strict-origin-when-cross-origin" allowfullscreen>
            </iframe>
        </div>'''
    else:
        embed_html = ""

    # Build Show Notes block
    show_notes_content = ""
    if best_question and best_question != "nan":
        show_notes_content += f"<p><strong>Best Question:</strong> {best_question}</p>\n"
    if major_themes and major_themes != "nan":
        show_notes_content += f"<p><strong>Major Themes:</strong> {major_themes}</p>\n"
    if not show_notes_content:
        show_notes_content = "<p>Show notes available in full podcast audio.</p>"

    # 1. WRITE INDIVIDUAL MOVIE HTML PAGE
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_title} - Out The Trunk</title>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <main class="container" style="max-width: 800px; margin: 0 auto; padding: 2rem 1rem;">
        <header style="text-align: center; margin-bottom: 2rem;">
            <p style="color: #00c853; font-weight: bold; letter-spacing: 1px; text-transform: uppercase;">MOVIE REVIEW & SHOW NOTES</p>
            <h1 style="font-size: 2.2rem; margin-top: 0.5rem;">{display_title}</h1>
        </header>

        {embed_html}

        <section class="ratings-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem;">
            <div class="card" style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 1.5rem; text-align: center;">
                <h3 style="font-size: 0.9rem; color: #555; text-transform: uppercase; margin-bottom: 0.5rem;">JORDAN'S RATING</h3>
                <p style="font-size: 1.8rem; font-weight: bold; margin: 0;">{jordan_rating}</p>
            </div>
            <div class="card" style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 1.5rem; text-align: center;">
                <h3 style="font-size: 0.9rem; color: #555; text-transform: uppercase; margin-bottom: 0.5rem;">DARIUS'S RATING</h3>
                <p style="font-size: 1.8rem; font-weight: bold; margin: 0;">{darius_rating}</p>
            </div>
        </section>

        <section class="card" style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem;">
            <h2 style="font-size: 1.4rem; margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 0.5rem;">Show Notes & Highlights</h2>
            <div style="margin-top: 1rem; line-height: 1.6;">
                {show_notes_content}
            </div>
        </section>

        <section class="card" style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 1.5rem;">
            <h2 style="font-size: 1.4rem; margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 0.5rem;">Full Episode Transcript</h2>
            <p style="color: #666; margin-top: 1rem; line-height: 1.6;"></p>
        </section>
    </main>
</body>
</html>
"""

    file_path = os.path.join(OUTPUT_DIR, f"{slug}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 2. SAVE CARD DATA FOR ARCHIVE PAGE
    archive_cards.append(f'''
        <a href="movies/{slug}.html" class="movie-card" style="text-decoration: none; color: inherit; border: 1px solid #e0e0e0; border-radius: 8px; padding: 1.2rem; display: block; background: #fff;">
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.2rem; color: #111;">{display_title}</h3>
            <p style="margin: 0; color: #00c853; font-weight: bold; font-size: 0.9rem;">View Review & Show Notes &rarr;</p>
        </a>''')

# 3. WRITE THE COMPLETE MOVIES-ARCHIVE.HTML PAGE
archive_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Movie Archive - Out The Trunk</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <main class="container" style="max-width: 1000px; margin: 0 auto; padding: 2rem 1rem;">
        <header style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">Movie Archive</h1>
            <p style="color: #666;">Browse all movie reviews and show notes</p>
        </header>

        <div class="movie-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem;">
            {"".join(archive_cards)}
        </div>
    </main>
</body>
</html>
"""

with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
    f.write(archive_html)

print("ALL movie pages and movies-archive.html generated successfully in one shot!")