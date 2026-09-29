# AttentionPay

AttentionPay is an AI-assisted payment security system designed to detect phishing websites and identify potentially fraudulent transactions through a layered security pipeline.

The system combines BERT-based phishing detection, rule-based transaction security checks, TabTransformer-based fraud detection, and Explainable AI (XAI) to provide both a security decision and an explanation of the model's prediction.

> **Project Scope:** AttentionPay is a controlled payment-security simulation developed for academic and demonstration purposes. It is not intended to process real financial transactions or replace production banking security systems.

---

## Features

- BERT-based phishing URL detection
- Two-stage payment security pipeline
- API route integrity verification
- Impossible-travel detection
- TabTransformer-based transaction fraud detection
- SHAP/LIME-based explainability
- Human-readable fraud explanations
- Transaction simulation using predefined scenarios
- PostgreSQL-backed transaction data
- React-based interactive dashboard
- FastAPI backend
- Docker-ready backend structure

---

## System Architecture

```text
                         ┌─────────────────────┐
                         │        User         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Stage 1: BERT     │
                         │ Phishing Detection  │
                         └──────────┬──────────┘
                                    │
                       ┌────────────┴────────────┐
                       │                         │
                    Phishing                  Legitimate
                       │                         │
                       ▼                         ▼
                    BLOCK              ┌─────────────────────┐
                                       │ Stage 2: Transaction│
                                       │      Security       │
                                       └──────────┬──────────┘
                                                  │
                                                  ▼
                                  ┌──────────────────────────┐
                                  │ Layer 1 Security Checks  │
                                  │                          │
                                  │ • API Route Integrity    │
                                  │ • Impossible Travel      │
                                  └────────────┬─────────────┘
                                               │
                              ┌────────────────┴────────────────┐
                              │                                 │
                            BLOCK                              PASS
                              │                                 │
                              ▼                                 ▼
                           BLOCKED                    ┌─────────────────────┐
                                                      │ Feature Engineering │
                                                      └──────────┬──────────┘
                                                                 │
                                                                 ▼
                                                      ┌─────────────────────┐
                                                      │    TabTransformer   │
                                                      │  Fraud Detection    │
                                                      └──────────┬──────────┘
                                                                 │
                                                                 ▼
                                                      ┌─────────────────────┐
                                                      │   Explainable AI    │
                                                      │     SHAP / LIME     │
                                                      └──────────┬──────────┘
                                                                 │
                                                                 ▼
                                                      ┌─────────────────────┐
                                                      │   Result Dashboard  │
                                                      └─────────────────────┘
```

---

## Technology Stack

### Frontend

- React
- Vite
- Axios
- React Leaflet
- Recharts
- CSS

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic Settings
- SQLAlchemy
- PostgreSQL
- Python-dotenv

### Machine Learning

#### Stage 1 — Phishing Detection

- BERT
- Hugging Face Transformers
- PyTorch

The model analyzes submitted URLs and classifies them as:

- Legitimate
- Phishing

#### Stage 2 — Transaction Fraud Detection

- TabTransformer
- PyTorch
- Scikit-learn
- Joblib

The model processes structured transaction and behavioral features to classify transactions as:

- Fraud
- Legitimate

### Explainable AI

- SHAP
- LIME
- Attention-based explanations
- Human-readable explanations

---

## Project Structure

```text
Attention_Pay/
│
├── backend/
│   ├── app/
│   │   ├── dependencies/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   └── explainability/
│   │   ├── utils/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   │
│   ├── ml/
│   │   └── tabtransformer/
│   │       ├── artifacts/
│   │       └── model.py
│   │
│   ├── create_tables.py
│   ├── seed_transactions.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── state/
│   │   ├── styles/
│   │   └── utils/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── model/
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer.json
│   └── tokenizer_config.json
│
├── AttentionPay SDD.pdf
├── .gitignore
└── README.md
```

---

## Security Pipeline

AttentionPay uses a layered approach rather than relying entirely on a single machine-learning model.

### Stage 1 — Phishing Detection

The user first submits a payment or website URL.

The BERT model analyzes the URL and determines whether it is **Legitimate** or **Phishing**.

- If the URL is classified as phishing, the transaction flow is stopped.
- If the URL is considered legitimate, the user can proceed to the transaction-security stage.

### Stage 2 — Transaction Security

Stage 2 contains two security layers.

#### Layer 1 — Backend Security Checks

Before the machine-learning fraud model is executed, the backend performs security checks including:

**API Route Integrity**

Checks whether the expected API route and transaction request structure have been maintained.

**Impossible Travel**

Checks whether the user's transaction location and timing indicate an impossible physical movement.

For example:

```text
Transaction A
Location: Bangalore
Time: 10:00 AM

Transaction B
Location: London
Time: 10:05 AM
```

Such a transition can be flagged by the backend security layer.

If a Layer 1 security check fails, the transaction is blocked before the TabTransformer is executed.

#### Layer 2 — TabTransformer Fraud Detection

Transactions that pass Layer 1 are processed by the TabTransformer model.

The model receives engineered transaction and behavioral features and produces a fraud/legitimate prediction.

