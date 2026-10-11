# 🇮🇳 Government Welfare Scheme Gap Analysis & Awareness Miner

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016-black.svg?style=flat&logo=next.js)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat&logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end intelligent Natural Language Processing (NLP) and Machine Learning platform designed to identify, mine, and analyze public awareness gaps, misinformation, eligibility confusion, and procedural bottlenecks across Indian Government Welfare Schemes (e.g., **PM-KISAN**, **PMFBY**, **PM-KUSUM**, **PMAY**, **Ayushman Bharat**, etc.).

The system processes citizen inquiries, grievance records, and web data through semantic clustering, intent classification, and geospatial mapping to pinpoint which regions and communities face the steepest information hurdles.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Configure Environment Variables](#2-configure-environment-variables)
  - [3. Backend Setup (Python)](#3-backend-setup-python)
  - [4. Seed the Database](#4-seed-the-database)
  - [5. Frontend Setup (Next.js)](#5-frontend-setup-nextjs)
- [Running the Project](#-running-the-project)
  - [Method 1: One-Command Start (Root Orchestrator)](#method-1-one-command-start-root-orchestrator)
  - [Method 2: Multi-Terminal Start (Recommended for Debugging)](#method-2-multi-terminal-start-recommended-for-debugging)
  - [Method 3: Running with Docker (PostgreSQL)](#method-3-running-with-docker-postgresql)
- [API Documentation](#-api-documentation)
- [Troubleshooting & FAQs](#-troubleshooting--faqs)

---

## 🌟 Key Features

1. **Semantic Awareness Gap Mining**:
   - Generates 384-dimensional dense sentence embeddings using HuggingFace's `all-MiniLM-L6-v2`.
   - Discovers latent grievance topics and awareness blind spots via unsupervised **HDBSCAN** clustering.
   - Detects scheme associations, citizen intent (inquiry, complaint, eligibility check), and specific gap types (documentation, disbursement delay, middleman issues, portal errors).

2. **Interactive Geospatial Intelligence**:
   - Full interactive choropleth maps of India at both **State** and **District** levels powered by Leaflet & GeoJSON.
   - Highlights high-friction zones and underserved geographic clusters.

3. **Automated Multi-Source Collection Engine**:
   - Configurable web scrapers and RSS feed ingestion pipelines for civic portals, news feeds, and official grievance feeds.
   - Background asynchronous worker daemon (`worker.py`) that handles scheduled crawls, discovery queues, and URL processing.

4. **Modern Executive Dashboard**:
   - Built on **Next.js 16 (App Router)**, **React 19**, and **Tailwind CSS**.
   - Dynamic charts (Recharts) covering gap distribution, scheme performance metrics, sentiment variance, and pipeline health.
   - Dark/Light mode theme switching and responsive analytics.

---

## 🏗 System Architecture

```mermaid
graph TD
    A[Public Data / Grievance Inquiries / CSV Feeds] --> B[Collection Engine & Scrapers]
    B --> C[FastAPI REST Backend]
    C --> D[(SQLite / PostgreSQL DB)]
    C --> E[ML / NLP Pipeline]
    E --> E1[SentenceTransformers: all-MiniLM-L6-v2]
    E --> E2[HDBSCAN Semantic Clustering]
    E --> E3[Intent & Gap Classifiers]
    E1 --> D
    E2 --> D
    E3 --> D
    D --> C
    C --> F[Next.js 16 Web Dashboard]
    F --> G[Interactive Choropleths & Leaflet Maps]
    F --> H[Gap Analytics & Insights Explorer]
```

---

## 📂 Project Structure

```
govt-welfare-scheme-gap-analysis/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── main.py           # FastAPI entry point & lifespan handler
│   │   ├── config.py         # Pydantic v2 application settings
│   │   ├── database.py       # SQLAlchemy engine & session factory
│   │   ├── seed.py           # Database seeder (15 schemes, geography, sample data)
│   │   ├── models/           # SQLAlchemy ORM models (Scheme, Document, Cluster, etc.)
│   │   ├── routers/          # API route controllers (dashboard, geography, schemes, etc.)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # Business logic (dataset import, crawler engine, analytics)
│   ├── connectors/           # External feed & data connectors
│   └── worker.py             # Asynchronous background collection worker
├── frontend/                 # Next.js 16 App Router UI
│   ├── src/
│   │   ├── app/              # Next.js pages (dashboard, explorer, geography, schemes, etc.)
│   │   ├── components/       # UI components, interactive Leaflet maps, stat cards
│   │   └── lib/              # API clients and utilities
│   ├── public/               # Static assets & India GeoJSON files (states & districts)
│   └── package.json          # Frontend dependencies
├── ml/                       # NLP & Machine Learning modules
│   ├── awareness_gap/        # Gap classification
│   ├── clustering/           # HDBSCAN semantic clustering
│   ├── embeddings/           # SentenceTransformer vectorizer
│   ├── intent/               # Citizen intent classifier
│   ├── preprocessing/        # Text normalization & cleaning
│   └── scheme_detection/     # Entity matching & scheme detection
├── data/
│   ├── raw/                  # Initial research CSV dataset (127+ classified records)
│   ├── geographic/           # Boundary data cache
│   ├── processed/            # Processed vectors and datasets
│   └── uploads/              # User-uploaded dataset storage
├── docker/                   # Docker environment configurations
├── docker-compose.yml        # PostgreSQL service definition
├── requirements.txt          # Python dependencies
├── package.json              # Root orchestration scripts (concurrent dev)
└── .env.example              # Template environment configuration
```

---

## 💻 Prerequisites

Ensure you have the following installed on your machine:
- **Python 3.10+** (Python 3.10, 3.11, 3.12, or 3.13)
- **Node.js 18.x or 20.x+** and **npm**
- **Git**
- *(Optional)* **Docker & Docker Compose** (only required if you want PostgreSQL instead of SQLite)

---

## 🚀 Quick Start Guide

### 1. Clone the Repository

```bash
git clone https://github.com/rishikethanreddy/govt-welfare-scheme-gap-analysis.git
cd govt-welfare-scheme-gap-analysis
```

---

### 2. Configure Environment Variables

Create your local `.env` file from the provided example template:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

> **Note:** By default, `.env` is configured to use a zero-configuration SQLite database (`welfare_awareness.db`), so you can run the project immediately without installing PostgreSQL.

---

### 3. Backend Setup (Python)

Create a Python virtual environment and install the required dependencies:

**On Windows:**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**On macOS / Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4. Seed the Database

Populate the database with the **15 core welfare schemes**, Indian **states/UTs geographic boundaries**, and the **initial research dataset**:

```bash
# With venv activated:
python -m backend.app.seed
```

You should see:
```text
============================================================
  Seeding Database
============================================================
  [OK] Database tables created/verified
  [OK] Seeded 15 welfare schemes
  [OK] Seeded 37 states/UTs + India
  [OK] Registered initial CSV source
  [OK] Imported dataset v1.0: 127 records
============================================================
  [OK] Seed complete!
============================================================
```

---

### 5. Frontend Setup (Next.js)

Install the frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

---

## ⚡ Running the Project

You can run the full platform using either a single orchestrator command or separate terminal windows.

### Method 1: One-Command Start (Root Orchestrator)

First, install the root orchestration utility (one time):
```bash
npm install
```

Then start Frontend + Backend + Background Worker concurrently (automatically detects your `venv` on Windows, macOS, and Linux):

```bash
npm run dev
```

> **Note:** `npm run dev` uses the built-in runner (`scripts/run-python.js`) which automatically directs Python execution through your local virtual environment (`venv`), so you don't even need to worry about path differences or manual virtualenv activation!

---

### Method 2: Multi-Terminal Start (Recommended for Debugging)

Running services in separate terminals gives you clear, real-time logging for each service:

#### 🌐 Terminal 1 — FastAPI Backend Server
```bash
# Activate your venv first
# Windows: .\venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API will be accessible at: `http://127.0.0.1:8000`
- Swagger Interactive Docs: `http://127.0.0.1:8000/docs`

#### ⚙️ Terminal 2 — Background Scraping & Collection Worker
```bash
# Activate your venv first
python -m backend.worker
```

#### 💻 Terminal 3 — Next.js Frontend UI
```bash
cd frontend
npm run dev
```
- Web Application will be live at: `http://localhost:3000`

---

### Method 3: Running with Docker (PostgreSQL)

If you prefer using a PostgreSQL database rather than SQLite:

1. Start the PostgreSQL container:
   ```bash
   docker-compose up -d
   ```
2. Update `.env` with your Postgres connection string:
   ```env
   DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/welfare_awareness
   ```
3. Run migrations / seed script:
   ```bash
   python -m backend.app.seed
   ```
4. Start backend and frontend as usual.

---

## 📖 API Documentation

Once the backend is running, open your browser to view the interactive OpenAPI documentation:

| Interface | URL | Description |
| :--- | :--- | :--- |
| **Swagger UI** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive API testing sandbox |
| **ReDoc** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | Detailed endpoint specifications |

### Core API Endpoints

- `GET /api/dashboard/stats`: Aggregate KPIs, top scheme gaps, intent counts.
- `GET /api/schemes`: List registered schemes (PM-KISAN, PMFBY, PMAY, etc.).
- `GET /api/geography/distribution`: State and district-wise gap signals for choropleths.
- `GET /api/documents`: Filterable citizen queries, split by gap type, sentiment, and scheme.
- `POST /api/analyze/text`: Real-time NLP inference on custom citizen inquiries.
- `POST /api/collection/campaigns`: Trigger automated crawl campaigns across civic sources.
- `GET /api/health`: System health & database connectivity status.

---

## 🛠 Troubleshooting & FAQs

### Q: PowerShell shows `Execution of scripts is disabled on this system` when activating `venv`?
Run this command in PowerShell to permit script execution for your session:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Q: Port 8000 or 3000 is already in use?
- Change the backend port: `uvicorn backend.app.main:app --port 8001 --reload` (update `NEXT_PUBLIC_API_URL` in `.env` accordingly).
- Change the frontend port: `cd frontend && npm run dev -- -p 3001`.

### Q: How do I test the NLP pipeline on custom sentences?
Visit `http://localhost:3000/analyze` or run a quick POST request:
```bash
curl -X POST "http://127.0.0.1:8000/api/analyze/text" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"I applied for PM-KISAN 3 months ago but have not received my 6000 rupees installment.\"}"
```

### Q: Are the map boundaries for India included?
Yes! The vector geo-boundaries (`india.geojson` and `india_districts.geojson`) are located in `frontend/public/` and load automatically in the **Geography** view.

---

## 🤝 Contributing & License

Contributions, bug reports, and pull requests are welcome!

Distributed under the **MIT License**. See `LICENSE` for more information.
