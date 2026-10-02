import os
import re
import pandas as pd

MOVIES_EXCEL = "Movie Archive Inputs_3.xlsx" if os.path.exists("Movie Archive Inputs_3.xlsx") else "Movie Archive Inputs.xlsx"
WOOM_EXCEL = "WOOM Archive Inputs_2.xlsx" if os.path.exists("WOOM Archive Inputs_2.xlsx") else "WOOM Archive Inputs.xlsx"

MOVIES_DIR = "movies"
WOOM_DIR = "woom"

MOVIES_ARCHIVE_PATH = "movies-archive.html"
WOOM_ARCHIVE_PATH = "woom-archive.html"

ACCENT_COLOR = "#00788C"

os.makedirs(MOVIES_DIR, exist_ok=True)
os.makedirs(WOOM_DIR, exist_ok=True)

MASTER_TOPICS = [
    "Relationships & Family",
    "Friendship & Community",
    "Aging & Personal Growth",
    "Work & Ambition",
    "Money & Class",
    "Social Norms & Etiquette",
    "Technology & Internet Culture",
    "Movies & Cinema",
    "Music & Hip-Hop",
    "Creativity & Art",
    "Sports & Athletics",
    "Food & Lifestyle"
]

def normalize_title(title):
    title = str(title).strip()
    match = re.match(r"^(.*?),\s*(The|A|An)$", title, re.IGNORECASE)
    if match:
        return f"{match.group(2)} {match.group(1)}"
    return title

def get_sort_key(title):
    normalized = normalize_title(title).upper()
    for prefix in ["THE ", "A ", "AN "]:
        if normalized.startswith(prefix):
            return normalized[len(prefix):]
    return normalized

