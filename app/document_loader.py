from pathlib import Path
from pypdf import PdfReader


def load_pdf(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


if __name__ == "__main__":
    pdf_path = "documents/test.pdf"

    text = load_pdf(pdf_path)

    print("=" * 60)
    print("PDF LOADED SUCCESSFULLY")
    print("=" * 60)

    print(f"Characters extracted: {len(text)}")

    print("\nFIRST 2000 CHARACTERS:")
    print(text[:2000])