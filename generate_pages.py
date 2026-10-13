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
PRIMARY_COLOR = "#1D1160"

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
        return "Not Rated"
    try:
        num = float(val)
        return f"{int(num)}/5" if num.is_integer() else f"{num:.1f}/5"
    except ValueError:
        return "Not Rated"

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
        return "<p style='color: #64748B; font-style: italic;'>Transcript coming soon.</p>"
    
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
                speaker_class = "speaker-jordan" if name.lower() == "jordan" else "speaker-darius"
                line = (
                    f'<div class="transcript-entry">'
                    f'<span class="transcript-ts">[{ts}]</span>'
                    f'<span class="transcript-badge {speaker_class}">{name}</span>'
                    f'<span class="transcript-text">{text.strip()}</span>'
                    f'</div>'
                )
                formatted_p.append(line)
            else:
                formatted_p.append(f'<div class="transcript-entry"><span class="transcript-text">{part_str}</span></div>')
        return "".join(formatted_p)
    
    paragraphs = [p.strip() for p in text_str.split("\n") if p.strip()]
    formatted_p = []
    for p in paragraphs:
        p_sub = re.sub(
            r'^(Jordan|Darius):\s*(.*)', 
            lambda m: f'<div class="transcript-entry"><span class="transcript-badge speaker-{m.group(1).lower()}">{m.group(1)}</span><span class="transcript-text">{m.group(2)}</span></div>', 
            p
        )
        if '<div class="transcript-entry">' in p_sub:
            formatted_p.append(p_sub)
        else:
            formatted_p.append(f'<div class="transcript-entry"><span class="transcript-text">{p}</span></div>')
        
    return "".join(formatted_p)

def strip_html_tags(text):
    return re.sub(r'<[^>]+>', ' ', str(text))

def get_poster_path(raw_title, is_subpage=True):
    base_prefix = "../Movie_Posters/" if is_subpage else "Movie_Posters/"
    fallback = "../logo.png" if is_subpage else "logo.png"
    
    if not raw_title or str(raw_title).strip().lower() in ["nan", ""]:
        return fallback

    raw_clean = str(raw_title).strip()
    norm = normalize_title(raw_clean)
    
    def to_snake(text):
        # Swap hyphens for spaces so they are processed safely
        t = str(text).replace("-", " ")
        t = re.sub(r"[^\w\s]", "", t)
        return re.sub(r"\s+", "_", t.strip())

    # Build a highly resilient list of possible filename bases
    # This ensures "Best Man, The" maps cleanly to "Best_Man_Poster.jpg"
    bases = [
        norm,
        norm.replace('&', 'And'),
        re.sub(r'\bNo\.?\b', 'Number', norm.replace('&', 'And'), flags=re.IGNORECASE).replace('2', 'Two'),
        re.sub(r'^(The|A|An)\s+', '', norm, flags=re.IGNORECASE),
        re.sub(r'^(The|A|An)\s+', '', norm.replace('&', 'And'), flags=re.IGNORECASE),
        raw_clean,
        re.sub(r',\s*(The|A|An)$', '', raw_clean, flags=re.IGNORECASE) 
    ]
    
    candidates = []
    for b in bases:
        snaked = to_snake(b)
        candidates.append(f"{snaked}_Poster.jpg")
        candidates.append(f"{snaked.replace('_', '')}_Poster.jpg")
    
    posters_dir = "Movie_Posters"
    if os.path.exists(posters_dir):
        available_files = {f.lower(): f for f in os.listdir(posters_dir)}
        for c in candidates:
            if c.lower() in available_files:
                return f"{base_prefix}{available_files[c.lower()]}"
    
    return fallback

def clean_show_notes(raw_html):
    if not raw_html or str(raw_html).strip().lower() in ["nan", ""]:
        return "<p>Show notes available in full podcast audio.</p>"
    
    html_str = str(raw_html).strip()
    html_str = re.sub(r'<h[23]>\s*Show Notes &amp; Highlights\s*</h[23]>', '', html_str, flags=re.IGNORECASE)
    return html_str

