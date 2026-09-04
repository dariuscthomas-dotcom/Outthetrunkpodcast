import os
import re
import pandas as pd

# Paths
EXCEL_PATH = "Movie Archive Inputs.xlsx"
OUTPUT_DIR = "movies"
ARCHIVE_PATH = "movies-archive.html"

# Panthers Color Theme Accent
ACCENT_COLOR = "#0085CA"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def normalize_title(title):
    """Converts 'Best Man, The' to 'The Best Man'."""
    title = str(title).strip()
    match = re.match(r"^(.*?),\s*(The|A|An)$", title, re.IGNORECASE)
    if match:
        return f"{match.group(2)} {match.group(1)}"
    return title

def get_sort_key(title):
    """Strips leading 'The ', 'A ', 'An ' for clean alphabetical sorting."""
    normalized = normalize_title(title).upper()
    for prefix in ["THE ", "A ", "AN "]:
        if normalized.startswith(prefix):
            return normalized[len(prefix):]
    return normalized

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

def format_transcript(raw_text):
    """Formats transcript text, bolding and highlighting Jordan: and Darius:."""
    if not raw_text or str(raw_text).strip().lower() in ["nan", ""]:
        return "<p style='color: #666;'>Transcript coming soon.</p>"
    
    paragraphs = [p.strip() for p in str(raw_text).split("\n") if p.strip()]
    formatted_p = []
    
    for p in paragraphs:
        # Bold and highlight "Jordan:" and "Darius:" at start of line
        p_highlighted = re.sub(
            r'^(Jordan|Darius):', 
            f'<strong style="color: {ACCENT_COLOR}; font-weight: bold;">\\1:</strong>', 
            p
        )
        formatted_p.append(f"<p style='margin-bottom: 1rem; line-height: 1.6;'>{p_highlighted}</p>")
        
    return "".join(formatted_p)

# Load Master Data & Transcripts Sheet
xls = pd.ExcelFile(EXCEL_PATH)

sheet_ratings = "Movie Ratings" if "Movie Ratings" in xls.sheet_names else xls.sheet_names[0]
df_main = pd.read_excel(xls, sheet_name=sheet_ratings)

if "Transcripts" in xls.sheet_names or "transcripts" in xls.sheet_names:
    trans_sheet = "Transcripts" if "Transcripts" in xls.sheet_names else "transcripts"
    df_transcripts = pd.read_excel(xls, sheet_name=trans_sheet)
    df_transcripts.columns = [str(c).strip().lower() for c in df_transcripts.columns]
    if "movie_title" in df_transcripts.columns and "transcript" in df_transcripts.columns:
        df = pd.merge(df_main, df_transcripts[['movie_title', 'transcript']], on="movie_title", how="left")
    else:
        df = df_main
        df['transcript'] = ""
else:
    df = df_main
    df['transcript'] = ""

movie_list = []

for idx, row in df.iterrows():
    raw_title = str(row.get("movie_title", "")).strip()
    if not raw_title or raw_title == "nan":
        continue

    clean_title = normalize_title(raw_title)
    slug = clean_slug(raw_title)
    sort_key = get_sort_key(raw_title)
    
    first_char = sort_key[0] if sort_key else "A"
    letter_group = first_char if first_char.isalpha() else "#"

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

    formatted_transcript = format_transcript(row.get("transcript"))

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

    # Show Notes block
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
            <p style="color: {ACCENT_COLOR}; font-weight: bold; letter-spacing: 1px; text-transform: uppercase;">MOVIE REVIEW & SHOW NOTES</p>
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
            <div style="margin-top: 1rem; line-height: 1.6;">
                {formatted_transcript}
            </div>
        </section>
    </main>
</body>
</html>
"""

    file_path = os.path.join(OUTPUT_DIR, f"{slug}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    movie_list.append({
        'clean_title': clean_title,
        'slug': slug,
        'sort_key': sort_key,
        'letter_group': letter_group
    })

# Sort movie list alphabetically
movie_list.sort(key=lambda x: x['sort_key'])

# 2. BUILD ALPHABETICAL ARCHIVE PAGE
all_groups = ["#"] + [chr(i) for i in range(ord('A'), ord('Z')+1)]
active_groups = set(m['letter_group'] for m in movie_list)

nav_buttons = []
for g in all_groups:
    if g in active_groups:
        nav_buttons.append(f'<a href="#group-{g}" style="display: inline-block; padding: 6px 12px; margin: 3px; border: 1px solid {ACCENT_COLOR}; border-radius: 4px; color: {ACCENT_COLOR}; text-decoration: none; font-weight: bold;">{g}</a>')
    else:
        nav_buttons.append(f'<span style="display: inline-block; padding: 6px 12px; margin: 3px; border: 1px solid #eee; border-radius: 4px; color: #ccc;">{g}</span>')

nav_bar_html = f'''<nav class="az-navigation" style="text-align: center; margin-bottom: 2.5rem; line-height: 2;">
    {"".join(nav_buttons)}
</nav>'''

sections_html = ""
grouped_movies = {}
for m in movie_list:
    g = m['letter_group']
    grouped_movies.setdefault(g, []).append(m)

for g in all_groups:
    if g in grouped_movies:
        cards = ""
        for item in grouped_movies[g]:
            cards += f'''
            <a href="movies/{item['slug']}.html" class="movie-card" style="text-decoration: none; color: inherit; border: 1px solid #e0e0e0; border-radius: 8px; padding: 1.2rem; display: block; background: #fff; text-align: center;">
                <h3 style="margin: 0; font-size: 1.2rem; color: #111;">{item['clean_title']}</h3>
            </a>'''
            
        sections_html += f'''
        <section id="group-{g}" style="margin-bottom: 3rem; scroll-margin-top: 2rem;">
            <h2 style="font-size: 2rem; border-bottom: 2px solid {ACCENT_COLOR}; padding-bottom: 0.4rem; margin-bottom: 1.5rem; color: #111;">{g}</h2>
            <div class="movie-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1.2rem;">
                {cards}
            </div>
        </section>'''

# 3. WRITE MOVIES-ARCHIVE.HTML PAGE
archive_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Movie Archive - Out The Trunk</title>
    <link rel="stylesheet" href="styles.css">
    <style>
        html {{ scroll-behavior: smooth; }}
    </style>
</head>
<body>
    <main class="container" style="max-width: 1000px; margin: 0 auto; padding: 2rem 1rem;">
        <header style="text-align: center; margin-bottom: 1.5rem;">
            <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">Movie Archive</h1>
            <p style="color: #666;">Browse all movie reviews and show notes</p>
        </header>

        {nav_bar_html}

        {sections_html}
    </main>
</body>
</html>
"""

with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
    f.write(archive_html)

print("Updated build complete! Applied Panthers color theme, title-only cards, and transcript highlighting.")