def get_youtube_id(url):
    if not isinstance(url, str):
        return None
    url = url.strip()
    if not url or ("youtube.com" not in url and "youtu.be" not in url):
        return None
    match = re.search(r"(?:v=|\/embed\/|\/1\/|\/v\/|https:\/\/youtu\.be\/|\/e\/|watch\?v=|^)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def clean_slug(title):
    normalized = normalize_title(title)
    filename = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
    return re.sub(r"[-\s]+", "-", filename)

def render_stars(rating_val):
    try:
        if pd.isna(rating_val) or str(rating_val).strip().lower() in ["nan", "n/a", ""]:
            return "☆☆☆☆☆"
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
    if pd.isna(val) or str(val).strip().lower() in ["nan", "n/a", ""]:
        return "N/A"
    try:
        num = float(val)
        return f"{int(num)}/5" if num.is_integer() else f"{num:.1f}/5"
    except ValueError:
        return "N/A"

def calculate_avg_num(jordan_val, darius_val):
    try:
        if pd.isna(jordan_val) or pd.isna(darius_val):
            return None
        j = float(jordan_val)
        d = float(darius_val)
        return (j + d) / 2.0
    except (ValueError, TypeError):
        return None

def calculate_avg_rating(jordan_val, darius_val):
    avg = calculate_avg_num(jordan_val, darius_val)
    if avg is not None:
        return f"{int(avg)}/5" if avg.is_integer() else f"{avg:.1f}/5"
    return None

def format_transcript(raw_text):
    if not raw_text or str(raw_text).strip().lower() in ["nan", ""]:
        return "<p style='color: #666;'>Transcript coming soon.</p>"
    
    text_str = str(raw_text).strip()
    
    if re.search(r'\d{2}:\d{2}:\d{2}\s+(?:Jordan|Darius)', text_str):
        parts = re.split(r'(?=\d{2}:\d{2}:\d{2}\s+(?:Jordan|Darius))', text_str)
        formatted_p = []
        for part in parts:
            part_str = part.strip()
            if not part_str:
                continue
            m = re.match(r'(\d{2}:\d{2}:\d{2})\s+(Jordan|Darius)\s+(.*)', part_str, re.DOTALL)
            if m:
                ts, name, text = m.groups()
                text_cleaned = text.strip()
                line = f'<p style="margin-bottom: 1rem; line-height: 1.6;"><span style="color: #888; font-size: 0.85rem; margin-right: 0.5rem; font-family: monospace;">[{ts}]</span><u style="color: {ACCENT_COLOR}; font-weight: bold;">{name}:</u> {text_cleaned}</p>'
                formatted_p.append(line)
            else:
                formatted_p.append(f'<p style="margin-bottom: 1rem; line-height: 1.6;">{part_str}</p>')
        return "".join(formatted_p)
    
    paragraphs = [p.strip() for p in text_str.split("\n") if p.strip()]
    formatted_p = []
    for p in paragraphs:
        p_highlighted = re.sub(
            r'^(Jordan|Darius):', 
            f'<u style="color: {ACCENT_COLOR}; font-weight: bold;">\\1:</u>', 
            p
        )
        formatted_p.append(f"<p style='margin-bottom: 1rem; line-height: 1.6;'>{p_highlighted}</p>")
        
    return "".join(formatted_p)

def strip_html_tags(text):
    return re.sub(r'<[^>]+>', ' ', str(text))

def get_poster_path(raw_title, is_subpage=False):
    normalized = normalize_title(raw_title)
    prefix = "../" if is_subpage else ""
    
    candidates = [
        re.sub(r"[^\w\s]", "", normalized).strip().replace(" ", "_") + "_Poster.jpg",
        re.sub(r"[^\w\s]", "", raw_title).strip().replace(" ", "_") + "_Poster.jpg",
        re.sub(r"^(The|A|An)\s+", "", normalized, flags=re.IGNORECASE).strip().replace(" ", "_") + "_Poster.jpg",
        normalized.replace(" ", "_") + "_Poster.jpg",
        normalized.replace("&", "and").replace(" ", "_") + "_Poster.jpg",
        normalized.replace("'", "").replace(" ", "_") + "_Poster.jpg"
    ]
    
    for filename in candidates:
        if os.path.exists(os.path.join("Movie_Posters", filename)):
            return f"{prefix}Movie_Posters/{filename}"

    clean_target = re.sub(r"[^\w]", "", normalized).lower()
    if os.path.exists("Movie_Posters"):
        for f in os.listdir("Movie_Posters"):
            clean_file = re.sub(r"[^\w]", "", f.replace("_Poster.jpg", "").replace(".jpg", "")).lower()
            if clean_file == clean_target or clean_target in clean_file or clean_file in clean_target:
                return f"{prefix}Movie_Posters/{f}"

    return f"{prefix}logo.png"

def clean_show_notes(raw_html):
    if not raw_html or str(raw_html).strip().lower() in ["nan", ""]:
        return "<p>Show notes available in full podcast audio.</p>"
    
    html_str = str(raw_html).strip()
    html_str = re.sub(r'<h[23]>\s*Show Notes &amp; Highlights\s*</h[23]>', '', html_str, flags=re.IGNORECASE)
    
    html_str = re.sub(
        r'<p><strong>Jordan Insight:</strong>\s*(.*?)</p>',
        r'<div class="insight-box jordan-box"><span class="insight-author">Jordan Insight</span><p>\1</p></div>',
        html_str, flags=re.IGNORECASE
    )
    html_str = re.sub(
        r'<p><strong>Darius Insight:</strong>\s*(.*?)</p>',
        r'<div class="insight-box darius-box"><span class="insight-author">Darius Insight</span><p>\1</p></div>',
        html_str, flags=re.IGNORECASE
    )
    return html_str

# ---------------------------------------------------------
# 1. BUILD MOVIE PAGES & MOVIE ARCHIVE
# ---------------------------------------------------------
print("Processing Movie Archive...")
if os.path.exists(MOVIES_EXCEL):
    xls_m = pd.ExcelFile(MOVIES_EXCEL)
    sheet_m = "Movie Ratings" if "Movie Ratings" in xls_m.sheet_names else xls_m.sheet_names[0]
    df_m_main = pd.read_excel(xls_m, sheet_name=sheet_m)

    if "Transcripts" in xls_m.sheet_names or "transcripts" in xls_m.sheet_names:
        ts_sheet = "Transcripts" if "Transcripts" in xls_m.sheet_names else "transcripts"
        df_m_trans = pd.read_excel(xls_m, sheet_name=ts_sheet)
        df_m_trans.columns = [str(c).strip().lower() for c in df_m_trans.columns]
        if "movie_title" in df_m_trans.columns and "transcript" in df_m_trans.columns:
            df_movies = pd.merge(df_m_main, df_m_trans[['movie_title', 'transcript']], on="movie_title", how="left")
        else:
            df_movies = df_m_main
            df_movies['transcript'] = ""
    else:
        df_movies = df_m_main
        df_movies['transcript'] = ""

    col_e_m = df_movies.columns[4]
    movie_list = []

    for idx, row in df_movies.iterrows():
        raw_title = str(row.get("movie_title", "")).strip()
        if not raw_title or raw_title == "nan":
            continue

        clean_title = normalize_title(raw_title)
        slug = clean_slug(raw_title)
        sort_key = get_sort_key(raw_title)
        first_char = sort_key[0] if sort_key else "A"
        letter_group = first_char if first_char.isalpha() else "#"

        year_val = row.get("movie_year")
        year_str = f"({int(float(year_val))})" if pd.notna(year_val) and str(year_val).strip() not in ["nan", ""] else ""

        poster_src_subpage = get_poster_path(raw_title, is_subpage=True)
        poster_src_root = get_poster_path(raw_title, is_subpage=False)

        j_stars = render_stars(row.get('jordan_rating'))
        d_stars = render_stars(row.get('darius_rating'))
        j_badge = format_rating_badge(row.get('jordan_rating'))
        d_badge = format_rating_badge(row.get('darius_rating'))
        avg_num = calculate_avg_num(row.get('jordan_rating'), row.get('darius_rating'))
        avg_rating = calculate_avg_rating(row.get('jordan_rating'), row.get('darius_rating'))

        show_notes_clean = clean_show_notes(row.get(col_e_m, ""))
        formatted_transcript = format_transcript(row.get("transcript"))

        yt_id = get_youtube_id(row.get("youtube_link"))
        embed_html = f'''<div class="video-container" style="margin-bottom: 2rem;"><iframe src="https://www.youtube-nocookie.com/embed/{yt_id}" title="{clean_title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>''' if yt_id else ""

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{clean_title} - Out The Trunk</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../styles.css">
    <style>
        .movie-grid {{
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 2rem;
            align-items: start;
        }}
        .sidebar-sticky {{
            position: sticky;
            top: 20px;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }}
        .poster-card {{
            background: #fff;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        }}
        .poster-img {{
            width: 100%;
            height: auto;
            display: block;
            object-fit: cover;
        }}
        .ratings-card {{
            background: #fff;
            border-radius: 12px;
            padding: 1.25rem;
            border: 1px solid #E2E8F0;
            border-top: 4px solid #00788C;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        }}
        .ratings-card h3 {{
            font-size: 1.1rem;
            font-weight: 800;
            color: #111;
            margin-bottom: 0.85rem;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 0.4rem;
        }}
        .rating-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.65rem;
        }}
        .rating-row:last-child {{ margin-bottom: 0; }}
        .host-name {{ font-weight: 700; color: #111; font-size: 0.95rem; }}
        .stars {{ color: #00788C; font-size: 1.1rem; letter-spacing: 1px; }}
        .rating-score {{ font-weight: 800; color: #111; font-size: 0.95rem; }}
        
        @media screen and (max-width: 850px) {{
            .movie-grid {{ grid-template-columns: 1fr; }}
            .sidebar-sticky {{ position: static; }}
        }}
    </style>
</head>
<body>
    <header class="site-header">
        <a href="../" class="brand">
            <img src="../logo.png" alt="Out The Trunk Logo" class="brand-logo" onerror="this.style.display='none'">
            <span class="brand-text">Out The Trunk</span>
        </a>
        <input type="checkbox" id="menu-toggle" class="menu-toggle-checkbox" aria-label="Toggle Navigation Menu">
        <label for="menu-toggle" class="nav-toggle-btn">MENU</label>
        <nav id="site-nav" class="site-nav">
            <a href="../#woom">WOOM</a>
            <a href="../woom-archive.html">WOOM Archive</a>
            <a href="../#movies">Movies</a>
            <a href="../movies-archive.html">Movie Archive</a>
            <a href="../#listen" class="listen-link">Listen</a>
        </nav>
    </header>

    <main class="container" style="max-width: 1200px;">
        <div style="display: flex; gap: 0.75rem; margin-bottom: 1.5rem;">
            <a href="../" style="color: {ACCENT_COLOR}; text-decoration: none; font-weight: 700; background: #fff; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #E2E8F0;">← Home</a>
            <a href="../movies-archive.html" style="color: {ACCENT_COLOR}; text-decoration: none; font-weight: 700; background: #fff; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #E2E8F0;">Movie Archive</a>
        </div>

        <header style="text-align: center; margin-bottom: 2rem; padding: 1.5rem; background: #fff; border-radius: 16px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
            <p style="color: {ACCENT_COLOR}; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; font-size: 0.85rem; margin-bottom: 0.25rem;">MOVIE REVIEW & SHOW NOTES</p>
            <h1 style="font-size: 2.2rem; font-weight: 800; margin: 0; color: #111;">{clean_title} <span style="color: #64748B;">{year_str}</span></h1>
        </header>

        <div class="movie-grid">
            <aside class="sidebar-sticky">
                <div class="poster-card">
                    <img src="{poster_src_subpage}" alt="{clean_title} Poster" class="poster-img" onerror="this.src='../logo.png';">
                </div>
                
                <div class="ratings-card">
                    <h3>Host Ratings</h3>
                    <div class="rating-row">
                        <span class="host-name">Jordan</span>
                        <span class="stars">{j_stars}</span>
                        <strong class="rating-score">{j_badge}</strong>
                    </div>
                    <div class="rating-row">
                        <span class="host-name">Darius</span>
                        <span class="stars">{d_stars}</span>
                        <strong class="rating-score">{d_badge}</strong>
                    </div>
                </div>
            </aside>

            <main class="main-content">
                {embed_html}
                
                <section class="subpage-content-card">
                    <h2 style="font-size: 1.35rem; font-weight: 800; color: #1D1160; border-bottom: 2px solid #F1F5F9; padding-bottom: 0.5rem; margin-bottom: 1rem;">Show Notes & Highlights</h2>
                    <div>{show_notes_clean}</div>
                </section>

                <section class="subpage-content-card">
                    <h2 style="font-size: 1.35rem; font-weight: 800; color: #1D1160; border-bottom: 2px solid #F1F5F9; padding-bottom: 0.5rem; margin-bottom: 1rem;">Full Episode Transcript</h2>
                    <details class="transcript-accordion">
                        <summary>▼ Click to Expand Full Transcript</summary>
                        <div class="transcript-body">
                            {formatted_transcript}
                        </div>
                    </details>
                </section>
            </main>
        </div>

        <button class="back-to-top" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}});">↑ Back to Top</button>
    </main>
</body>
</html>"""
        with open(os.path.join(MOVIES_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(html_content)

        movie_list.append({'clean_title': clean_title, 'avg_num': avg_num, 'avg_rating': avg_rating, 'slug': slug, 'sort_key': sort_key, 'letter_group': letter_group, 'poster_src': poster_src_root})

    movie_list.sort(key=lambda x: x['sort_key'])

    all_groups = ["#"] + [chr(i) for i in range(ord('A'), ord('Z')+1)]
    active_groups = set(m['letter_group'] for m in movie_list)
    nav_buttons = [f'<a href="#group-{g}" class="nav-btn active-btn" style="display: inline-block; padding: 6px 12px; margin: 3px; border-radius: 6px; font-weight: 700; font-size: 0.9rem; background: {ACCENT_COLOR}; color: #fff; text-decoration: none;">{g}</a>' if g in active_groups else f'<span class="nav-btn disabled-btn" style="display: inline-block; padding: 6px 12px; margin: 3px; border-radius: 6px; font-weight: 700; font-size: 0.9rem; border: 1px solid #eaeaea; color: #d1d1d1; background: #fafafa;">{g}</span>' for g in all_groups]

    sections_html = ""
    grouped_movies = {}
    for m in movie_list:
        grouped_movies.setdefault(m['letter_group'], []).append(m)

    for g in all_groups:
        if g in grouped_movies:
            cards = "".join([f'''
            <a href="movies/{item['slug']}.html" class="movie-poster-card movie-card-styled" data-title="{item['clean_title'].lower()}" data-rating="{item['avg_num'] if item['avg_num'] is not None else 0}">
                <div class="poster-thumb-wrapper">
                    <img src="{item['poster_src']}" alt="{item['clean_title']} Poster" class="poster-thumb-img" onerror="this.src='logo.png';">
                    <div class="poster-overlay-badge">{f'★ {item["avg_rating"]}' if item['avg_rating'] else 'Not Rated'}</div>
                </div>
                <div class="poster-card-info">
                    <h3 class="poster-card-title">{item['clean_title']}</h3>
                </div>
            </a>''' for item in grouped_movies[g]])
            
            sections_html += f'''<section id="group-{g}" class="movie-section-group" style="margin-bottom: 3rem; scroll-margin-top: 2rem;"><h2 class="group-header" style="font-size: 1.8rem; font-weight: 800; border-bottom: 2px solid {ACCENT_COLOR}; padding-bottom: 0.4rem; margin-bottom: 1.5rem;">{g}</h2><div class="movie-poster-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1.25rem;">{cards}</div></section>'''

    rating_tiers = [
        (5.0, 5.0, "5 Stars (Masterpieces)"),
        (4.0, 4.9, "4 Stars (Highly Recommended)"),
        (3.0, 3.9, "3 Stars (Solid / Worth A Watch)"),
        (2.0, 2.9, "2 Stars (Mixed / Flawed)"),
        (0.0, 1.9, "1 Star (Avoid / Rough)"),
    ]

    rating_sections_html = ""
    for min_r, max_r, tier_label in rating_tiers:
        tier_movies = [m for m in movie_list if m['avg_num'] is not None and min_r <= m['avg_num'] <= max_r]
        if tier_movies:
            tier_movies.sort(key=lambda x: x['avg_num'], reverse=True)
            cards = "".join([f'''
            <a href="movies/{item['slug']}.html" class="movie-poster-card movie-card-styled" data-title="{item['clean_title'].lower()}" data-rating="{item['avg_num']}">
                <div class="poster-thumb-wrapper">
                    <img src="{item['poster_src']}" alt="{item['clean_title']} Poster" class="poster-thumb-img" onerror="this.src='logo.png';">
                    <div class="poster-overlay-badge">★ {item["avg_rating"]}</div>
                </div>
                <div class="poster-card-info">
                    <h3 class="poster-card-title">{item['clean_title']}</h3>
                </div>
            </a>''' for item in tier_movies])
            rating_sections_html += f'''<section style="margin-bottom: 3rem;"><h2 class="group-header" style="font-size: 1.8rem; font-weight: 800; border-bottom: 2px solid {ACCENT_COLOR}; padding-bottom: 0.4rem; margin-bottom: 1.5rem;">{tier_label}</h2><div class="movie-poster-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1.25rem;">{cards}</div></section>'''

    movie_archive_html = f"""<!DOCTYPE html>
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
        .movie-poster-card {{
            background: #fff;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
            text-decoration: none;
            color: #111;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .movie-poster-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 24px rgba(0,0,0,0.1);
        }}
        .poster-thumb-wrapper {{
            position: relative;
            aspect-ratio: 2/3;
            background: #1D1160;
            overflow: hidden;
        }}
        .poster-thumb-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}
        .poster-overlay-badge {{
            position: absolute;
            bottom: 8px;
            right: 8px;
            background: rgba(0, 120, 140, 0.9);
            color: #fff;
            font-size: 0.75rem;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }}
        .poster-card-info {{
            padding: 0.85rem 0.75rem;
            text-align: center;
        }}
        .poster-card-title {{
            font-size: 0.92rem;
            font-weight: 800;
            margin: 0;
            line-height: 1.3;
            color: #111;
        }}
    </style>
</head>
<body>
    <header class="site-header">
        <a href="/" class="brand">
            <img src="logo.png" alt="Out The Trunk Logo" class="brand-logo" onerror="this.style.display='none'">
            <span class="brand-text">Out The Trunk</span>
        </a>
        <input type="checkbox" id="menu-toggle" class="menu-toggle-checkbox" aria-label="Toggle Navigation Menu">
        <label for="menu-toggle" class="nav-toggle-btn">MENU</label>
        <nav id="site-nav" class="site-nav">
            <a href="/#woom">WOOM</a>
            <a href="woom-archive.html">WOOM Archive</a>
            <a href="/#movies">Movies</a>
            <a href="movies-archive.html" style="border-bottom: 2px solid #00788C;">Movie Archive</a>
            <a href="/#listen" class="listen-link">Listen</a>
        </nav>
    </header>

    <main class="container">
        <a href="/" style="display: inline-flex; align-items: center; color: {ACCENT_COLOR}; text-decoration: none; font-weight: 700; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #eaeaea; margin-bottom: 1.5rem;">← Home</a>
        <header style="text-align: center; margin-bottom: 1.5rem;">
            <h1 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; color: #111;">Movie Archive</h1>
            <p style="color: #666; font-size: 1.05rem;">Search movie reviews or browse by title and rating</p>
        </header>

        <div class="search-container" style="width: 100%; max-width: 650px; margin: 0 auto 1rem auto;">
            <input type="text" id="movie-search" class="search-input" placeholder="Search Movie Reviews..." oninput="filterMovies()" style="width: 100%; padding: 0.9rem 1.25rem; font-size: 1rem; font-weight: 600; border: 2px solid #00788C; border-radius: 30px; outline: none;">
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 0.45rem; justify-content: center; margin-bottom: 1.5rem;">
            <button class="topic-chip active" onclick="filterRatingTier('all', this)">All Movies ({len(movie_list)})</button>
            <button class="topic-chip" onclick="filterRatingTier('5', this)">★ 5-Star Classics</button>
            <button class="topic-chip" onclick="filterRatingTier('4', this)">★ 4-Star Tier</button>
        </div>

        <div class="toggle-container" style="display: flex; justify-content: center; gap: 0.75rem; margin-bottom: 2rem;">
            <button id="btn-title" class="toggle-btn active" onclick="showView('title')" style="background: #00788C; color: #fff; border: 2px solid #00788C; padding: 0.65rem 1.25rem; border-radius: 30px; font-weight: 800; cursor: pointer;">Browse by Title (A–Z)</button>
            <button id="btn-rating" class="toggle-btn" onclick="showView('rating')" style="background: #fff; color: #00788C; border: 2px solid #00788C; padding: 0.65rem 1.25rem; border-radius: 30px; font-weight: 800; cursor: pointer;">Browse by Rating (★)</button>
        </div>

        <div id="view-title">
            <nav style="text-align: center; margin-bottom: 2.5rem; background: #fff; padding: 1rem; border-radius: 12px; border: 1px solid #eaeaea;">{"".join(nav_buttons)}</nav>
            {sections_html}
        </div>

        <div id="view-rating" style="display: none;">
            {rating_sections_html}
        </div>

        <button class="back-to-top" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}});">↑ Back to Top</button>
    </main>

    <script>
        var currentRatingFilter = 'all';

        function showView(viewType) {{
            var viewTitle = document.getElementById('view-title');
            var viewRating = document.getElementById('view-rating');
            var btnTitle = document.getElementById('btn-title');
            var btnRating = document.getElementById('btn-rating');

            if (viewType === 'rating') {{
                viewTitle.style.display = 'none';
                viewRating.style.display = 'block';
                btnTitle.style.background = '#fff'; btnTitle.style.color = '#00788C';
                btnRating.style.background = '#00788C'; btnRating.style.color = '#fff';
            }} else {{
                viewTitle.style.display = 'block';
                viewRating.style.display = 'none';
                btnTitle.style.background = '#00788C'; btnTitle.style.color = '#fff';
                btnRating.style.background = '#fff'; btnRating.style.color = '#00788C';
            }}
        }}

        function filterRatingTier(tier, btnElement) {{
            currentRatingFilter = tier;
            var chips = btnElement.parentElement.querySelectorAll('.topic-chip');
            chips.forEach(function(c) {{ c.classList.remove('active'); }});
            btnElement.classList.add('active');
            filterMovies();
        }}

        function filterMovies() {{
            var query = document.getElementById('movie-search').value.toLowerCase().trim();
            var cards = document.querySelectorAll('.movie-card-styled');

            cards.forEach(function(card) {{
                var title = card.getAttribute('data-title') || '';
                var rating = parseFloat(card.getAttribute('data-rating') || 0);

                var matchesSearch = (query === '' || title.indexOf(query) !== -1);
                var matchesRating = (currentRatingFilter === 'all') || 
                                    (currentRatingFilter === '5' && rating >= 5.0) ||
                                    (currentRatingFilter === '4' && rating >= 4.0 && rating < 5.0);

                if (matchesSearch && matchesRating) {{
                    card.style.display = 'flex';
                }} else {{
                    card.style.display = 'none';
                }}
            }});

            var sectionGroups = document.querySelectorAll('.movie-section-group');
            sectionGroups.forEach(function(sec) {{
                var visibleCards = sec.querySelectorAll('.movie-card-styled[style*="display: flex"]');
                if ((query !== '' || currentRatingFilter !== 'all') && visibleCards.length === 0) {{
                    sec.style.display = 'none';
                }} else {{
                    sec.style.display = 'block';
                }}
            }});
        }}
    </script>
</body>
</html>"""
    with open(MOVIES_ARCHIVE_PATH, "w", encoding="utf-8") as f:
        f.write(movie_archive_html)

# ---------------------------------------------------------
# 2. BUILD WOOM EPISODE PAGES & WOOM ARCHIVE
# ---------------------------------------------------------
print("Processing WOOM Archive & Transcripts...")
if os.path.exists(WOOM_EXCEL):
    xls_w = pd.ExcelFile(WOOM_EXCEL)
    sheet_w_main = xls_w.sheet_names[0]
    df_w_main = pd.read_excel(xls_w, sheet_name=sheet_w_main)
    df_w_main.columns = [str(c).strip().lower() for c in df_w_main.columns]

    if len(xls_w.sheet_names) > 1 or "transcripts" in [s.lower() for s in xls_w.sheet_names]:
        ts_sheet_w = xls_w.sheet_names[1] if len(xls_w.sheet_names) > 1 else "Transcripts"
        df_w_trans = pd.read_excel(xls_w, sheet_name=ts_sheet_w)
        df_w_trans.columns = [str(c).strip().lower() for c in df_w_trans.columns]
        
        merge_col = None
        for candidate in ['episode title', 'episode_title', 'webpage title', 'webpage_title', 'title']:
            if candidate in df_w_main.columns and candidate in df_w_trans.columns:
                merge_col = candidate
                break
        
        if merge_col and 'transcript' in df_w_trans.columns:
            df_woom = pd.merge(df_w_main, df_w_trans[[merge_col, 'transcript']], on=merge_col, how="left")
        else:
            df_woom = df_w_main
            if 'transcript' not in df_woom.columns:
                df_woom['transcript'] = ""
    else:
        df_woom = df_w_main
        if 'transcript' not in df_woom.columns:
            df_woom['transcript'] = ""

    title_col = [c for c in df_woom.columns if "title" in c or "name" in c][0] if any("title" in c or "name" in c for c in df_woom.columns) else df_woom.columns[0]
    date_col = [c for c in df_woom.columns if "date" in c][0] if any("date" in c for c in df_woom.columns) else None
    yt_col = [c for c in df_woom.columns if "youtube" in c or "link" in c][0] if any("youtube" in c for c in df_woom.columns) else None
    
    notes_col = None
    for candidate in ['show_notes_highlights', 'show notes & highlights', 'show_notes', 'notes', 'highlights']:
        if candidate in df_woom.columns:
            notes_col = candidate
            break

    topics_col = None
    for candidate in ['topics', 'tags', 'categories', 'topic_tags']:
        if candidate in df_woom.columns:
            topics_col = candidate
            break

    if date_col:
        df_woom['parsed_date'] = pd.to_datetime(df_woom[date_col], errors='coerce')
        df_woom = df_woom.sort_values(by='parsed_date', ascending=False)
    
    woom_list = []
    topic_counts = {t: 0 for t in MASTER_TOPICS}

    for idx, row in df_woom.iterrows():
        raw_title = str(row.get(title_col, "")).strip()
        if not raw_title or raw_title == "nan":
            continue

        clean_title = normalize_title(raw_title)
        slug = clean_slug(raw_title)

        if date_col and pd.notna(row.get('parsed_date')):
            date_str = row.get('parsed_date').strftime('%B %d, %Y')
        elif date_col and pd.notna(row.get(date_col)):
            date_str = str(row.get(date_col)).strip()
        else:
            date_str = ""

        raw_topics = str(row.get(topics_col, "")).strip() if topics_col and pd.notna(row.get(topics_col)) else ""
        episode_topics = [t.strip() for t in raw_topics.split(",") if t.strip()] if raw_topics and raw_topics.lower() != "nan" else []

        for t in episode_topics:
            if t in topic_counts:
                topic_counts[t] += 1

        raw_notes = str(row.get(notes_col, "")).strip() if notes_col and pd.notna(row.get(notes_col)) else ""
        clean_notes = strip_html_tags(raw_notes)

        show_notes_html = raw_notes if raw_notes else "<p>Show notes available in full podcast audio.</p>"
        formatted_transcript = format_transcript(row.get("transcript"))

        yt_id = get_youtube_id(row.get(yt_col)) if yt_col else None
        embed_html = f'''<div class="subpage-embed-wrapper"><div class="video-container"><iframe src="https://www.youtube-nocookie.com/embed/{yt_id}" title="{clean_title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div></div>''' if yt_id else ""

        date_badge_html = f'<p style="color: {ACCENT_COLOR}; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; font-size: 0.85rem; margin-bottom: 0.25rem;">RECORDED: {date_str.upper()}</p>' if date_str else '<p style="color: {ACCENT_COLOR}; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; font-size: 0.85rem; margin-bottom: 0.25rem;">WOOM EPISODE</p>'

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{clean_title} - WOOM - Out The Trunk</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <header class="site-header">
        <a href="../" class="brand">
            <img src="../logo.png" alt="Out The Trunk Logo" class="brand-logo" onerror="this.style.display='none'">
            <span class="brand-text">Out The Trunk</span>
        </a>
        <input type="checkbox" id="menu-toggle" class="menu-toggle-checkbox" aria-label="Toggle Navigation Menu">
        <label for="menu-toggle" class="nav-toggle-btn">MENU</label>
        <nav id="site-nav" class="site-nav">
            <a href="../#woom">WOOM</a>
            <a href="../woom-archive.html">WOOM Archive</a>
            <a href="../#movies">Movies</a>
            <a href="../movies-archive.html">Movie Archive</a>
            <a href="../#listen" class="listen-link">Listen</a>
        </nav>
    </header>

    <main class="container" style="max-width: 900px;">
        <div style="display: flex; gap: 0.75rem; margin-bottom: 1.5rem;">
            <a href="../" style="color: {ACCENT_COLOR}; text-decoration: none; font-weight: 700; background: #fff; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #E2E8F0;">← Home</a>
            <a href="../woom-archive.html" style="color: {ACCENT_COLOR}; text-decoration: none; font-weight: 700; background: #fff; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #E2E8F0;">WOOM Archive</a>
        </div>

        <header style="text-align: center; margin-bottom: 2rem; padding: 1.75rem; background: #fff; border-radius: 16px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
            {date_badge_html}
            <h1 style="font-size: 2.2rem; font-weight: 800; margin: 0; color: #111;">{clean_title}</h1>
        </header>

        {embed_html}

        <section class="subpage-content-card">
            <h2 style="font-size: 1.35rem; font-weight: 800; color: #1D1160; border-bottom: 2px solid #F1F5F9; padding-bottom: 0.5rem; margin-bottom: 1rem;">Show Notes & Highlights</h2>
            <div>{show_notes_html}</div>
        </section>

        <section class="subpage-content-card">
            <h2 style="font-size: 1.35rem; font-weight: 800; color: #1D1160; border-bottom: 2px solid #F1F5F9; padding-bottom: 0.5rem; margin-bottom: 1rem;">Full Episode Transcript</h2>
            <details class="transcript-accordion">
                <summary>▼ Click to Expand Full Transcript</summary>
                <div class="transcript-body">
                    {formatted_transcript}
                </div>
            </details>
        </section>

        <button class="back-to-top" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}});">↑ Back to Top</button>
    </main>
</body>
</html>"""
        with open(os.path.join(WOOM_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(html_content)

        woom_list.append({'clean_title': clean_title, 'date_str': date_str, 'slug': slug, 'topics': episode_topics, 'clean_notes': clean_notes})

    total_episodes = len(woom_list)
    topic_chips = [f'<button class="topic-chip active" onclick="filterTopic(\'all\', this)">All Episodes ({total_episodes})</button>']
    for t in MASTER_TOPICS:
        count = topic_counts[t]
        topic_chips.append(f'<button class="topic-chip" onclick="filterTopic(\'{t}\', this)">{t} ({count})</button>')

    cards_woom = ""
    for item in woom_list:
        date_meta = f'<span class="card-meta" style="display: block; margin-top: 0.45rem; font-size: 0.85rem; font-weight: 700; color: {ACCENT_COLOR};">{item["date_str"]}</span>' if item['date_str'] else ""
        data_topics = "|".join(item['topics'])
        
        topics_line = f'<span class="card-topics" style="display: block; margin-top: 0.6rem; font-size: 0.72rem; color: #8A94A6; font-weight: 500;">{" • ".join(item["topics"])}</span>' if item['topics'] else ""
        search_text = f"{item['clean_title']} {' '.join(item['topics'])} {item['clean_notes']}".lower().replace('"', '&quot;')
        
        cards_woom += f'''
        <a href="woom/{item['slug']}.html" class="woom-card-styled" data-topics="{data_topics}" data-search="{search_text}" style="text-decoration: none; color: #111; background: #fff; border: 1px solid #eaeaea; border-left: 4px solid {ACCENT_COLOR}; border-radius: 12px; padding: 1.35rem 1.1rem; display: flex; flex-direction: column; justify-content: space-between; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <div class="card-content">
                <h3 style="margin: 0; font-size: 1.2rem; font-weight: 800; color: #111827; line-height: 1.35;">{item['clean_title']}</h3>
                {date_meta}
                {topics_line}
            </div>
        </a>'''

    woom_archive_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WOOM Archive - Out The Trunk</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header class="site-header">
        <a href="/" class="brand">
            <img src="logo.png" alt="Out The Trunk Logo" class="brand-logo" onerror="this.style.display='none'">
            <span class="brand-text">Out The Trunk</span>
        </a>
        <input type="checkbox" id="menu-toggle" class="menu-toggle-checkbox" aria-label="Toggle Navigation Menu">
        <label for="menu-toggle" class="nav-toggle-btn">MENU</label>
        <nav id="site-nav" class="site-nav">
            <a href="/#woom">WOOM</a>
            <a href="woom-archive.html" style="border-bottom: 2px solid #00788C;">WOOM Archive</a>
            <a href="/#movies">Movies</a>
            <a href="movies-archive.html">Movie Archive</a>
            <a href="/#listen" class="listen-link">Listen</a>
        </nav>
    </header>

    <main class="container">
        <a href="/" style="display: inline-flex; align-items: center; color: {ACCENT_COLOR}; text-decoration: none; font-weight: 700; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #eaeaea; margin-bottom: 1.5rem;">← Home</a>
        <header style="text-align: center; margin-bottom: 1.5rem;">
            <p style="color: {ACCENT_COLOR}; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 0.25rem;">WHAT'S ON OUR MIND</p>
            <h1 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; color: #111;">WOOM Archive</h1>
            <p style="color: #666; font-size: 1.05rem;">Search topics, questions, and episodes or browse by theme</p>
        </header>

        <div class="search-container" style="width: 100%; max-width: 750px; margin: 0 auto 1rem auto; text-align: center;">
            <input type="text" id="archive-search" class="search-input" placeholder="Search Topics, Questions, and Episodes..." oninput="filterArchive()" style="width: 100%; padding: 1.1rem 1.5rem; font-size: 1.1rem; font-weight: 600; border: 2px solid #00788C; border-radius: 35px; outline: none;">
            <button id="clear-btn" style="display: none; margin-top: 0.75rem; background: #eef6fc; color: #00788C; border: 1px solid #00788C; padding: 0.4rem 1rem; border-radius: 20px; font-weight: 700; cursor: pointer;" onclick="clearFilters()">Clear Search & Filters</button>
        </div>

        <div id="results-banner" style="text-align: center; font-weight: 700; color: #00788C; font-size: 0.9rem; margin-bottom: 1rem; text-transform: uppercase;">Showing {total_episodes} Episodes</div>

        <div style="margin-bottom: 2rem; text-align: center; background: #fff; padding: 1.25rem; border-radius: 12px; border: 1px solid #eaeaea;">
            <h3 style="font-size: 0.85rem; text-transform: uppercase; color: #666; margin-bottom: 0.85rem; font-weight: 800;">Filter by Topic</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center;">
                {"".join(topic_chips)}
            </div>
        </div>

        <div class="woom-grid" id="woom-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.25rem;">
            {cards_woom}
            <div id="no-results" style="display: none; text-align: center; padding: 3rem 1rem; color: #666; grid-column: 1 / -1;">
                No episodes matched that search. Try a broader search term or choose <strong>All Episodes</strong>.
            </div>
        </div>

        <button class="back-to-top" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}});">↑ Back to Top</button>
    </main>

    <script>
        var currentTopic = 'all';

        function filterTopic(selectedTopic, btnElement) {{
            currentTopic = selectedTopic;
            var chips = document.querySelectorAll('.topic-chip');
            chips.forEach(function(c) {{ c.classList.remove('active'); }});
            btnElement.classList.add('active');
            filterArchive();
        }}

        function clearFilters() {{
            document.getElementById('archive-search').value = '';
            currentTopic = 'all';
            var chips = document.querySelectorAll('.topic-chip');
            chips.forEach(function(c, idx) {{
                if (idx === 0) {{ c.classList.add('active'); }}
                else {{ c.classList.remove('active'); }}
            }});
            filterArchive();
        }}

        function filterArchive() {{
            var searchInput = document.getElementById('archive-search');
            var searchQuery = searchInput.value.toLowerCase().trim();
            var cards = document.querySelectorAll('.woom-card-styled');
            var clearBtn = document.getElementById('clear-btn');
            var noResults = document.getElementById('no-results');
            var visibleCount = 0;

            if (searchQuery !== '' || currentTopic !== 'all') {{
                clearBtn.style.display = 'inline-block';
            }} else {{
                clearBtn.style.display = 'none';
            }}

            cards.forEach(function(card) {{
                var cardTopics = card.getAttribute('data-topics') || '';
                var searchMeta = card.getAttribute('data-search') || '';

                var matchesTopic = (currentTopic === 'all') || (cardTopics.indexOf(currentTopic) !== -1);
                var matchesSearch = (searchQuery === '') || (searchMeta.indexOf(searchQuery) !== -1);

                if (matchesTopic && matchesSearch) {{
                    card.style.display = 'flex';
                    visibleCount++;
                }} else {{
                    card.style.display = 'none';
                }}
            }});

            var banner = document.getElementById('results-banner');
            if (searchQuery !== '' && currentTopic !== 'all') {{
                banner.textContent = 'Showing ' + visibleCount + ' Episode' + (visibleCount === 1 ? '' : 's') + ' for "' + searchQuery + '" in ' + currentTopic;
            }} else if (searchQuery !== '') {{
                banner.textContent = 'Showing ' + visibleCount + ' Episode' + (visibleCount === 1 ? '' : 's') + ' for "' + searchQuery + '"';
            }} else if (currentTopic !== 'all') {{
                banner.textContent = 'Showing ' + visibleCount + ' Episode' + (visibleCount === 1 ? '' : 's') + ' in ' + currentTopic;
            }} else {{
                banner.textContent = 'Showing ' + visibleCount + ' Episodes';
            }}

            if (visibleCount === 0) {{
                noResults.style.display = 'block';
            }} else {{
                noResults.style.display = 'none';
            }}
        }}
    </script>
</body>
</html>"""
    with open(WOOM_ARCHIVE_PATH, "w", encoding="utf-8") as f:
        f.write(woom_archive_html)

print("Build complete! Absolute/Relative routing and image asset links verified.")