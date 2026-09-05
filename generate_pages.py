import os
import re
import pandas as pd

# Paths
EXCEL_PATH = "Movie Archive Inputs_3.xlsx" if os.path.exists("Movie Archive Inputs_3.xlsx") else "Movie Archive Inputs.xlsx"
OUTPUT_DIR = "movies"
ARCHIVE_PATH = "movies-archive.html"

# Panthers Process Blue Accent Color
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

def render_stars(rating_val):
    """Converts numeric ratings into visual star graphics."""
    try:
        val = float(rating_val)
        full_stars = int(val)
        half_star = (val - full_stars) >= 0.5
        stars_html = "★" * full_stars
        if half_star:
            stars_html += "½"
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        stars_html += "☆" * empty_stars
        return stars_html
    except (ValueError, TypeError):
        return "☆☆☆☆☆"

def format_rating_badge(val):
    """Formats numeric values into rating badges."""
    if pd.isna(val) or str(val).strip().lower() in ["nan", "n/a", ""]:
        return "N/A"
    try:
        num = float(val)
        return f"{int(num)}/5" if num.is_integer() else f"{num}/5"
    except ValueError:
        return "N/A"

def calculate_avg_rating(jordan_val, darius_val):
    """Calculates average host rating for card metadata."""
    try:
        j = float(jordan_val)
        d = float(darius_val)
        avg = (j + d) / 2
        return f"{int(avg)}/5" if avg.is_integer() else f"{avg:.1f}/5"
    except (ValueError, TypeError):
        return None

def format_transcript(raw_text):
    """Formats transcript text, bolding, underlining, and highlighting Jordan: and Darius:."""
    if not raw_text or str(raw_text).strip().lower() in ["nan", ""]:
        return "<p style='color: #666;'>Transcript coming soon.</p>"
    
    paragraphs = [p.strip() for p in str(raw_text).split("\n") if p.strip()]
    formatted_p = []
    
    for p in paragraphs:
        p_highlighted = re.sub(
            r'^(Jordan|Darius):', 
            f'<u style="color: {ACCENT_COLOR}; font-weight: bold;">\\1:</u>', 
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
col_e_name = df.columns[4]

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
        year_str = ""
        display_title = clean_title

    j_raw = row.get('jordan_rating')
    d_raw = row.get('darius_rating')
    
    jordan_badge = format_rating_badge(j_raw)
    darius_badge = format_rating_badge(d_raw)
    
    jordan_stars = render_stars(j_raw)
    darius_stars = render_stars(d_raw)
    
    avg_rating = calculate_avg_rating(j_raw, d_raw)

    show_notes_html = str(row.get(col_e_name, "")).strip() if pd.notna(row.get(col_e_name)) else ""
    if not show_notes_html or show_notes_html == "nan":
        show_notes_html = "<p>Show notes available in full podcast audio.</p>"

    formatted_transcript = format_transcript(row.get("transcript"))

    # Hero Video Embed Block
    yt_id = get_youtube_id(row.get("youtube_link"))
    if yt_id:
        embed_html = f'''
        <div class="hero-video-container">
            <iframe 
                src="https://www.youtube-nocookie.com/embed/{yt_id}" 
                title="{display_title}" frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                referrerpolicy="strict-origin-when-cross-origin" allowfullscreen>
            </iframe>
        </div>'''
    else:
        embed_html = ""

    # 1. GENERATE INDIVIDUAL MOVIE PAGE (WITH MODERN SANS-SERIF & RATING BADGES)
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_title} - Out The Trunk</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../styles.css">
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #fcfcfc;
            color: #222222;
        }}
        .hero-header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
            border: 1px solid #eaeaea;
        }}
        .hero-video-container {{
            margin-bottom: 2rem;
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            overflow: hidden;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }}
        .hero-video-container iframe {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: 0;
        }}
        .ratings-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}
        .rating-card {{
            background: #ffffff;
            border: 1px solid #eaeaea;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        }}
        .rating-card h3 {{
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 0 0 0.5rem 0;
        }}
        .star-display {{
            color: {ACCENT_COLOR};
            font-size: 1.5rem;
            letter-spacing: 2px;
            margin-bottom: 0.25rem;
        }}
        .rating-num {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #111;
        }}
        .modern-card {{
            background: #ffffff;
            border: 1px solid #eaeaea;
            border-radius: 12px;
            padding: 1.75rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
            line-height: 1.6;
        }}
        .modern-card h2 {{
            font-size: 1.35rem;
            font-weight: 700;
            margin-top: 0;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 0.5rem;
            color: #111;
        }}
        .modern-card h3 {{
            font-size: 1.1rem;
            color: {ACCENT_COLOR};
            margin-top: 1.25rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}
        .modern-card ul {{
            padding-left: 1.2rem;
            margin-bottom: 1rem;
        }}
        .modern-card li {{
            margin-bottom: 0.4rem;
        }}
        .major-themes ul {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            list-style: none;
            padding-left: 0;
        }}
        .major-themes li {{
            background: #f0f8ff;
            color: {ACCENT_COLOR};
            border: 1px solid {ACCENT_COLOR};
            border-radius: 20px;
            padding: 0.25rem 0.85rem;
            font-size: 0.85rem;
            font-weight: 600;
            margin: 0;
        }}
    </style>
</head>
<body>
    <main class="container" style="max-width: 850px; margin: 0 auto; padding: 2rem 1rem;">
        <header class="hero-header">
            <p style="color: {ACCENT_COLOR}; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; font-size: 0.85rem; margin-bottom: 0.25rem;">MOVIE REVIEW & SHOW NOTES</p>
            <h1 style="font-size: 2.2rem; font-weight: 800; margin: 0; color: #111;">{display_title}</h1>
        </header>

        {embed_html}

        <section class="ratings-grid">
            <div class="rating-card">
                <h3>Jordan's Rating</h3>
                <div class="star-display">{jordan_stars}</div>
                <div class="rating-num">{jordan_badge}</div>
            </div>
            <div class="rating-card">
                <h3>Darius's Rating</h3>
                <div class="star-display">{darius_stars}</div>
                <div class="rating-num">{darius_badge}</div>
            </div>
        </section>

        <section class="modern-card">
            {show_notes_html}
        </section>

        <section class="modern-card">
            <h2>Full Episode Transcript</h2>
            <div style="margin-top: 1rem;">
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
        'year_str': year_str,
        'avg_rating': avg_rating,
        'slug': slug,
        'sort_key': sort_key,
        'letter_group': letter_group
    })

