import { useEffect, useState } from "react";

import "./index.css";


const API_URL = "http://127.0.0.1:8000";


function App() {

    const [documents, setDocuments] = useState([]);

    const [question, setQuestion] = useState("");

    const [messages, setMessages] = useState([]);

    const [loading, setLoading] = useState(false);

    const [uploading, setUploading] = useState(false);

    const [error, setError] = useState("");


    // ========================================================
    // LOAD DOCUMENTS
    // ========================================================

    async function loadDocuments() {

        try {

            const response = await fetch(
                `${API_URL}/documents`
            );

            if (!response.ok) {
                throw new Error(
                    "Failed to load documents."
                );
            }

            const data = await response.json();

            setDocuments(
                data.documents || []
            );

        } catch (err) {

            setError(
                err.message
            );
        }
    }


    // ========================================================
    // INITIAL LOAD
    // ========================================================

    useEffect(() => {

        loadDocuments();

    }, []);


    // ========================================================
    // UPLOAD
    // ========================================================

    async function handleUpload(event) {

        const file = event.target.files?.[0];

        if (!file) {
            return;
        }

        setError("");

        setUploading(true);

        const formData = new FormData();

        formData.append(
            "file",
            file
        );

        try {

            const response = await fetch(
                `${API_URL}/documents/upload`,
                {
                    method: "POST",
                    body: formData,
                }
            );

            const data = await response.json();

            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Document upload failed."
                );
            }

            await loadDocuments();

        } catch (err) {

            setError(
                err.message
            );

        } finally {

            setUploading(false);

            event.target.value = "";
        }
    }


    // ========================================================
    // DELETE DOCUMENT
    // ========================================================

    async function handleDelete(
        documentId
    ) {

        setError("");

        try {

            const response = await fetch(
                `${API_URL}/documents/${documentId}`,
                {
                    method: "DELETE",
                }
            );

            const data = await response.json();

            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Failed to delete document."
                );
            }

            await loadDocuments();

        } catch (err) {

            setError(
                err.message
            );
        }
    }


    // ========================================================
    // CHAT
    // ========================================================

    async function handleSubmit(
        event
    ) {

        event.preventDefault();

        const trimmedQuestion =
            question.trim();

        if (
            !trimmedQuestion ||
            loading
        ) {
            return;
        }

        setError("");

        setMessages(
            previous => [
                ...previous,
                {
                    type: "user",
                    content: trimmedQuestion,
                },
            ]
        );

        setQuestion("");

        setLoading(true);

        try {

            const response = await fetch(
                `${API_URL}/chat`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",
                    },

                    body: JSON.stringify({
                        question:
                            trimmedQuestion,
                    }),
                }
            );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Chat request failed."
                );
            }

            setMessages(
                previous => [
                    ...previous,
                    {
                        type: "assistant",
                        content:
                            data.answer,

                        data,
                    },
                ]
            );

        } catch (err) {

            setError(
                err.message
            );

        } finally {

            setLoading(false);
        }
    }


    // ========================================================
    // RENDER
    // ========================================================

    return (

        <div className="app">

            {/* =================================================
                SIDEBAR
            ================================================= */}

            <aside className="sidebar">

                <div className="brand">

                    <div className="brand-mark">
                        R
                    </div>

                    <div>

                        <h1>
                            Agentic RAG
                        </h1>

                        <p>
                            Research Assistant
                        </p>

                    </div>

                </div>


                <div className="sidebar-section">

                    <div className="section-header">

                        <h2>
                            Documents
                        </h2>

                        <label
                            className={
                                "upload-button " +
                                (
                                    uploading
                                        ? "disabled"
                                        : ""
                                )
                            }
                        >

                            {uploading
                                ? "Uploading..."
                                : "+ Add PDF"
                            }

                            <input
                                type="file"
                                accept=".pdf"
                                onChange={
                                    handleUpload
                                }
                                disabled={
                                    uploading
                                }
                                hidden
                            />

                        </label>

                    </div>


                    <div className="document-list">

                        {documents.length === 0 ? (

                            <div className="empty-documents">

                                <p>
                                    No documents
                                </p>

                                <span>
                                    Upload a PDF to
                                    begin.
                                </span>

                            </div>

                        ) : (

                            documents.map(
                                document => (

                                    <div
                                        className="document-item"
                                        key={
                                            document.document_id
                                        }
                                    >

                                        <div className="document-icon">
                                            PDF
                                        </div>

                                        <div className="document-info">

                                            <div
                                                className="document-name"
                                                title={
                                                    document.document_name
                                                }
                                            >
                                                {
                                                    document.document_name
                                                }
                                            </div>

                                            <div className="document-meta">

                                                {
                                                    document.chunks
                                                }{" "}
                                                chunks

                                            </div>

                                        </div>

                                        <button
                                            className="delete-button"
                                            onClick={() =>
                                                handleDelete(
                                                    document.document_id
                                                )
                                            }
                                            title="Delete document"
                                        >
                                            ×
                                        </button>

                                    </div>

                                )
                            )

                        )}

                    </div>

                </div>


                <div className="sidebar-footer">

                    <div className="status-dot"></div>

                    <span>
                        Local RAG system
                    </span>

                </div>

            </aside>


            {/* =================================================
                MAIN
            ================================================= */}

            <main className="main">

                <header className="topbar">

                    <div>

                        <h2>
                            Research Assistant
                        </h2>

                        <p>
                            Ask questions about
                            your documents
                        </p>

                    </div>

                    <div className="system-status">

                        <span className="status-dot"></span>

                        System online

                    </div>

                </header>


                {/* =================================================
                    CHAT AREA
                ================================================= */}

                <section className="chat-area">

                    {messages.length === 0 ? (

                        <div className="welcome">

                            <div className="welcome-icon">
                                R
                            </div>

                            <h2>
                                Ask your research
                                question
                            </h2>

                            <p>
                                Upload research
                                documents and ask
                                questions. The system
                                retrieves evidence,
                                reranks it, generates
                                an answer, and verifies
                                the claims.
                            </p>

                            <div className="example-grid">

                                <button
                                    onClick={() =>
                                        setQuestion(
                                            "What is deep learning?"
                                        )
                                    }
                                >
                                    What is deep
                                    learning?
                                </button>

                                <button
                                    onClick={() =>
                                        setQuestion(
                                            "Who introduced reinforcement learning?"
                                        )
                                    }
                                >
                                    Who introduced
                                    reinforcement
                                    learning?
                                </button>

                                <button
                                    onClick={() =>
                                        setQuestion(
                                            "What are the current research areas in AI?"
                                        )
                                    }
                                >
                                    What are the current
                                    research areas in AI?
                                </button>

                            </div>

                        </div>

                    ) : (

                        <div className="messages">

                            {messages.map(
                                (message, index) => (

                                    <div
                                        className={
                                            `message-row ${message.type}`
                                        }
                                        key={index}
                                    >

                                        <div className="message">

                                            <div className="message-label">

                                                {message.type === "user"
                                                    ? "You"
                                                    : "AI"
                                                }

                                            </div>

                                            <div className="message-content">

                                                {
                                                    message.content
                                                }

                                            </div>


                                            {/* =================================
                                                AI METADATA
                                            ================================= */}

                                            {message.type ===
                                                "assistant" &&
                                                message.data && (

                                                    <div className="answer-details">

                                                        <div className="metadata-row">

                                                            <span>
                                                                Agent:
                                                            </span>

                                                            <strong>
                                                                {
                                                                    message.data.agent_decision
                                                                }
                                                            </strong>

                                                            <span>
                                                                Verification:
                                                            </span>

                                                            <strong>
                                                                {
                                                                    message.data.verification ||
                                                                    "N/A"
                                                                }
                                                            </strong>

                                                            <span>
                                                                Retries:
                                                            </span>

                                                            <strong>
                                                                {
                                                                    message.data.retry_count
                                                                }
                                                            </strong>

                                                        </div>


                                                        {/* SOURCES */}

                                                        {message.data.sources?.length >
                                                            0 && (

                                                            <details>

                                                                <summary>
                                                                    Sources and
                                                                    retrieved
                                                                    evidence
                                                                </summary>

                                                                <div className="sources">

                                                                    {message.data.sources.map(
                                                                        (
                                                                            source,
                                                                            sourceIndex
                                                                        ) => (

                                                                            <div
                                                                                className="source-card"
                                                                                key={
                                                                                    sourceIndex
                                                                                }
                                                                            >

                                                                                <div className="source-header">

                                                                                    <strong>
                                                                                        {
                                                                                            source.document_name
                                                                                        }
                                                                                    </strong>

                                                                                    <span>
                                                                                        Chunk{" "}
                                                                                        {
                                                                                            source.chunk_id
                                                                                        }
                                                                                    </span>

                                                                                </div>

                                                                                <div className="source-scores">

                                                                                    Similarity:{" "}
                                                                                    {
                                                                                        Number(
                                                                                            source.similarity
                                                                                        ).toFixed(
                                                                                            4
                                                                                        )
                                                                                    }

                                                                                    {" • "}

                                                                                    Rerank:{" "}
                                                                                    {
                                                                                        Number(
                                                                                            source.rerank_score
                                                                                        ).toFixed(
                                                                                            1
                                                                                        )
                                                                                    }

                                                                                </div>

                                                                                <p>
                                                                                    {
                                                                                        source.text
                                                                                    }
                                                                                </p>

                                                                            </div>

                                                                        )
                                                                    )}

                                                                </div>

                                                            </details>

                                                        )}


                                                        {/* CLAIM VERIFICATION */}

                                                        {message.data.claims?.length >
                                                            0 && (

                                                            <details>

                                                                <summary>
                                                                    Claim
                                                                    verification
                                                                </summary>

                                                                <div className="claims">

                                                                    {message.data.claims.map(
                                                                        (
                                                                            claim,
                                                                            claimIndex
                                                                        ) => (

                                                                            <div
                                                                                className="claim-card"
                                                                                key={
                                                                                    claimIndex
                                                                                }
                                                                            >

                                                                                <div className="claim-status">

                                                                                    <span
                                                                                        className={
                                                                                            claim.verification ===
                                                                                            "SUPPORTED"
                                                                                                ? "supported"
                                                                                                : "unsupported"
                                                                                        }
                                                                                    >
                                                                                        {
                                                                                            claim.verification
                                                                                        }
                                                                                    </span>

                                                                                </div>

                                                                                <p>
                                                                                    {
                                                                                        claim.claim
                                                                                    }
                                                                                </p>

                                                                                {claim.supporting_evidence?.length >
                                                                                    0 && (

                                                                                    <div className="claim-evidence">

                                                                                        Supported by:

                                                                                        {claim.supporting_evidence.map(
                                                                                            (
                                                                                                evidence,
                                                                                                evidenceIndex
                                                                                            ) => (

                                                                                                <span
                                                                                                    key={
                                                                                                        evidenceIndex
                                                                                                    }
                                                                                                >
                                                                                                    {
                                                                                                        evidence.document_name
                                                                                                    }{" "}
                                                                                                    /
                                                                                                    Chunk{" "}
                                                                                                    {
                                                                                                        evidence.chunk_id
                                                                                                    }
                                                                                                </span>

                                                                                            )
                                                                                        )}

                                                                                    </div>

                                                                                )}

                                                                            </div>

                                                                        )
                                                                    )}

                                                                </div>

                                                            </details>

                                                        )}

                                                    </div>

                                                )}

                                        </div>

                                    </div>

                                )
                            )}

                            {loading && (

                                <div className="message-row assistant">

                                    <div className="message">

                                        <div className="message-label">
                                            AI
                                        </div>

                                        <div className="loading-state">

                                            <span></span>
                                            <span></span>
                                            <span></span>

                                            <div>
                                                Running Agentic RAG...
                                            </div>

                                        </div>

                                    </div>

                                </div>

                            )}

                        </div>

                    )}

                </section>


                {/* =================================================
                    ERROR
                ================================================= */}

                {error && (

                    <div className="error">

                        {error}

                    </div>

                )}


                {/* =================================================
                    INPUT
                ================================================= */}

                <form
                    className="chat-input-container"
                    onSubmit={handleSubmit}
                >

                    <div className="chat-input-wrapper">

                        <textarea
                            value={question}
                            onChange={event =>
                                setQuestion(
                                    event.target.value
                                )
                            }
                            placeholder={
                                "Ask a question about your documents..."
                            }
                            rows={1}
                            disabled={loading}
                            onKeyDown={event => {

                                if (
                                    event.key === "Enter" &&
                                    !event.shiftKey
                                ) {

                                    event.preventDefault();

                                    handleSubmit(event);
                                }

                            }}
                        />

                        <button
                            type="submit"
                            disabled={
                                loading ||
                                !question.trim()
                            }
                        >
                            {loading
                                ? "..."
                                : "Send"
                            }
                        </button>

                    </div>

                    <div className="input-hint">

                        Press Enter to send •
                        Shift + Enter for a new line

                    </div>

                </form>

            </main>

        </div>
    );
}


export default App;