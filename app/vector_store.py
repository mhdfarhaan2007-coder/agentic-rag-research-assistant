import json
from pathlib import Path


VECTORSTORE_PATH = Path(
    "vectorstore/document_vectors.json"
)


# ============================================================
# SAVE
# ============================================================

def save_embeddings(embedded_chunks):
    VECTORSTORE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        VECTORSTORE_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            embedded_chunks,
            file,
            ensure_ascii=False
        )


# ============================================================
# LOAD
# ============================================================

def load_embeddings():

    if not VECTORSTORE_PATH.exists():

        raise FileNotFoundError(
            "Vector store does not exist. "
            "Run document ingestion first."
        )

    with open(
        VECTORSTORE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# ADD EMBEDDINGS
# ============================================================

def add_embeddings(new_embeddings):

    if VECTORSTORE_PATH.exists():

        existing_embeddings = load_embeddings()

    else:

        existing_embeddings = []

    existing_embeddings.extend(
        new_embeddings
    )

    save_embeddings(
        existing_embeddings
    )


# ============================================================
# DELETE DOCUMENT
# ============================================================

def delete_document_embeddings(
    document_id: str
):
    """
    Remove every vector belonging to one document.
    """

    if not VECTORSTORE_PATH.exists():

        return {
            "deleted": False,
            "removed_chunks": 0
        }

    existing_embeddings = load_embeddings()

    remaining_embeddings = []

    removed_chunks = 0

    for chunk in existing_embeddings:

        if chunk.get("document_id") == document_id:

            removed_chunks += 1

        else:

            remaining_embeddings.append(
                chunk
            )

    save_embeddings(
        remaining_embeddings
    )

    return {
        "deleted": removed_chunks > 0,
        "removed_chunks": removed_chunks
    }


# ============================================================
# GET DOCUMENTS
# ============================================================

def get_indexed_documents():

    if not VECTORSTORE_PATH.exists():

        return []

    embeddings = load_embeddings()

    documents = {}

    for chunk in embeddings:

        document_id = chunk.get(
            "document_id"
        )

        document_name = chunk.get(
            "document_name"
        )

        if not document_id:
            continue

        if document_id not in documents:

            documents[document_id] = {
                "document_id": document_id,
                "document_name": document_name,
                "chunks": 0
            }

        documents[document_id]["chunks"] += 1

    return list(
        documents.values()
    )