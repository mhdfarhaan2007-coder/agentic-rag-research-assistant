import re

from document_loader import load_pdf


def clean_text(text: str) -> str:
    # Normalize Windows line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove trailing spaces from each line
    text = "\n".join(line.rstrip() for line in text.split("\n"))

    # Replace multiple spaces/tabs with one space
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


if __name__ == "__main__":
    raw_text = load_pdf("documents/test.pdf")
    cleaned_text = clean_text(raw_text)

    print("=" * 60)
    print("SAFE TEXT CLEANING")
    print("=" * 60)

    print("Raw characters:", len(raw_text))
    print("Cleaned characters:", len(cleaned_text))

    print("\nFIRST 3000 CHARACTERS:")
    print(cleaned_text[:3000])