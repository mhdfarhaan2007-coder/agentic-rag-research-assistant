from ollama import embeddings

from document_loader import load_pdf
from text_cleaner import clean_text
from chunker import split_text


def create_embedding(text: str):
    response = embeddings(
        model="nomic-embed-text",
        prompt=text,
    )

    return response["embedding"]


def embed_chunks(chunks):
    embedded_chunks = []

    for i, chunk in enumerate(chunks):

        vector = create_embedding(chunk)

        embedded_chunks.append({
            "chunk_id": i,
            "text": chunk,
            "embedding": vector,
        })

    return embedded_chunks


if __name__ == "__main__":

    raw_text = load_pdf("documents/test.pdf")

    cleaned_text = clean_text(raw_text)

    chunks = split_text(cleaned_text)

    print("=" * 60)
    print("DOCUMENT EMBEDDING")
    print("=" * 60)

    print("Total chunks:", len(chunks))

    embedded_chunks = embed_chunks(chunks)

    print("Total embeddings:", len(embedded_chunks))

    print("Embedding dimensions:",
          len(embedded_chunks[0]["embedding"]))

    print("\nFirst chunk ID:", embedded_chunks[0]["chunk_id"])

    print("\nFirst chunk preview:")
    print(embedded_chunks[0]["text"][:300])

    print("\nFirst 5 embedding values:")
    print(embedded_chunks[0]["embedding"][:5])