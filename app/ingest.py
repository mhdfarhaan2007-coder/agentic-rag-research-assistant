from pathlib import Path

from document_loader import load_pdf
from text_cleaner import clean_text
from chunker import split_text
from embeddings import embed_chunks
from vector_store import add_embeddings


def ingest_document(file_path):

    path = Path(file_path)

    if not path.exists():

        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    document_name = path.name

    # Create a simple document ID.
    document_id = (
        path.stem
        .lower()
        .replace(" ", "_")
    )

    print("[1] Loading document...")

    raw_text = load_pdf(
        file_path
    )

    print("[2] Cleaning text...")

    cleaned_text = clean_text(
        raw_text
    )

    print("[3] Creating chunks...")

    chunks = split_text(
        cleaned_text
    )

    print(
        f"    Created {len(chunks)} chunks."
    )

    if not chunks:

        raise ValueError(
            "No usable text was extracted "
            "from the document."
        )

    print("[4] Creating embeddings...")

    embedded_chunks = embed_chunks(
        chunks
    )

    print(
        f"    Created {len(embedded_chunks)} embeddings."
    )

    # Add document metadata to every chunk.
    for chunk in embedded_chunks:

        chunk["document_id"] = document_id

        chunk["document_name"] = document_name

    print(
        "[5] Adding to vector store..."
    )

    add_embeddings(
        embedded_chunks
    )

    print("[6] Ingestion complete.")

    print(
        f"    Document: {document_name}"
    )

    print(
        f"    Document ID: {document_id}"
    )

    return {
        "document_id": document_id,
        "document_name": document_name,
        "chunks": len(embedded_chunks)
    }


if __name__ == "__main__":

    ingest_document(
        "documents/test.pdf"
    )