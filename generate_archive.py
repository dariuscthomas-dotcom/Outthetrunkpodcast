import os
import re
from docx import Document

# Absolute paths for source folders
TRANSCRIPTS_DIR = r"E:\Creative\Podcasts\Transcripts\Movie_Reviews"
SHOW_NOTES_DIR = r"E:\Creative\Podcasts\Show Notes"

# Relative paths inside your E:\Creative\Podcasts\Website folder
OUTPUT_DIR = "movies"
TEMPLATE_FILE = "movie-template.html"

def slugify(text):
    """Converts movie titles into clean URL filenames (e.g., '12_Angry_Men' -> '12-angry-men')."""
    text = text.lower()
    text = re.sub(r'[\'\"]', '', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def read_docx_paragraphs(file_path):
    """Extracts clean text paragraphs from a Word document."""
    if not os.path.exists(file_path):
        return None
    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)

def process_all_movies():
    # Load HTML template
    if not os.path.exists(TEMPLATE_FILE):
        print(f"Error: Could not find '{TEMPLATE_FILE}'. Ensure it sits inside E:\\Creative\\Podcasts\\Website.")
        return

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        html_template = f.read()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(TRANSCRIPTS_DIR):
        print(f"Error: Could not find transcripts folder at '{TRANSCRIPTS_DIR}'.")
        return

    # Get list of transcript files
    transcript_files = [f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith(".docx") and not f.startswith("~$")]

    print(f"Found {len(transcript_files)} transcript files at '{TRANSCRIPTS_DIR}'.")
    print("Generating movie pages...\n")

    for filename in transcript_files:
        # Extract title (e.g., '12_Angry_Men_Transcript.docx' -> '12 Angry Men')
        clean_title = filename.replace("_Transcript.docx", "").replace(".docx", "").replace("_", " ")
        slug = slugify(clean_title)

        transcript_path = os.path.join(TRANSCRIPTS_DIR, filename)
        
        # Match show notes file (e.g., '12_Angry_Men_Notes.docx')
        notes_filename = filename.replace("_Transcript.docx", "_Notes.docx")
        notes_path = os.path.join(SHOW_NOTES_DIR, notes_filename)

        # Read contents
        transcript_text = read_docx_paragraphs(transcript_path) or "Transcript coming soon."
        show_notes_text = read_docx_paragraphs(notes_path) if os.path.exists(notes_path) else "Show notes coming soon."

        # Fill template placeholders
        page_html = html_template
        page_html = page_html.replace("{{MOVIE_TITLE}}", clean_title)
        page_html = page_html.replace("{{MOVIE_YEAR}}", "")
        page_html = page_html.replace("{{TRANSCRIPT_TEXT}}", transcript_text)
        page_html = page_html.replace("{{JORDAN_INSIGHT}}", show_notes_text)
        
        # Default placeholders for future metadata updates
        page_html = page_html.replace("{{AVG_RATING}}", "N/A")
        page_html = page_html.replace("{{JORDAN_RATING}}", "N/A")
        page_html = page_html.replace("{{DARIUS_RATING}}", "N/A")
        page_html = page_html.replace("{{BEST_QUESTION}}", "See episode show notes")
        page_html = page_html.replace("{{DARIUS_INSIGHT}}", "")
        page_html = page_html.replace("{{MAJOR_THEMES}}", "")
        page_html = page_html.replace("{{VERDICT}}", "")
        page_html = page_html.replace("{{YOUTUBE_VIDEO_ID}}", "PLHyesB7Qpe2g")
        page_html = page_html.replace("{{LETTERBOXD_LINK}}", "https://letterboxd.com/")

        # Write output file inside the /movies/ subfolder
        output_filepath = os.path.join(OUTPUT_DIR, f"{slug}.html")
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(page_html)

        print(f"✓ Generated: {output_filepath}")

    print(f"\nSuccess! Created {len(transcript_files)} movie pages in 'E:\\Creative\\Podcasts\\Website\\movies'.")

if __name__ == "__main__":
    process_all_movies()