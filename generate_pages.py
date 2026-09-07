import os
import re
import pandas as pd

# Paths & Settings
MOVIES_EXCEL = "Movie Archive Inputs_3.xlsx" if os.path.exists("Movie Archive Inputs_3.xlsx") else "Movie Archive Inputs.xlsx"
WOOM_EXCEL = "WOOM Archive Inputs.xlsx"

MOVIES_DIR = "movies"
WOOM_DIR = "woom"

MOVIES_ARCHIVE_PATH = "movies-archive.html"
WOOM_ARCHIVE_PATH = "woom-archive.html"

# Panthers Process Blue Accent
ACCENT_COLOR = "#0085CA"

os.makedirs(MOVIES_DIR, exist_ok=True)
os.makedirs(WOOM_DIR, exist_ok=True)

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def normalize_title(title):
    """Converts 'Best Man, The' to 'The Best Man'."""
    title = str(title).strip()
    match = re.match(r"^(.*?),\s*(The|A|An)$", title, re.IGNORECASE)
    if match:
        return f"{match.group(2)} {match.group(1)}"
    return title

def get_sort_key(title):
    """Strips leading 'The ', 'A ', 'An ' for alphabetical sorting."""
    normalized = normalize_title(title).upper()
    for prefix in ["THE ", "A ", "AN "]:
        if normalized.startswith(prefix):
            return normalized[len(prefix):]
    return normalized