The model uses structured transaction information such as:

- Transaction velocity
- Transaction amount
- Previous transaction amount
- Device information
- Browser information
- Operating system
- Session risk
- Amount compared with user average
- Time since previous transaction
- User/device history
- Receiver history
- Behavioral information

The feature engineering layer converts incoming transaction data into the format expected by the trained model.

---

## Explainable AI

AttentionPay does not only provide a prediction.

When the TabTransformer is executed, the system also generates explanations for the prediction.

The XAI layer uses:

- SHAP
- LIME
- Model attention information
- Human-readable explanation generation

The frontend presents these explanations through the results dashboard. This allows the user to understand which transaction characteristics contributed to the model's decision.

---

## Transaction Simulation

AttentionPay includes a controlled transaction simulation system for demonstrating different security conditions.

Supported simulation scenarios include:

- Normal Transaction
- Impossible Travel
- API Route Tampering
- Behaviour Fraud
- Random Transaction

The simulation flow is:

```text
Scenario Selection
        │
        ▼
Scenario Generator
        │
        ▼
Generate Transaction Values
        │
        ▼
Feature Engineering
        │
        ▼
Layer 1 Security Checks
        │
        ├── Block
        │
        └── Pass
              │
              ▼
       TabTransformer
              │
              ▼
       Explainable AI
              │
              ▼
       Final Result
```

The simulation is intended to demonstrate how different transaction conditions move through the security pipeline.

---

## Backend API

The backend is implemented using FastAPI.

### Health Check

```http
GET /health
```

Used to verify that the backend is running.

### Analyze URL

```http
POST /api/v1/analyze/url
```

Analyzes a submitted URL using the Stage 1 BERT phishing detection model.

The endpoint determines whether the URL is legitimate or phishing. A legitimate result allows the transaction flow to continue to Stage 2.

### Simulate Transaction

```http
POST /api/v1/simulate/transaction
```

Creates/retrieves a transaction for the selected simulation scenario.

### Process Transaction

```http
POST /api/v1/simulate/transaction/{transaction_id}/process
```

Processes the selected transaction through:

```text
Layer 1 Security
       ↓
Feature Engineering
       ↓
TabTransformer
       ↓
Explainability
       ↓
Final Decision
```

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Harshith810/Attention_Pay.git
cd Attention_Pay
```

### Backend Setup

### 2. Create a Python Virtual Environment

From the project root:

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file according to the backend configuration required by the project.

> **Do not** commit credentials, database passwords, API keys, or other secrets to Git.

### 5. Start the Backend

From the project root:

```bash
uvicorn backend.app.main:app --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

FastAPI Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### Frontend Setup

Open another terminal.

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Vite will provide the local frontend URL in the terminal.

---

## Running the Full Application

You should have two terminals running.

**Terminal 1 — Backend** (from the project root)

```bash
uvicorn backend.app.main:app --reload
```

**Terminal 2 — Frontend**

```bash
cd frontend
npm run dev
```

The frontend communicates with the FastAPI backend through the configured API base URL.

---

## Database

AttentionPay uses PostgreSQL for transaction simulation data.

The backend contains scripts for database initialization and transaction seeding:

```bash
python backend/create_tables.py
```

and:

```bash
python backend/seed_transactions.py
```

Database configuration should be provided through the backend environment configuration.

---

## Model Artifacts

The repository contains the required trained-model artifacts.

### Stage 1

The BERT model and tokenizer files are located under `model/`, including:

- `model.safetensors`
- `config.json`
- `tokenizer.json`
- `tokenizer_config.json`

### Stage 2

The TabTransformer model and preprocessing artifacts are located under:

```text
backend/ml/tabtransformer/artifacts/
```

These include the trained model and preprocessing components required for inference.

---

## Development Notes

AttentionPay separates security decisions into different stages.

The general decision flow is:

```text
URL
 │
 ▼
BERT Phishing Detection
 │
 ├── Phishing ───────────────► BLOCK
 │
 └── Legitimate
        │
        ▼
   Transaction
        │
        ▼
 Layer 1 Security
        │
        ├── Failed ──────────► BLOCK
        │
        └── Passed
               │
               ▼
        Feature Engineering
               │
               ▼
         TabTransformer
               │
               ▼
          Fraud Check
               │
               ▼
        SHAP / LIME / XAI
               │
               ▼
         Result Dashboard
```

This separation ensures that deterministic security checks can stop a transaction before invoking the machine-learning fraud model.

---

## Project Documentation

The detailed Software Design Document is available in `AttentionPay SDD.pdf`.

It contains the project's architecture, system design, processing flow, model components, and implementation details.

---

## Disclaimer

AttentionPay is an academic and demonstration project.

It uses simulated transaction scenarios and machine-learning models to demonstrate a layered payment-security architecture.

It should not be used as a production payment-processing system, banking system, or security solution without appropriate security validation, compliance review, infrastructure hardening, monitoring, and independent testing.

---

## License

This project is intended for academic and educational purposes.

Add an explicit open-source license here if the repository is intended to be distributed under one.
