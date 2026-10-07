# DQPS — Autonomous D2C Advertising Intelligence & Decision Engine

Backend-only implementation.

## Quickstart
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/generate_mock_data.py
uvicorn app.main:app --reload --port 8000

Docs: http://localhost:8000/docs

## Supabase
Run supabase_schema.sql in Supabase SQL editor.

## Endpoints
POST /ingest/run
GET  /ingest/summary
POST /diagnose/run
POST /diagnose/full
GET  /execute/recommendations
POST /execute/run
GET  /feed/events
POST /feed/feedback
GET  /health

## Native C NN
Compile to libnn.so exposing: float score_conversion(float* feats, int n);
Set NN_LIBRARY_PATH in .env. Falls back to logistic regression otherwise.