movie_list.sort(key=lambda x: x['sort_key'])

# 2. BUILD ALPHABETICAL ARCHIVE PAGE
all_groups = ["#"] + [chr(i) for i in range(ord('A'), ord('Z')+1)]
active_groups = set(m['letter_group'] for m in movie_list)

nav_buttons = []
for g in all_groups:
    if g in active_groups:
        nav_buttons.append(f'<a href="#group-{g}" class="nav-btn active-btn">{g}</a>')
    else:
        nav_buttons.append(f'<span class="nav-btn disabled-btn">{g}</span>')

nav_bar_html = f'''<nav class="az-navigation">
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
            meta_str = f" ({item['year_str']})" if item['year_str'] else ""
            rating_meta = f'<span class="card-meta"> ★ {item["avg_rating"]}</span>' if item['avg_rating'] else ""
            
            cards += f'''
            <a href="movies/{item['slug']}.html" class="movie-card-styled">
                <div class="card-content">
                    <h3>{item['clean_title']}</h3>
                    {rating_meta}
                </div>
            </a>'''
            
        sections_html += f'''
        <section id="group-{g}" style="margin-bottom: 3rem; scroll-margin-top: 2rem;">
            <h2 class="group-header">{g}</h2>
            <div class="movie-grid">
                {cards}
            </div>
        </section>'''

# 3. WRITE MOVIES-ARCHIVE.HTML PAGE WITH MODERN UI STYLING
archive_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Movie Archive - Out The Trunk</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <style>
        html {{ scroll-behavior: smooth; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #fcfcfc;
            color: #222;
        }}
        
        .az-navigation {{
            text-align: center;
            margin-bottom: 2.5rem;
            line-height: 2.2;
            background: #ffffff;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            border: 1px solid #eaeaea;
        }}
        
        .nav-btn {{
            display: inline-block;
            padding: 6px 12px;
            margin: 3px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.9rem;
            transition: all 0.2s ease-in-out;
        }}
        
        .active-btn {{
            background-color: {ACCENT_COLOR};
            color: #fff !important;
            border: 1px solid {ACCENT_COLOR};
            text-decoration: none;
            box-shadow: 0 2px 6px rgba(0, 133, 202, 0.25);
        }}
        
        .active-btn:hover {{
            background-color: #006dae;
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0, 133, 202, 0.35);
        }}
        
        .disabled-btn {{
            border: 1px solid #eaeaea;
            color: #d1d1d1;
            background-color: #fafafa;
        }}
        
        .group-header {{
            font-size: 1.8rem;
            font-weight: 800;
            border-bottom: 2px solid {ACCENT_COLOR};
            padding-bottom: 0.4rem;
            margin-bottom: 1.5rem;
            color: #111;
        }}
        
        .movie-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 1.25rem;
        }}
        
        .movie-card-styled {{
            text-decoration: none;
            color: #111;
            background: #ffffff;
            border: 1px solid #eaeaea;
            border-left: 4px solid {ACCENT_COLOR};
            border-radius: 10px;
            padding: 1.25rem 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            box-shadow: 0 3px 8px rgba(0,0,0,0.03);
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        
        .movie-card-styled:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(0, 133, 202, 0.15);
            border-color: {ACCENT_COLOR};
            background-color: #f8fcff;
        }}
        
        .movie-card-styled h3 {{
            margin: 0;
            font-size: 1.05rem;
            font-weight: 600;
            line-height: 1.3;
        }}
        
        .card-meta {{
            display: block;
            margin-top: 0.35rem;
            font-size: 0.8rem;
            font-weight: 700;
            color: {ACCENT_COLOR};
        }}
    </style>
</head>
<body>
    <main class="container" style="max-width: 1000px; margin: 0 auto; padding: 2rem 1rem;">
        <header style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; color: #111;">Movie Archive</h1>
            <p style="color: #666; font-size: 1.05rem;">Browse all movie reviews and show notes</p>
        </header>

        {nav_bar_html}

        {sections_html}
    </main>
</body>
</html>
"""

with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
    f.write(archive_html)

print("Modern website code update complete!")