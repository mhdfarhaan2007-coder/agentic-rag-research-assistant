import sys
from pathlib import Path


# ============================================================
# PATH SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

APP_DIR = PROJECT_ROOT / "app"

DOCUMENTS_DIR = PROJECT_ROOT / "documents"


if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# ============================================================
# IMPORTS
# ============================================================

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from ingest import ingest_document

from vector_store import (
    get_indexed_documents,
    delete_document_embeddings,
)

from rag_pipeline import run_agentic_rag


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Agentic RAG Research Assistant",
    description=(
        "Agentic RAG system with adaptive retrieval, "
        "reranking, generation, verification, "
        "and agent control."
    ),
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    question: str


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "name": "Agentic RAG Research Assistant",
        "status": "running",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
    }


# ============================================================
# LIST DOCUMENTS
# ============================================================

@app.get("/documents")
def list_documents():

    return {
        "documents": get_indexed_documents(),
    }


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    # --------------------------------------------------------
    # Validate extension
    # --------------------------------------------------------

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    # --------------------------------------------------------
    # Create documents directory
    # --------------------------------------------------------

    DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = Path(
        file.filename
    ).name

    file_path = (
        DOCUMENTS_DIR /
        safe_filename
    )

    # --------------------------------------------------------
    # Prevent duplicate filename
    # --------------------------------------------------------

    if file_path.exists():

        raise HTTPException(
            status_code=409,
            detail=(
                "A document with this filename "
                "already exists."
            ),
        )

    # --------------------------------------------------------
    # Save PDF
    # --------------------------------------------------------

    try:

        contents = await file.read()

        if not contents:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        with open(
            file_path,
            "wb",
        ) as output_file:

            output_file.write(contents)

    except HTTPException:
        raise

    except Exception as exc:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save document: {exc}"
            ),
        )

    # --------------------------------------------------------
    # Ingest PDF
    # --------------------------------------------------------

    try:

        result = ingest_document(
            str(file_path)
        )

    except Exception as exc:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Document ingestion failed: {exc}"
            ),
        )

    return {
        "success": True,
        "message": "Document uploaded successfully.",
        **result,
    }


# ============================================================
# DELETE DOCUMENT
# ============================================================

@app.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
):

    documents = get_indexed_documents()

    document = next(
        (
            item
            for item in documents
            if item["document_id"] == document_id
        ),
        None,
    )

    if document is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    # --------------------------------------------------------
    # Delete vectors
    # --------------------------------------------------------

    vector_result = delete_document_embeddings(
        document_id
    )

    # --------------------------------------------------------
    # Delete physical PDF
    # --------------------------------------------------------

    document_name = document[
        "document_name"
    ]

    file_path = (
        DOCUMENTS_DIR /
        document_name
    )

    if file_path.exists():
        file_path.unlink()

    return {
        "success": True,
        "message": "Document deleted successfully.",
        "document_id": document_id,
        "document_name": document_name,
        "removed_chunks": (
            vector_result["removed_chunks"]
        ),
    }


# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:

        result = run_agentic_rag(
            question
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"RAG pipeline failed: {exc}"
            ),
        )

    # ========================================================
    # CLEAN SOURCES
    # ========================================================

    sources = []

    for chunk in result.get(
        "reranked_chunks",
        [],
    ):

        sources.append(
            {
                "document_id": chunk.get(
                    "document_id"
                ),

                "document_name": chunk.get(
                    "document_name"
                ),

                "chunk_id": chunk.get(
                    "chunk_id"
                ),

                "similarity": chunk.get(
                    "score",
                    0,
                ),

                "rerank_score": chunk.get(
                    "rerank_score",
                    0,
                ),

                "text": chunk.get(
                    "text",
                    "",
                ),
            }
        )

    # ========================================================
    # CLAIM VERIFICATION
    # ========================================================

    verification = result.get(
        "verification"
    )

    claims = []

    if verification:

        for item in verification.get(
            "claims",
            [],
        ):

            evidence = []

            for source in item.get(
                "supporting_evidence",
                [],
            ):

                evidence.append(
                    {
                        "document_name": source.get(
                            "document_name"
                        ),

                        "chunk_id": source.get(
                            "chunk_id"
                        ),
                    }
                )

            claims.append(
                {
                    "claim": item.get(
                        "claim"
                    ),

                    "verification": item.get(
                        "verification"
                    ),

                    "supporting_evidence": evidence,
                }
            )

    # ========================================================
    # FINAL API RESPONSE
    # ========================================================

    return {
        "success": True,

        "question": question,

        "answer": result.get(
            "answer",
            "NOT ENOUGH EVIDENCE",
        ),

        "router_decision": result.get(
            "decision"
        ),

        "agent_decision": result.get(
            "agent_decision"
        ),

        "retry_count": result.get(
            "retry_count",
            0,
        ),

        "verification": (
            verification.get(
                "overall_verification"
            )
            if verification
            else None
        ),

        "claims": claims,

        "sources": sources,
    }