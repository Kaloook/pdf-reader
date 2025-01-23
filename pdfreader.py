import os
import sys
from PyPDF2 import PdfReader
import re  # For sanitizing filenames
import shutil  # For moving files

def extract_title(pdf_path):
    """Extract the title from the first line of the first page of a PDF."""
    try:
        reader = PdfReader(pdf_path)
        if reader.pages:
            text = reader.pages[0].extract_text()
            title = text.splitlines()[0]  # Extract the first line as title
            return title.strip()
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return None

def sanitize_filename(name):
    """Remove invalid characters for file names."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name)

def rename_pdfs(source_dir, renamed_dir):
    """Rename PDFs in the directory based on their titles."""
    # Create renamed directory if it doesn't exist
    os.makedirs(renamed_dir, exist_ok=True)

    for file in os.listdir(source_dir):
        if file.lower().endswith('.pdf'):
            old_path = os.path.join(source_dir, file)
            title = extract_title(old_path)

            if title:
                sanitized_title = sanitize_filename(title)  # Sanitize title
                new_name = f"{sanitized_title}.pdf"
                new_path = os.path.join(source_dir, new_name)
                
                if len(new_path) > 260:
                    print(f"Skipped: {file} (new path too long)")
                    continue
                
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: {file} -> {new_name}")

                    # Move the renamed file to the renamed directory
                    shutil.move(new_path, os.path.join(renamed_dir, new_name))
                    
                except Exception as e:
                    print(f"Error renaming {file}: {e}")
                    print(f"{file} remains in the source directory.")
            else:
                # No title found, skip renaming and leave the file in the original directory
                print(f"Skipped: {file} (no title found)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pdfreader.py <source_directory> <renamed_directory>")
        sys.exit(1)

    source_directory = sys.argv[1]
    renamed_directory = sys.argv[2]

    rename_pdfs(source_directory, renamed_directory)
