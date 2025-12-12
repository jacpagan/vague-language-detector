# Vague Language Detector

This is a small FastAPI app that detects whether a statement **is vague** (binary yes/no), optimized for statements that are **100% true in all cases**.

## Run it (copy/paste)

### 1) Download the project and open it in Terminal

If you have git installed:

```bash
git clone https://github.com/jacpagan/vague-language-detector.git
cd vague-language-detector
```

If you downloaded a ZIP: unzip it, then `cd` into the unzipped folder (it will usually be named `vague-language-detector`).

```bash
cd vague-language-detector
```

### 2) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

(If you see `(.venv)` at the start of your prompt, it’s activated.)

### 3) Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4) Start the server

```bash
python -m uvicorn vague_language_detector.main:app --host 127.0.0.1 --port 8000
```

Leave that running.

### 5) Open the API docs in your browser

- Swagger UI: `http://127.0.0.1:8000/docs`

## Examples (copy/paste)

Open a **second** Terminal window/tab (keep the server running), then:

### Health check

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### Classify text

```bash
curl -X POST http://127.0.0.1:8000/classify \
  -H 'Content-Type: application/json' \
  -d '{"text":"I always mess everything up."}'
```

You’ll get a JSON response including `has_cognitive_distortion`.

## Run tests

```bash
source .venv/bin/activate
python -m pytest
```

## Stress test (load test)

Start the server in one terminal:

```bash
source .venv/bin/activate
python -m uvicorn vague_language_detector.main:app --host 127.0.0.1 --port 8000
```

Then, in a second terminal:

```bash
source .venv/bin/activate
python scripts/stress_test.py --concurrency 50 --duration 15
```

More aggressive:

```bash
python scripts/stress_test.py --concurrency 200 --duration 30 --timeout 2
```

## Troubleshooting

### “address already in use” (port 8000 is busy)

Either run on a different port:

```bash
python -m uvicorn vague_language_detector.main:app --host 127.0.0.1 --port 8001
```

Or find and stop whatever is using port 8000:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
kill <PID>
```

### Stop the server

Go back to the Terminal running `uvicorn` and press **Ctrl+C**.
