# Agentic RAG Research Assistant

An AI-powered research assistant that uses Retrieval-Augmented Generation (RAG) and agentic workflows to answer questions from research documents, retrieve relevant information, and verify generated claims against source content.

## Overview

Traditional RAG systems retrieve relevant document chunks and use them to generate answers. However, retrieval alone does not guarantee that every generated claim is accurate.

This project explores an agentic approach to improve the research and verification process.

It combines document processing, semantic retrieval, reranking, query rewriting, answer generation, and claim verification into a modular pipeline.

**Project Status:** Built and tested locally. Under development.

## Key Features

- **Document Processing:** Load and process research documents, including PDF files.
- **Text Chunking:** Divide documents into smaller chunks for efficient retrieval.
- **Semantic Search:** Generate embeddings and retrieve relevant document content.
- **Vector Database:** Store and search document embeddings using ChromaDB.
- **Query Rewriting:** Improve user queries to support more effective retrieval.
- **Reranking:** Reorder retrieved results based on relevance.
- **Answer Generation:** Generate responses using Large Language Models.
- **Claim Extraction:** Extract individual claims from generated responses.
- **Claim Verification:** Check extracted claims against retrieved source content.
- **Agent Controller:** Coordinate different components of the research workflow.

## System Architecture

The project follows a modular architecture:

```text
                 User Query
                     |
                     v
              Agent Controller
                     |
                     v
                Query Rewriter
                     |
                     v
                 Retriever
                     |
                     v
                  Reranker
                     |
                     v
             Relevant Documents
                     |
                     v
              Answer Generator
                     |
                     v
               Claim Extractor
                     |
                     v
              Claim Verifier
                     |
                     v
               Final Response
```

### Document Ingestion Pipeline

```text
Research Documents (PDF)
          |
          v
    Document Loader
          |
          v
      Text Cleaner
          |
          v
       Chunker
          |
          v
    Embedding Model
          |
          v
       ChromaDB
```

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Frontend | React, Vite, JavaScript |
| Backend | FastAPI |
| LLM Integration | Ollama, LangChain |
| Embedding Model | Nomic Embed Text |
| Vector Database | ChromaDB |
| Document Processing | PDF processing tools |
| Version Control | Git, GitHub |

## Project Structure

```text
Agentic-RAG-Research-Assistant/
│
├── app/
│   ├── api/
│   │   └── main.py
│   ├── agent_controller.py
│   ├── chunker.py
│   ├── claim_extractor.py
│   ├── claim_verifier.py
│   ├── document_loader.py
│   ├── embeddings.py
│   ├── generator.py
│   ├── ingest.py
│   ├── llm.py
│   ├── query_rewriter.py
│   ├── rag_pipeline.py
│   ├── reranker.py
│   ├── retriever.py
│   ├── router.py
│   ├── text_cleaner.py
│   ├── vector_store.py
│   └── verifier.py
│
├── documents/
│   └── Research Documents
│
├── frontend/
│   └── React Application
│
├── benchmark.py
├── check_models.py
├── requirements.txt
├── test_llm.py
└── README.md
```

## Installation and Setup

### Prerequisites

- Python 3.12
- Node.js and npm
- Git
- Ollama
- Required Ollama models

### 1. Clone the repository

```bash
git clone https://github.com/mhdfarhaan2007-coder/agentic-rag-research-assistant.git

cd agentic-rag-research-assistant
```

### 2. Create a Python virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Ollama

Install Ollama and download the models required by your configuration.

Example:

```bash
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

Make sure Ollama is running before starting the application.

### 5. Configure environment variables

Create a `.env` file in the project root if your configuration requires API keys.

Never upload your actual `.env` file or expose API keys in the repository.

### 6. Install frontend dependencies

```bash
cd frontend
npm install
```

Start the frontend using:

```bash
npm run dev
```

### 7. Start the backend

From the project root, use the FastAPI application entry point:

```bash
uvicorn app.api.main:app --reload
```

Check your backend configuration and required environment variables before running it.

## Project Goals

The main objective is to explore how agentic workflows can improve the reliability of traditional RAG applications.

The project focuses on:

1. Improving document retrieval.
2. Enhancing the relevance of retrieved information.
3. Breaking generated answers into verifiable claims.
4. Checking claims against supporting source content.
5. Organizing the workflow into independent, reusable modules.

## Future Improvements

- Improve retrieval accuracy and evaluation.
- Add more robust hallucination detection.
- Improve source attribution and evidence presentation.
- Add automated evaluation metrics.
- Implement detailed agent execution tracing.
- Improve error handling and production deployment.

## Learning Outcomes

Through this project, I explored:

- Retrieval-Augmented Generation (RAG).
- Embedding models and semantic search.
- Vector databases.
- LLM application development.
- Agentic workflow design.
- Retrieval reranking.
- Claim extraction and verification.
- Building AI applications with Python and React.

## Author

**Mohammed Farhaan M**

B.Sc. Computer Science with Artificial Intelligence

GitHub: [mhdfarhaan2007-coder](https://github.com/mhdfarhaan2007-coder)

---

*This is an academic and portfolio project focused on exploring reliable AI-powered research systems.*