# ---------------------------------------------------------
# 1. BUILD MOVIE PAGES & MOVIE ARCHIVE
# ---------------------------------------------------------
print("Processing Movie Archive & Subpages...")
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

        poster_subpage = get_poster_path(raw_title, is_subpage=True)
        poster_archive = get_poster_path(raw_title, is_subpage=False)

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
            gap: 2.25rem;
            align-items: start;
        }}
        .sidebar-sticky {{
            position: sticky;
            top: 24px;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}
        .poster-card {{
            background: #fff;
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid #E2E8F0;
            box-shadow: 0 10px 25px rgba(0,0,0,0.06);
        }}
        .poster-img {{
            width: 100%;
            height: auto;
            aspect-ratio: 2/3;
            display: block;
            object-fit: cover;
            background: #0f0a28;
        }}
        .ratings-box {{
            background: #fff;
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid #E2E8F0;
            border-top: 5px solid #00788C;
            box-shadow: 0 8px 20px rgba(0,0,0,0.04);
        }}
        .ratings-box h3 {{
            font-size: 1.15rem;
            font-weight: 800;
            color: #1D1160;
            margin-bottom: 1.25rem;
            border-bottom: 2px solid #F1F5F9;
            padding-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .host-verdict {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.65rem 0;
            border-bottom: 1px solid #F8FAFC;
        }}
        .host-verdict:last-child {{ border-bottom: none; }}
        .host-name {{ font-weight: 800; color: #1D1160; font-size: 1rem; }}
        .host-score {{
            background: #E6F3F5;
            color: #00788C;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.9rem;
            margin-left: 0.5rem;
        }}
        .stars {{ color: #00788C; font-size: 1.05rem; letter-spacing: 1px; }}
        
        @media screen and (max-width: 850px) {{
            .movie-grid {{ grid-template-columns: 1fr; }}
            .sidebar-sticky {{ position: static; }}
            .poster-card {{ max-width: 320px; margin: 0 auto; }}
        }}
    </style>
</head>
<body>
    <header class="site-header">
        <a href="/" class="brand">
            <img src="../logo.png" alt="Out The Trunk Logo" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid #00788C;" onerror="this.style.display='none'">
            <span class="brand-text">Out The Trunk</span>
        </a>
        <input type="checkbox" id="menu-toggle" class="menu-toggle-checkbox" aria-label="Toggle Navigation Menu">
        <label for="menu-toggle" class="nav-toggle-btn">MENU</label>
        <nav id="site-nav" class="site-nav">
            <a href="/#movies">Movies</a>
            <a href="../movies-archive.html">Movie Archive</a>
            <a href="/#woom">WOOM</a>
            <a href="../woom-archive.html">WOOM Archive</a>
            <a href="/#listen" class="listen-link">Listen</a>
        </nav>
    </header>

    <main class="container" style="max-width: 1200px;">
        <div style="display: flex; gap: 0.75rem; margin-bottom: 1.5rem;">
            <a href="/" class="nav-breadcrumb">← Home</a>
            <a href="../movies-archive.html" class="nav-breadcrumb">Movie Archive</a>
        </div>

        <header class="subpage-header-card">
            <p class="subpage-eyebrow">MOVIE REVIEW & SHOW NOTES</p>
            <h1 class="subpage-title">{clean_title} <span style="color: #64748B; font-weight: 500;">{year_str}</span></h1>
            {f'<div style="margin-top: 0.5rem;"><span class="badge-avg">Average Host Rating: ★ {avg_rating}</span></div>' if avg_rating else ''}
        </header>

        <div class="movie-grid">
            <aside class="sidebar-sticky">
                <div class="poster-card">
                    <img src="{poster_subpage}" alt="{clean_title} Poster" class="poster-img" onerror="this.src='../logo.png';">
                </div>
                
                <div class="ratings-box">
                    <h3>Host Ratings</h3>
                    <div class="host-verdict">
                        <span class="host-name">Jordan</span>
                        <div>
                            <span class="stars">{j_stars}</span>
                            <span class="host-score">{j_badge}</span>
                        </div>
                    </div>
                    <div class="host-verdict">
                        <span class="host-name">Darius</span>
                        <div>
                            <span class="stars">{d_stars}</span>
                            <span class="host-score">{d_badge}</span>
                        </div>
                    </div>
                </div>
            </aside>

            <main class="main-content">
                {embed_html}
                
                <section class="subpage-content-card">
                    <h2 class="subpage-section-heading">Show Notes & Highlights</h2>
                    <div class="show-notes-body">{show_notes_clean}</div>
                </section>

                <section class="subpage-content-card">
                    <h2 class="subpage-section-heading">Full Episode Transcript</h2>
                    <div class="transcript-container">{formatted_transcript}</div>
                </section>
            </main>
        </div>

        <button class="back-to-top" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}});">↑ Back to Top</button>
    </main>
</body>
</html>"""
        with open(os.path.join(MOVIES_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(html_content)

        movie_list.append({
            'clean_title': clean_title,
            'year_str': year_str,
            'avg_num': avg_num,
            'avg_rating': avg_rating,
            'slug': slug,
            'sort_key': sort_key,
            'letter_group': letter_group,
            'poster_src': poster_archive
        })

    movie_list.sort(key=lambda x: x['sort_key'])

    all_groups = ["#"] + [chr(i) for i in range(ord('A'), ord('Z')+1)]
    active_groups = set(m['letter_group'] for m in movie_list)
    nav_buttons = [
        f'<a href="#group-{g}" class="nav-alpha-btn active">{g}</a>' if g in active_groups else f'<span class="nav-alpha-btn disabled">{g}</span>' 
        for g in all_groups
    ]

    def render_movie_card(item):
        rating_markup = f'<span class="movie-rating-badge">★ {item["avg_rating"]}</span>' if item['avg_rating'] else '<span class="movie-rating-badge not-rated">Not Rated</span>'
        return f'''
        <a href="movies/{item['slug']}.html" class="movie-archive-card" data-title="{item['clean_title'].lower()}">
            <div class="archive-poster-wrap">
                <img src="{item['poster_src']}" alt="{item['clean_title']} Poster" class="archive-poster-img" loading="lazy" onerror="this.src='logo.png';">
                {rating_markup}
            </div>
            <div class="archive-card-details">
                <h3 class="archive-card-title">{item['clean_title']}</h3>
                <span class="archive-card-year">{item['year_str']}</span>
            </div>
        </a>'''

    sections_html = ""
    grouped_movies = {}
    for m in movie_list:
        grouped_movies.setdefault(m['letter_group'], []).append(m)

    for g in all_groups:
        if g in grouped_movies:
            cards = "".join([render_movie_card(item) for item in grouped_movies[g]])
            sections_html += f'''
            <section id="group-{g}" class="movie-section-group">
                <h2 class="group-header"><span class="letter-badge">{g}</span></h2>
                <div class="movie-archive-grid">{cards}</div>
            </section>'''

    rating_tiers = [
        (5.0, 5.0, "5 Stars — Masterpieces"),
        (4.0, 4.9, "4 Stars — Highly Recommended"),
        (3.0, 3.9, "3 Stars — Solid / Worth A Watch"),
        (2.0, 2.9, "2 Stars — Mixed / Flawed"),
        (0.0, 1.9, "1 Star — Rough / Pass"),
    ]

    rating_sections_html = ""
    for min_r, max_r, tier_label in rating_tiers:
        tier_movies = [m for m in movie_list if m['avg_num'] is not None and min_r <= m['avg_num'] <= max_r]
        if tier_movies:
            tier_movies.sort(key=lambda x: x['avg_num'], reverse=True)
            cards = "".join([render_movie_card(item) for item in tier_movies])
            rating_sections_html += f'''
            <section class="rating-tier-section">
                <h2 class="group-header">{tier_label}</h2>
                <div class="movie-archive-grid">{cards}</div>
            </section>'''

    movie_archive_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Movie Archive - Out The Trunk</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header class="site-header">
        <a href="/" class="brand">
            <img src="logo.png" alt="Out The Trunk Logo" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid #00788C;" onerror="this.style.display='none'">
            <span class="brand-text">Out The Trunk</span>
        </a>
        <input type="checkbox" id="menu-toggle" class="menu-toggle-checkbox" aria-label="Toggle Navigation Menu">
        <label for="menu-toggle" class="nav-toggle-btn">MENU</label>
        <nav id="site-nav" class="site-nav">
            <a href="/#movies">Movies</a>
            <a href="movies-archive.html" class="active-nav">Movie Archive</a>
            <a href="/#woom">WOOM</a>
            <a href="woom-archive.html">WOOM Archive</a>
            <a href="/#listen" class="listen-link">Listen</a>
        </nav>
    </header>

    <main class="container">
        <div style="margin-bottom: 1.5rem;">
            <a href="/" class="nav-breadcrumb">← Home</a>
        </div>
        
        <header class="archive-header-card">
            <p class="subpage-eyebrow">CATALOG & RATINGS</p>
            <h1 class="archive-main-title">Movie Review Archive</h1>
            <p class="archive-subtitle">Explore 39+ films broken down by Jordan & Darius. Search titles or sort by average host score.</p>
        </header>

        <div class="search-container" style="max-width: 650px; margin: 0 auto 1.5rem auto;">
            <input type="text" id="movie-search" class="search-input" placeholder="Search by title, director, or keyword..." oninput="filterMovies()">
        </div>

        <div class="toggle-container" style="display: flex; justify-content: center; gap: 0.75rem; margin-bottom: 2rem;">
            <button id="btn-title" class="toggle-btn active" onclick="showView('title')">Browse by Title (A–Z)</button>
            <button id="btn-rating" class="toggle-btn" onclick="showView('rating')">Browse by Rating (★)</button>
        </div>

        <div id="view-title">
            <nav class="alpha-nav-bar">{"".join(nav_buttons)}</nav>
            {sections_html}
        </div>

        <div id="view-rating" style="display: none;">
            {rating_sections_html}
        </div>

        <button class="back-to-top" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}});">↑ Back to Top</button>
    </main>

    <script>
        function showView(viewType) {{
            var viewTitle = document.getElementById('view-title');
            var viewRating = document.getElementById('view-rating');
            var btnTitle = document.getElementById('btn-title');
            var btnRating = document.getElementById('btn-rating');

            if (viewType === 'rating') {{
                viewTitle.style.display = 'none';
                viewRating.style.display = 'block';
                btnTitle.classList.remove('active');
                btnRating.classList.add('active');
            }} else {{
                viewTitle.style.display = 'block';
                viewRating.style.display = 'none';
                btnTitle.classList.add('active');
                btnRating.classList.remove('active');
            }}
        }}

        function filterMovies() {{
            var query = document.getElementById('movie-search').value.toLowerCase().trim();
            var cards = document.querySelectorAll('.movie-archive-card');

            cards.forEach(function(card) {{
                var title = card.getAttribute('data-title') || '';
                if (query === '' || title.indexOf(query) !== -1) {{
                    card.style.display = 'flex';
                }} else {{
                    card.style.display = 'none';
                }}
            }});

            var sectionGroups = document.querySelectorAll('.movie-section-group, .rating-tier-section');
            sectionGroups.forEach(function(sec) {{
                var visibleCards = sec.querySelectorAll('.movie-archive-card[style*="display: flex"]');
                if (query !== '' && visibleCards.length === 0) {{
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
print("Processing WOOM Archive & Subpages...")
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

        # Strip redundant trailing date parentheses from the display title
        display_title = re.sub(r"\s*\(WOOM\s*\d{1,2}/\d{1,2}/\d{2,4}\)", "", clean_title, flags=re.IGNORECASE).strip()

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
        embed_html = f'''<div class="subpage-embed-wrapper"><div class="video-container"><iframe src="https://www.youtube-nocookie.com/embed/{yt_id}" title="{display_title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div></div>''' if yt_id else ""

        date_badge_html = f'<p class="subpage-eyebrow">RECORDED: {date_str.upper()}</p>' if date_str else '<p class="subpage-eyebrow">WOOM EPISODE</p>'

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_title} - WOOM - Out The Trunk</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <header class="site-header">
        <a href="/" class="brand">
            <img src="../logo.png" alt="Out The Trunk Logo" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid #00788C;" onerror="this.style.display='none'">
            <span class="brand-text">Out The Trunk</span>
        </a>
        <input type="checkbox" id="menu-toggle" class="menu-toggle-checkbox" aria-label="Toggle Navigation Menu">
        <label for="menu-toggle" class="nav-toggle-btn">MENU</label>
        <nav id="site-nav" class="site-nav">
            <a href="/#woom">WOOM</a>
            <a href="../woom-archive.html">WOOM Archive</a>
            <a href="/#movies">Movies</a>
            <a href="../movies-archive.html">Movie Archive</a>
            <a href="/#listen" class="listen-link">Listen</a>
        </nav>
    </header>

    <main class="container" style="max-width: 900px;">
        <div style="display: flex; gap: 0.75rem; margin-bottom: 1.5rem;">
            <a href="/" class="nav-breadcrumb">← Home</a>
            <a href="../woom-archive.html" class="nav-breadcrumb">WOOM Archive</a>
        </div>

        <header class="subpage-header-card">
            {date_badge_html}
            <h1 class="subpage-title">{display_title}</h1>
        </header>

        {embed_html}

        <section class="subpage-content-card">
            <h2 class="subpage-section-heading">Show Notes & Highlights</h2>
            <div class="show-notes-body">{show_notes_html}</div>
        </section>

        <section class="subpage-content-card">
            <h2 class="subpage-section-heading">Full Episode Transcript</h2>
            <div class="transcript-container">{formatted_transcript}</div>
        </section>

        <button class="back-to-top" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}});">↑ Back to Top</button>
    </main>
</body>
</html>"""
        with open(os.path.join(WOOM_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(html_content)

        woom_list.append({
            'display_title': display_title,
            'clean_title': clean_title,
            'date_str': date_str,
            'slug': slug,
            'topics': episode_topics,
            'clean_notes': clean_notes
        })

    total_episodes = len(woom_list)
    topic_chips = [f'<button class="topic-chip active" onclick="filterTopic(\'all\', this)">All Episodes ({total_episodes})</button>']
    for t in MASTER_TOPICS:
        count = topic_counts[t]
        topic_chips.append(f'<button class="topic-chip" onclick="filterTopic(\'{t}\', this)">{t} ({count})</button>')

    cards_woom = ""
    for item in woom_list:
        date_meta = f'<span class="woom-card-date">{item["date_str"]}</span>' if item['date_str'] else ""
        data_topics = "|".join(item['topics'])
        
        # Display max 2 tags cleanly with overflow badge to avoid vertical stretch
        topics_badges = []
        if item['topics']:
            for t in item['topics'][:2]:
                topics_badges.append(f'<span class="woom-tag-pill">{t}</span>')
            if len(item['topics']) > 2:
                topics_badges.append(f'<span class="woom-tag-pill overflow">+{len(item["topics"]) - 2} more</span>')
        topics_line = f'<div class="woom-tags-wrapper">{"".join(topics_badges)}</div>' if topics_badges else ""
        
        search_text = f"{item['display_title']} {' '.join(item['topics'])} {item['clean_notes']}".lower().replace('"', '&quot;')
        
        cards_woom += f'''
        <a href="woom/{item['slug']}.html" class="woom-card-styled" data-topics="{data_topics}" data-search="{search_text}">
            <div class="woom-card-header">
                {date_meta}
                <h3 class="woom-card-title">{item['display_title']}</h3>
            </div>
            {topics_line}
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
            <img src="logo.png" alt="Out The Trunk Logo" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid #00788C;" onerror="this.style.display='none'">
            <span class="brand-text">Out The Trunk</span>
        </a>
        <input type="checkbox" id="menu-toggle" class="menu-toggle-checkbox" aria-label="Toggle Navigation Menu">
        <label for="menu-toggle" class="nav-toggle-btn">MENU</label>
        <nav id="site-nav" class="site-nav">
            <a href="/#woom">WOOM</a>
            <a href="woom-archive.html" class="active-nav">WOOM Archive</a>
            <a href="/#movies">Movies</a>
            <a href="movies-archive.html">Movie Archive</a>
            <a href="/#listen" class="listen-link">Listen</a>
        </nav>
    </header>

    <main class="container">
        <div style="margin-bottom: 1.5rem;">
            <a href="/" class="nav-breadcrumb">← Home</a>
        </div>

        <header class="archive-header-card">
            <p class="subpage-eyebrow">WHAT'S ON OUR MIND</p>
            <h1 class="archive-main-title">WOOM Archive</h1>
            <p class="archive-subtitle">Cultural analysis, personal finance, friendships, sports debates, and lifestyle questions unfiltered.</p>
        </header>

        <div class="search-container" style="max-width: 750px; margin: 0 auto 1.5rem auto;">
            <input type="text" id="archive-search" class="search-input" placeholder="Search topics, questions, debates, or keywords..." oninput="filterArchive()">
            <div style="text-align: center; margin-top: 0.5rem;">
                <button id="clear-btn" class="clear-filters-btn" style="display: none;" onclick="clearFilters()">Clear Filters & Search</button>
            </div>
        </div>

        <div id="results-banner" class="results-counter-banner">Showing {total_episodes} Episodes</div>

        <div class="filter-pills-container">
            <h3 class="filter-label">Filter by Topic</h3>
            <div class="filter-scroll-row">
                {"".join(topic_chips)}
            </div>
        </div>

        <div class="woom-grid" id="woom-grid">
            {cards_woom}
            <div id="no-results" class="no-results-box" style="display: none;">
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

print("Build complete! All archives and subpages generated with updated UI hierarchy.")