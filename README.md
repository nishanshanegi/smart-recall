# 🧠 Smart-Recall: Intelligent Personal Knowledge Vault

A scalable, asynchronous RAG (Retrieval-Augmented Generation) backend that transforms messy personal data (Text, Images, PDFs) into a searchable AI-powered knowledge base.

## 🚀 Key Technical Features
- **Multimodal Ingestion:** Automated text extraction from images via **Tesseract OCR** and documents via **PyPDF**.
- **Asynchronous Architecture:** Event-driven processing using **AWS SQS** to decouple ingestion from heavy AI computation.
- **Hybrid Semantic Search:** Combines **pgvector** (Cosine Similarity) with traditional keyword matching (ILike) for 100% accuracy.
- **RAG Pipeline:** Context-aware answering using **Llama 3 (Groq)** and **Sentence-Transformers**.
- **Observability:** Custom Middleware for **Latency & Performance Tracking**.
- **Security:** State-of-the-art **JWT Authentication** with Bcrypt password hashing.

## 🛠️ Tech Stack
- **Language:** Python 3.12+
- **Framework:** FastAPI
- **Database:** PostgreSQL + pgvector
- **Message Queue:** AWS SQS (Mocked via LocalStack)
- **Object Storage:** AWS S3 (Mocked via LocalStack)
- **ORM:** SQLAlchemy 2.0
- **AI Models:** all-MiniLM-L6-v2 (Local) & Llama-3 (Cloud)

## 🏗️ Architecture Flow
1. **API Ingests** raw data/files and persists metadata to Postgres.
2. **Binary files** are uploaded to S3.
3. **SQS Task** is triggered for background processing.
4. **Worker** extracts text (OCR/PDF) and generates **384-dim Embeddings**.
5. **Vector Search** identifies relevant chunks in the database.
6. **LLM** synthesizes a natural language answer based on retrieved context.

## 🔧 Installation & Setup
1. **Clone the repo:** `git clone ...`
2. **Docker:** `docker-compose up -d`
3. **Setup Infra:** `python infra_setup.py`
4. **Run API:** `uvicorn app.main:app --reload`
5. **Run Worker:** `python -m app.worker.process`