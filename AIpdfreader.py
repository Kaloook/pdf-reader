import os
import sys
from PyPDF2 import PdfReader
import re  # For sanitizing filenames
import shutil  # For moving files
import requests  # For interacting with the Ollama API

# Ollama settings
OLLAMA_MODEL = "llama2"  # Change this to your preferred model (e.g., "llama3.1")
OLLAMA_API_URL = "http://localhost:11434/api/chat"  # Ollama's local API endpoint

def extract_text_from_pdf(pdf_path):
    """
    Extract the text from the first page of a PDF.
    """
    try:
        reader = PdfReader(pdf_path)
        if reader.pages:
            text = reader.pages[0].extract_text()
            return text.strip() if text else "No content found in the PDF."
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return "Failed to read the content."

def get_filename_from_ollama(content):
    """
    Query Ollama to generate a sanitized filename based on the content.
    """
    prompt = (
        "You are an assistant tasked with generating file names for documents. "
        "Based on the content provided, return a filename that is concise, descriptive, "
        "and uses only English characters, numbers, and underscores. Ensure it is no longer than 50 characters."
    )

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "system": prompt,
                "messages": [{"role": "user", "content": content}],
            },
        )
        response.raise_for_status()
        filename = response.json()["response"].strip()
        return sanitize_filename(filename)
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return "Untitled"

def sanitize_filename(name):
    """
    Remove invalid characters for file names and limit the length to 50 characters.
    """
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name)  # Replace invalid characters with '_'
    return sanitized[:50]  # Limit filename length to 50 characters

def ensure_unique_filename(directory, filename):
    """
    Ensure the filename is unique in the target directory by appending a counter if needed.
    """
    base_name, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(os.path.join(directory, filename)):
        filename = f"{base_name}_{counter}{ext}"
        counter += 1
    return filename

def rename_pdfs(source_dir, renamed_dir):
    """
    Rename PDFs in the source directory based on AI-generated titles.
    Moved renamed PDFs to the renamed directory.
    """
    # Ensure the renamed directory exists
    os.makedirs(renamed_dir, exist_ok=True)

    for file in os.listdir(source_dir):
        if file.lower().endswith('.pdf'):
            old_path = os.path.join(source_dir, file)
            print(f"Processing: {file}")

            # Extract text from the PDF
            content = extract_text_from_pdf(old_path)
            print(f"Extracted content: {content[:100]}...")  # Log a snippet of the content

            # Get filename from Ollama
            ai_filename = get_filename_from_ollama(content)
            print(f"AI suggested filename: {ai_filename}")

            # Ensure unique filename
            new_name = f"{ai_filename}.pdf"
            new_name = ensure_unique_filename(renamed_dir, new_name)

            # Ensure the total path length is within limits
            new_path = os.path.join(renamed_dir, new_name)
            if len(new_path) > 260:  # Adjust for filesystem limits
                print(f"Skipped: {file} (path too long)")
                continue

            # Rename and move the file
            try:
                shutil.move(old_path, new_path)
                print(f"Renamed and moved: {file} -> {new_name}")
            except Exception as e:
                print(f"Error renaming {file}: {e}")
                print(f"{file} remains in the source directory.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pdf_rename_ollama.py <source_directory> <renamed_directory>")
        sys.exit(1)

    source_directory = sys.argv[1]
    renamed_directory = sys.argv[2]

    # Validate input directories
    if not os.path.isdir(source_directory):
        print(f"Error: Source directory '{source_directory}' does not exist.")
        sys.exit(1)
    if not os.path.isdir(renamed_directory):
        print(f"Error: Renamed directory '{renamed_directory}' does not exist. It will be created.")

    rename_pdfs(source_directory, renamed_directory)
