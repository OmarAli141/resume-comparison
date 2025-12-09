import pdfplumber  # library to read PDF content (text, tables, layout)
from pathlib import Path  # object-oriented filesystem paths
from typing import List, Dict  # type hints for function arguments and return values

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extracts text from a PDF file.
    Args:
        pdf_path: Path to the PDF file
    Returns:
        Text from the PDF file
    """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting {pdf_path.name}: {e}")
    return text.strip()


def extract_texts_from_directory(directory: Path) -> List[Dict]:
    """
    Extracts text from all PDF files in a directory.
    Args:
        directory: Path to the directory containing the PDF files
    Returns:
        List of dictionaries containing the file name, path, and text
    """
    results = []
    for pdf_file in directory.rglob("*.pdf"):
        print(f"Extracting: {pdf_file.name}")
        text = extract_text_from_pdf(pdf_file)
        results.append({
            "file_name": pdf_file.name,
            "file_path": str(pdf_file),
            "text": text
        })
    return results