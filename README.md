# Vanguard Arena OS 🏟️

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash-8E75C2?style=for-the-badge&logo=google-gemini&logoColor=white)](https://ai.google.dev/)
[![Google Cloud Run](https://img.shields.io/badge/Google%20Cloud%20Run-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/run)

Vanguard Arena OS is a highly performant, secure, and production-ready Python backend leveraging the Google Gemini SDK for **FIFA World Cup 2026** stadium operations, crowds monitoring, and fan safety experiences. 

The entire codebase is designed to be extremely lightweight (weighs less than 1MB including templates and configurations), fast, and fully compliant with modern enterprise software patterns.

---

## 🚀 Live Cloud Deployment

The application is deployed on Google Cloud Run and is fully operational:

*   **API Base URL / OpenAPI Documentation**:  
    [https://vanguard-arena-os-453397284615.us-central1.run.app/docs](https://vanguard-arena-os-453397284615.us-central1.run.app/docs)
*   **Interactive Telemetry Dashboard**:  
    [https://vanguard-arena-os-453397284615.us-central1.run.app/dashboard](https://vanguard-arena-os-453397284615.us-central1.run.app/dashboard)

---

## 🎮 Live Demo Quick Start

Follow these steps to run a telemetry analysis simulation:

### 1. Using the Web Dashboard
1. Open the [Interactive Telemetry Dashboard](https://vanguard-arena-os-453397284615.us-central1.run.app/dashboard).
2. Input the demo credentials token in the **Internal Security Token** field:
   ```text
   d866fa7a41981045a557b7f14b620b78c879d747c320e8d02df91745db7ee12e
   ```
3. Select a **User Role** (e.g. `FAN`, `STAFF`, `VOLUNTEER`, or `ORGANIZER`).
4. Click one of the **Quick Presets** to pre-fill a scenario, or write custom telemetry.
5. Click **Analyze Telemetry Stream** to send the request.

### 2. Testing via Terminal (`curl`)
Run the following request to analyze standard crowd telemetry:
```bash
curl -X POST https://vanguard-arena-os-453397284615.us-central1.run.app/api/v1/operations/analyze \
  -H "Content-Type: application/json" \
  -H "X-Arena-Token: d866fa7a41981045a557b7f14b620b78c879d747c320e8d02df91745db7ee12e" \
  -d '{
    "user_role": "FAN",
    "telemetry_stream": "Ramps near main entrance are clear. Assist desk is active."
  }'
```

---

## ✨ Features

- **💡 AI-Native Operations**: Leverages async-native Gemini SDK for real-time analysis of crowd telemetry and incident response directives.
- **⚡ Non-blocking Async Engine**: Uses Python's native `async`/`await` architecture and FastAPI to handle high-concurrency stadium requests without blocking the event loop.
- **🛡️ Secure By Default**: Enforces authorization via custom header checks and actively blocks prompt injection attempts at the API schema level.
- **♿ Accessibility-First (ADA)**: The AI engine prioritizes step-free, barrier-free route calculations and responds in the detected input language (e.g. Spanish, English).
- **🔄 Resilient Fallback Mode**: Automatically falls back to a highly responsive, rule-based multilingual parser if the Gemini API key is missing or encounters limits.

---

## 🛠️ Architecture & Setup

### Requirements
- **Python**: `3.12+`
- **Dependencies**: `fastapi`, `uvicorn`, `google-generativeai`, `pydantic`, `pytest`, `python-dotenv`, `httpx`

### Local Installation

1. **Clone the repository** and navigate to the directory:
   ```bash
   cd vanguard-arena-os
   ```

2. **Set up the Python environment** using `uv` (recommended):
   ```bash
   uv venv .venv --prompt "vao"
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` and fill in `GEMINI_API_KEY` and your custom `INTERNAL_API_TOKEN`.*

### Running the Server Locally
To spin up the hot-reloading development server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Access the local OpenAPI documentation at `http://localhost:8000/docs` and the control panel at `http://localhost:8000/dashboard`.

### Running the Test Suite
We maintain comprehensive unit test coverage verifying routing logic, security guards, and fallbacks:
```bash
pytest -v
```

---

## 🔌 API Reference

| Endpoint | Method | Headers | Description |
| :--- | :---: | :--- | :--- |
| `/` | `GET` | *None* | Redirects to interactive Swagger `/docs`. |
| `/dashboard` | `GET` | *None* | Serves the premium, glassmorphic operator dashboard UI. |
| `/api/v1/operations/analyze` | `POST` | `X-Arena-Token: <TOKEN>` | Analyzes telemetry streams and maps out response actions. |

### POST `/api/v1/operations/analyze` Payload Specifications

#### Request Body
```json
{
  "user_role": "FAN",
  "telemetry_stream": "Ramp near Gate A is blocked by debris, wheelchair users need support."
}
```
*Allowed `user_role` values: `FAN`, `STAFF`, `VOLUNTEER`, `ORGANIZER`.*

#### Response Body
```json
{
  "alert_level": "MEDIUM",
  "recommendation": "For assistance, proceed to the accessibility guest services desk near the main entrance.",
  "accessibility_routing": "Use the elevator at Section 104 to reach Level 2. Accessible seating is in Section 202."
}
```

---

## 🔒 Security Compliance

### 1. API Token Verification
Endpoints are guarded by the custom `X-Arena-Token` header. Any requests with missing or invalid tokens are immediately blocked with a `403 Forbidden` response:
```http
X-Arena-Token: your_secure_internal_api_token_here
```

### 2. Prompt Injection Safeguards
To prevent attackers from overriding AI behavior using malicious strings (e.g., *"ignore previous instructions"*), the system integrates a regex-based pattern validator inside the Pydantic schema model. These requests fail validation with `422 Unprocessable Entity` before ever reaching the LLM context, protecting resource budgets and safety alignment.

---

## 🐳 Containerization & Cloud Run Deployment

The service contains a lightweight `Dockerfile` configured to run securely on Google Cloud Run:
- **Non-root Execution**: Runs under a dedicated `appuser` (UID/GID 10001) for security compliance.
- **Port Binding**: Binds dynamically to the port provided by Cloud Run via the `PORT` env variable (defaulting to `8080`).
- **Signal Handling**: Launches via `exec uvicorn` to guarantee proper propagation of `SIGTERM` signals for graceful revision updates.

To build and deploy your own instance to Cloud Run:
```bash
gcloud run deploy vanguard-arena-os \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="INTERNAL_API_TOKEN=your_token_here,GEMINI_API_KEY=your_key_here"
```
