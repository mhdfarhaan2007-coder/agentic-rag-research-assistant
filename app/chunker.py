from document_loader import load_pdf
from text_cleaner import clean_text


def split_text(text, chunk_size=800, chunk_overlap=120):
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks = []
    start = 0

    while start < len(text):

        end = min(start + chunk_size, len(text))

        if end < len(text):

            boundaries = [
                text.rfind("\n\n", start, end),
                text.rfind("\n", start, end),
                text.rfind(". ", start, end),
                text.rfind(" ", start, end),
            ]

            boundary = max(boundaries)

            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        next_start = end - chunk_overlap

        # Avoid starting in the middle of a word
        while (
            next_start < end
            and next_start < len(text)
            and not text[next_start].isspace()
        ):
            next_start += 1

        # Safety: always move forward
        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


if __name__ == "__main__":

    raw_text = load_pdf("documents/test.pdf")

    cleaned_text = clean_text(raw_text)

    chunks = split_text(cleaned_text)

    print("=" * 60)
    print("CHUNKING RESULT")
    print("=" * 60)

    print("Raw characters:", len(raw_text))
    print("Cleaned characters:", len(cleaned_text))
    print("Total chunks:", len(chunks))

    for i, chunk in enumerate(chunks[:5]):

        print("\n" + "-" * 60)
        print(f"CHUNK {i + 1}")
        print("-" * 60)

        print(chunk)

        print(f"\nCharacters: {len(chunk)}")