def get_youtube_id(url):
    """Extracts YouTube video ID safely."""
    if not isinstance(url, str):
        return None
    url = url.strip()
    if not url or ("youtube.com" not in url and "youtu.be" not in url):
        return None
    match = re.search(r"(?:v=|\/embed\/|\/1\/|\/v\/|https:\/\/youtu\.be\/|\/e\/|watch\?v=|^)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def clean_slug(title):
    """Generates clean URL slug like 'my-woom-episode'."""
    normalized = normalize_title(title)
    filename = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
    return re.sub(r"[-\s]+", "-", filename)

def render_stars(rating_val):
    """Converts numeric ratings to star graphics."""
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
    """Formats numeric ratings into badges."""
    if pd.isna(val) or str(val).strip().lower() in ["nan", "n/a", ""]:
        return "N/A"
    try:
        num = float(val)
        return f"{int(num)}/5" if num.is_integer() else f"{num}/5"
    except ValueError:
        return "N/A"

def calculate_avg_rating(jordan_val, darius_val):
    """Calculates average host rating."""
    try:
        j = float(jordan_val)
        d = float(darius_val)
        avg = (j + d) / 2
        return f"{int(avg)}/5" if avg.is_integer() else f"{avg:.1f}/5"
    except (ValueError, TypeError):
        return None

def format_transcript(raw_text):
    """Formats transcripts, bolding, underlining, and highlighting Jordan: and Darius:."""
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
        year_str = str(int(float(year_val))) if pd.notna(year_val) and str(year_val).strip() not in ["nan", ""] else ""
        display_title = f"{clean_title} ({year_str})" if year_str else clean_title

        j_stars = render_stars(row.get('jordan_rating'))
        d_stars = render_stars(row.get('darius_rating'))
        j_badge = format_rating_badge(row.get('jordan_rating'))
        d_badge = format_rating_badge(row.get('darius_rating'))
        avg_rating = calculate_avg_rating(row.get('jordan_rating'), row.get('darius_rating'))

        show_notes_html = str(row.get(col_e_m, "")).strip() if pd.notna(row.get(col_e_m)) else "<p>Show notes available in full podcast audio.</p>"
        formatted_transcript = format_transcript(row.get("transcript"))

        yt_id = get_youtube_id(row.get("youtube_link"))
        embed_html = f'''<div class="hero-video-container"><iframe src="https://www.youtube-nocookie.com/embed/{yt_id}" title="{display_title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>''' if yt_id else ""

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
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Inter', sans-serif; background-color: #fcfcfc; color: #222; }}
        .subpage-nav {{ display: flex; gap: 0.75rem; margin-bottom: 1.5rem; }}
        .home-btn {{ display: inline-flex; align-items: center; gap: 0.4rem; color: {ACCENT_COLOR}; text-decoration: none; font-weight: 700; font-size: 0.95rem; background: #fff; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #eaeaea; transition: all 0.2s; }}
        .home-btn:hover {{ background: #f0f8ff; transform: translateX(-3px); border-color: {ACCENT_COLOR}; }}
        .hero-header {{ text-align: center; margin-bottom: 2rem; padding: 1.5rem; background: #fff; border-radius: 12px; border: 1px solid #eaeaea; box-shadow: 0 4px 12px rgba(0,0,0,0.04); }}
        .hero-video-container {{ margin-bottom: 2rem; position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); }}
        .hero-video-container iframe {{ position: absolute; top:0; left:0; width:100%; height:100%; border:0; }}
        .ratings-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; margin-bottom: 2rem; }}
        .rating-card {{ background: #fff; border: 1px solid #eaeaea; border-radius: 12px; padding: 1.5rem; text-align: center; }}
        .star-display {{ color: {ACCENT_COLOR}; font-size: 1.5rem; letter-spacing: 2px; margin-bottom: 0.25rem; }}
        .rating-num {{ font-size: 1.25rem; font-weight: 700; color: #111; }}
        .modern-card {{ background: #fff; border: 1px solid #eaeaea; border-radius: 12px; padding: 1.75rem; margin-bottom: 2rem; line-height: 1.6; }}
        .modern-card h2 {{ font-size: 1.35rem; font-weight: 700; margin-top: 0; border-bottom: 2px solid #f0f0f0; padding-bottom: 0.5rem; color: #111; }}
        .modern-card h3 {{ font-size: 1.1rem; color: {ACCENT_COLOR}; margin-top: 1.25rem; margin-bottom: 0.5rem; font-weight: 600; }}
        .back-to-top {{ position: fixed; bottom: 25px; right: 25px; background: {ACCENT_COLOR}; color: #fff !important; text-decoration: none; padding: 10px 16px; border-radius: 30px; font-weight: 700; font-size: 0.85rem; box-shadow: 0 4px 12px rgba(0, 133, 202, 0.4); transition: all 0.2s; z-index: 1000; }}
        .back-to-top:hover {{ background: #006dae; transform: translateY(-3px); }}
    </style>
</head>
<body id="top">
    <main class="container" style="max-width: 850px; margin: 0 auto; padding: 2rem 1rem;">
        <div class="subpage-nav">
            <a href="../index.html" class="home-btn">← Home</a>
            <a href="../movies-archive.html" class="home-btn">Movie Archive</a>
        </div>
        <header class="hero-header">
            <p style="color: {ACCENT_COLOR}; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; font-size: 0.85rem; margin-bottom: 0.25rem;">MOVIE REVIEW & SHOW NOTES</p>
            <h1 style="font-size: 2.2rem; font-weight: 800; margin: 0; color: #111;">{display_title}</h1>
        </header>
        {embed_html}
        <section class="ratings-grid">
            <div class="rating-card">
                <h3>Jordan's Rating</h3>
                <div class="star-display">{j_stars}</div>
                <div class="rating-num">{j_badge}</div>
            </div>
            <div class="rating-card">
                <h3>Darius's Rating</h3>
                <div class="star-display">{d_stars}</div>
                <div class="rating-num">{d_badge}</div>
            </div>
        </section>
        <section class="modern-card">{show_notes_html}</section>
        <section class="modern-card">
            <h2>Full Episode Transcript</h2>
            <div style="margin-top: 1rem;">{formatted_transcript}</div>
        </section>
        <a href="#top" class="back-to-top">↑ Back to Top</a>
    </main>
</body>
</html>"""
        with open(os.path.join(MOVIES_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(html_content)

        movie_list.append({'clean_title': clean_title, 'avg_rating': avg_rating, 'slug': slug, 'sort_key': sort_key, 'letter_group': letter_group})

    movie_list.sort(key=lambda x: x['sort_key'])

    # Build Movie Archive HTML
    all_groups = ["#"] + [chr(i) for i in range(ord('A'), ord('Z')+1)]
    active_groups = set(m['letter_group'] for m in movie_list)
    nav_buttons = [f'<a href="#group-{g}" class="nav-btn active-btn">{g}</a>' if g in active_groups else f'<span class="nav-btn disabled-btn">{g}</span>' for g in all_groups]

    sections_html = ""
    grouped_movies = {}
    for m in movie_list:
        grouped_movies.setdefault(m['letter_group'], []).append(m)

    for g in all_groups:
        if g in grouped_movies:
            cards = "".join([f'''<a href="movies/{item['slug']}.html" class="movie-card-styled"><div class="card-content"><h3>{item['clean_title']}</h3>{f'<span class="card-meta"> ★ {item["avg_rating"]}</span>' if item['avg_rating'] else ''}</div></a>''' for item in grouped_movies[g]])
            sections_html += f'''<section id="group-{g}" style="margin-bottom: 3rem; scroll-margin-top: 2rem;"><h2 class="group-header">{g}</h2><div class="movie-grid">{cards}</div></section>'''

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
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Inter', sans-serif; background-color: #fcfcfc; color: #222; }}
        .home-btn {{ display: inline-flex; align-items: center; color: {ACCENT_COLOR}; text-decoration: none; font-weight: 700; font-size: 0.95rem; background: #fff; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #eaeaea; transition: all 0.2s; margin-bottom: 1.5rem; }}
        .home-btn:hover {{ background: #f0f8ff; transform: translateX(-3px); border-color: {ACCENT_COLOR}; }}
        .az-navigation {{ text-align: center; margin-bottom: 2.5rem; line-height: 2.2; background: #fff; padding: 1rem; border-radius: 12px; border: 1px solid #eaeaea; }}
        .nav-btn {{ display: inline-block; padding: 6px 12px; margin: 3px; border-radius: 6px; font-weight: 700; font-size: 0.9rem; transition: all 0.2s; }}
        .active-btn {{ background-color: {ACCENT_COLOR}; color: #fff !important; border: 1px solid {ACCENT_COLOR}; text-decoration: none; }}
        .active-btn:hover {{ background-color: #006dae; transform: translateY(-2px); }}
        .disabled-btn {{ border: 1px solid #eaeaea; color: #d1d1d1; background-color: #fafafa; }}
        .group-header {{ font-size: 1.8rem; font-weight: 800; border-bottom: 2px solid {ACCENT_COLOR}; padding-bottom: 0.4rem; margin-bottom: 1.5rem; color: #111; }}
        .movie-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1.25rem; }}
        .movie-card-styled {{ text-decoration: none; color: #111; background: #fff; border: 1px solid #eaeaea; border-left: 4px solid {ACCENT_COLOR}; border-radius: 10px; padding: 1.25rem 1rem; display: flex; align-items: center; justify-content: center; text-align: center; box-shadow: 0 3px 8px rgba(0,0,0,0.03); transition: all 0.2s; }}
        .movie-card-styled:hover {{ transform: translateY(-4px); box-shadow: 0 8px 16px rgba(0, 133, 202, 0.15); border-color: {ACCENT_COLOR}; background-color: #f8fcff; }}
        .movie-card-styled h3 {{ margin: 0; font-size: 1.05rem; font-weight: 600; }}
        .card-meta {{ display: block; margin-top: 0.35rem; font-size: 0.8rem; font-weight: 700; color: {ACCENT_COLOR}; }}
        .back-to-top {{ position: fixed; bottom: 25px; right: 25px; background: {ACCENT_COLOR}; color: #fff !important; text-decoration: none; padding: 10px 16px; border-radius: 30px; font-weight: 700; font-size: 0.85rem; box-shadow: 0 4px 12px rgba(0, 133, 202, 0.4); transition: all 0.2s; z-index: 1000; }}
        .back-to-top:hover {{ background: #006dae; transform: translateY(-3px); }}
    </style>
</head>
<body id="top">
    <main class="container" style="max-width: 1000px; margin: 0 auto; padding: 2rem 1rem;">
        <a href="index.html" class="home-btn">← Home</a>
        <header style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; color: #111;">Movie Archive</h1>
            <p style="color: #666; font-size: 1.05rem;">Browse all movie reviews and show notes</p>
        </header>
        <nav class="az-navigation">{"".join(nav_buttons)}</nav>
        {sections_html}
        <a href="#top" class="back-to-top">↑ Back to Top</a>
    </main>
</body>
</html>"""
    with open(MOVIES_ARCHIVE_PATH, "w", encoding="utf-8") as f:
        f.write(movie_archive_html)

# ---------------------------------------------------------
# 2. BUILD WOOM EPISODE PAGES & WOOM ARCHIVE
# ---------------------------------------------------------
print("Processing WOOM Archive...")
if os.path.exists(WOOM_EXCEL):
    xls_w = pd.ExcelFile(WOOM_EXCEL)
    sheet_w = "WOOM Episodes" if "WOOM Episodes" in xls_w.sheet_names else xls_w.sheet_names[0]
    df_w_main = pd.read_excel(xls_w, sheet_name=sheet_w)

    # Clean column names for flexibility
    df_w_main.columns = [str(c).strip().lower() for c in df_w_main.columns]

    if "transcripts" in xls_w.sheet_names or "Transcripts" in xls_w.sheet_names:
        ts_sheet_w = "Transcripts" if "Transcripts" in xls_w.sheet_names else "transcripts"
        df_w_trans = pd.read_excel(xls_w, sheet_name=ts_sheet_w)
        df_w_trans.columns = [str(c).strip().lower() for c in df_w_trans.columns]
        
        # Find matching title column
        t_col = "episode_title" if "episode_title" in df_w_main.columns else "title"
        if t_col in df_w_trans.columns and "transcript" in df_w_trans.columns:
            df_woom = pd.merge(df_w_main, df_w_trans[[t_col, 'transcript']], on=t_col, how="left")
        else:
            df_woom = df_w_main
            df_woom['transcript'] = ""
    else:
        df_woom = df_w_main
        if 'transcript' not in df_woom.columns:
            df_woom['transcript'] = ""

    # Identify key columns safely
    title_col = [c for c in df_woom.columns if "title" in c or "name" in c][0] if any("title" in c or "name" in c for c in df_woom.columns) else df_woom.columns[0]
    date_col = [c for c in df_woom.columns if "date" in c][0] if any("date" in c for c in df_woom.columns) else None
    yt_col = [c for c in df_woom.columns if "youtube" in c or "link" in c][0] if any("youtube" in c or "link" in c for c in df_woom.columns) else None
    notes_col = [c for c in df_woom.columns if "notes" in c or "highlights" in c or "show" in c][0] if any("notes" in c or "highlights" in c or "show" in c for c in df_woom.columns) else None

    # Date parsing and sorting (Newest recorded episodes at top)
    if date_col:
        df_woom['parsed_date'] = pd.to_datetime(df_woom[date_col], errors='coerce')
        df_woom = df_woom.sort_values(by='parsed_date', ascending=False)
    
    woom_list = []

    for idx, row in df_woom.iterrows():
        raw_title = str(row.get(title_col, "")).strip()
        if not raw_title or raw_title == "nan":
            continue

        clean_title = normalize_title(raw_title)
        slug = clean_slug(raw_title)

        # Date Display
        if date_col and pd.notna(row.get('parsed_date')):
            date_str = row.get('parsed_date').strftime('%B %d, %Y')
        elif date_col and pd.notna(row.get(date_col)):
            date_str = str(row.get(date_col)).strip()
        else:
            date_str = ""

        show_notes_html = str(row.get(notes_col, "")).strip() if notes_col and pd.notna(row.get(notes_col)) else "<p>Show notes available in full podcast audio.</p>"
        formatted_transcript = format_transcript(row.get("transcript"))

        yt_id = get_youtube_id(row.get(yt_col)) if yt_col else None
        embed_html = f'''<div class="hero-video-container"><iframe src="https://www.youtube-nocookie.com/embed/{yt_id}" title="{clean_title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>''' if yt_id else ""

        date_badge_html = f'<p style="color: {ACCENT_COLOR}; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; font-size: 0.85rem; margin-bottom: 0.25rem;">RECORDED: {date_str.upper()}</p>' if date_str else '<p style="color: {ACCENT_COLOR}; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; font-size: 0.85rem; margin-bottom: 0.25rem;">WOOM EPISODE</p>'

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{clean_title} - WOOM - Out The Trunk</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../styles.css">
    <style>
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Inter', sans-serif; background-color: #fcfcfc; color: #222; }}
        .subpage-nav {{ display: flex; gap: 0.75rem; margin-bottom: 1.5rem; }}
        .home-btn {{ display: inline-flex; align-items: center; gap: 0.4rem; color: {ACCENT_COLOR}; text-decoration: none; font-weight: 700; font-size: 0.95rem; background: #fff; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #eaeaea; transition: all 0.2s; }}
        .home-btn:hover {{ background: #f0f8ff; transform: translateX(-3px); border-color: {ACCENT_COLOR}; }}
        .hero-header {{ text-align: center; margin-bottom: 2rem; padding: 1.5rem; background: #fff; border-radius: 12px; border: 1px solid #eaeaea; box-shadow: 0 4px 12px rgba(0,0,0,0.04); }}
        .hero-video-container {{ margin-bottom: 2rem; position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); }}
        .hero-video-container iframe {{ position: absolute; top:0; left:0; width:100%; height:100%; border:0; }}
        .modern-card {{ background: #fff; border: 1px solid #eaeaea; border-radius: 12px; padding: 1.75rem; margin-bottom: 2rem; line-height: 1.6; }}
        .modern-card h2 {{ font-size: 1.35rem; font-weight: 700; margin-top: 0; border-bottom: 2px solid #f0f0f0; padding-bottom: 0.5rem; color: #111; }}
        .modern-card h3 {{ font-size: 1.1rem; color: {ACCENT_COLOR}; margin-top: 1.25rem; margin-bottom: 0.5rem; font-weight: 600; }}
        .back-to-top {{ position: fixed; bottom: 25px; right: 25px; background: {ACCENT_COLOR}; color: #fff !important; text-decoration: none; padding: 10px 16px; border-radius: 30px; font-weight: 700; font-size: 0.85rem; box-shadow: 0 4px 12px rgba(0, 133, 202, 0.4); transition: all 0.2s; z-index: 1000; }}
        .back-to-top:hover {{ background: #006dae; transform: translateY(-3px); }}
    </style>
</head>
<body id="top">
    <main class="container" style="max-width: 850px; margin: 0 auto; padding: 2rem 1rem;">
        <div class="subpage-nav">
            <a href="../index.html" class="home-btn">← Home</a>
            <a href="../woom-archive.html" class="home-btn">WOOM Archive</a>
        </div>
        <header class="hero-header">
            {date_badge_html}
            <h1 style="font-size: 2.2rem; font-weight: 800; margin: 0; color: #111;">{clean_title}</h1>
        </header>
        {embed_html}
        <section class="modern-card">{show_notes_html}</section>
        <section class="modern-card">
            <h2>Full Episode Transcript</h2>
            <div style="margin-top: 1rem;">{formatted_transcript}</div>
        </section>
        <a href="#top" class="back-to-top">↑ Back to Top</a>
    </main>
</body>
</html>"""
        with open(os.path.join(WOOM_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(html_content)

        woom_list.append({'clean_title': clean_title, 'date_str': date_str, 'slug': slug})

    # Build WOOM Archive Cards
    cards_woom = ""
    for item in woom_list:
        date_meta = f'<span class="card-meta">{item["date_str"]}</span>' if item['date_str'] else ""
        cards_woom += f'''
        <a href="woom/{item['slug']}.html" class="woom-card-styled">
            <div class="card-content">
                <h3>{item['clean_title']}</h3>
                {date_meta}
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <style>
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Inter', sans-serif; background-color: #fcfcfc; color: #222; }}
        .home-btn {{ display: inline-flex; align-items: center; color: {ACCENT_COLOR}; text-decoration: none; font-weight: 700; font-size: 0.95rem; background: #fff; padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid #eaeaea; transition: all 0.2s; margin-bottom: 1.5rem; }}
        .home-btn:hover {{ background: #f0f8ff; transform: translateX(-3px); border-color: {ACCENT_COLOR}; }}
        .woom-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.25rem; }}
        .woom-card-styled {{ text-decoration: none; color: #111; background: #fff; border: 1px solid #eaeaea; border-left: 4px solid {ACCENT_COLOR}; border-radius: 10px; padding: 1.25rem 1rem; display: flex; align-items: center; justify-content: center; text-align: center; box-shadow: 0 3px 8px rgba(0,0,0,0.03); transition: all 0.2s; }}
        .woom-card-styled:hover {{ transform: translateY(-4px); box-shadow: 0 8px 16px rgba(0, 133, 202, 0.15); border-color: {ACCENT_COLOR}; background-color: #f8fcff; }}
        .woom-card-styled h3 {{ margin: 0; font-size: 1.1rem; font-weight: 600; line-height: 1.35; }}
        .card-meta {{ display: block; margin-top: 0.4rem; font-size: 0.85rem; font-weight: 700; color: {ACCENT_COLOR}; }}
        .back-to-top {{ position: fixed; bottom: 25px; right: 25px; background: {ACCENT_COLOR}; color: #fff !important; text-decoration: none; padding: 10px 16px; border-radius: 30px; font-weight: 700; font-size: 0.85rem; box-shadow: 0 4px 12px rgba(0, 133, 202, 0.4); transition: all 0.2s; z-index: 1000; }}
        .back-to-top:hover {{ background: #006dae; transform: translateY(-3px); }}
    </style>
</head>
<body id="top">
    <main class="container" style="max-width: 1000px; margin: 0 auto; padding: 2rem 1rem;">
        <a href="index.html" class="home-btn">← Home</a>
        <header style="text-align: center; margin-bottom: 2.5rem;">
            <p style="color: {ACCENT_COLOR}; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 0.25rem;">WHAT'S ON OUR MIND</p>
            <h1 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; color: #111;">WOOM Archive</h1>
            <p style="color: #666; font-size: 1.05rem;">Browse all WOOM episodes chronologically by recorded date</p>
        </header>

        <div class="woom-grid">
            {cards_woom}
        </div>

        <a href="#top" class="back-to-top">↑ Back to Top</a>
    </main>
</body>
</html>"""
    with open(WOOM_ARCHIVE_PATH, "w", encoding="utf-8") as f:
        f.write(woom_archive_html)

print("ALL Movie and WOOM archives generated successfully!")