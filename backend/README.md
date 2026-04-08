# 🌤️ PMA Weather API (Backend)

[![Backend CI](https://github.com/mogesTesema/PM-Accelerator-Weather-App/actions/workflows/backend-CI.yml/badge.svg)](https://github.com/mogesTesema/PM-Accelerator-Weather-App/actions/workflows/backend-CI.yml)
[![Backend CD](https://github.com/mogesTesema/PM-Accelerator-Weather-App/actions/workflows/backend-CD.yml/badge.svg)](https://github.com/mogesTesema/PM-Accelerator-Weather-App/actions/workflows/backend-CD.yml)
[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-6.0%2B-092E20.svg?logo=django)](https://www.djangoproject.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Deployment](https://img.shields.io/badge/render-deployed-success?logo=render)](https://pma-weather-app-ftol.onrender.com)

A production-grade, AI-powered weather intelligence system engineered for the **PM Accelerator AI Engineering Intern assessment**. This backend exposes a highly scalable RESTful API built with Django, powered by full CRUD operations, multi-format exports, and an autonomous LLM orchestration layer that fetches and contextualizes weather, location, and multimedia data in real-time.

---

## 🌟 Live Deployed API Documentation

- **Swagger UI:** [https://pma-weather-app-ftol.onrender.com/api/docs/](https://pma-weather-app-ftol.onrender.com/api/docs/)
- **ReDoc:** [https://pma-weather-app-ftol.onrender.com/api/redoc/](https://pma-weather-app-ftol.onrender.com/api/redoc/)

---

## 📑 Table of Contents

- [Visuals](#visuals)
- [Architectural Highlights & Features](#architectural-highlights--features)
- [Tech Stack](#tech-stack)
- [Local Setup & Installation](#local-setup--installation)
- [API Endpoints & Usage](#api-endpoints--usage)
- [Testing & CI/CD](#testing--cicd)
- [Contributing Guidelines](#contributing-guidelines)
- [License](#license)
- [About](#about)



<a id="architectural-highlights--features"></a>
## 🏗️ Architectural Highlights & Features

- **🤖 Autonomous LLM Orchestration:** Integrates the OpenAI-compatible chat-completions API with function calling to parse complex natural language queries, dynamically invoking distinct tools to return structured weather intelligence. Supports multiple LLM backends (OpenAI, GitHub Models, Groq, DeepSeek).
- **🔍 Semantic Fuzzy Location Matching (Pinecone):** Uses Pinecone's vector database with `llama-text-embed-v2` embeddings (1024-dim, cosine similarity) to semantically resolve ambiguous or alias-based queries — e.g., *"Big Apple"* → New York City, *"Iron Lady"* → Eiffel Tower, *"City of Light"* → Paris. Pre-seeded with 120 world capitals, major cities, and famous landmarks via a dedicated management command.

```mermaid
flowchart LR
    A["User Query: 'Big Apple'"] --> B{"LocationIQ\n(Exact Geocoding)"}
    B -- "✅ Found" --> D["lat/lon → OpenWeatherMap"]
    B -- "❌ Not Found" --> C{"Pinecone\n(Semantic Search)"}
    C -- "score ≥ 0.3" --> E["'New York City'\nlat=40.71, lon=-74.00"]
    E --> D
    C -- "score < 0.3" --> F["❌ Location not found"]
```
- **🌍 Extensive Third-Party APIs:** Orchestrates data from **OpenWeatherMap**, **LocationIQ**, **Google Maps**, **Stadia Maps**, and **YouTube** to provide a rich, multimedia-enriched weather context.
- **📄 Extensible Export System:** Includes a robust, custom abstraction for exporting weather records seamlessly into CSV, JSON, PDF, XML, and Markdown.
- **📅 5-Day Forecast with Day-Range Filtering:** Supports up to 5-day forecasts with a customizable `days` parameter (1–5), returning clear error messages for invalid ranges.
- **⚙️ Automated CI/CD:** Protected by a smart GitHub Actions workflow separating CI and CD layers, strictly enforcing Pytest and Ruff linting rules prior to Render deployment.

<a id="tech-stack"></a>
## 🛠️ Tech Stack

| Category         | Technology / Dependency |
|------------------|-------------------------|
| **Core**         | Python 3.13, Django 6.0, Django REST Framework, PostgreSQL |
| **Package Mgr**  | `uv` (Ultra-fast Python package installer) |
| **AI / LLM**     | OpenAI-compatible chat-completions (OpenAI, GitHub Models, Groq, DeepSeek) |
| **Vector DB**    | Pinecone Serverless (Free Tier), `llama-text-embed-v2` via Pinecone Inference API |
| **Integrations** | `httpx`, `requests` (OpenWeather, Google Maps, Stadia Maps, YouTube, LocationIQ) |
| **Dev Tools**    | Pytest, Ruff, Factory-Boy, Gunicorn, Docker |

---

<a id="local-setup--installation"></a>
## 🚀 Local Setup & Installation

Getting the backend running locally takes less than a minute utilizing the `uv` package manager.

### Prerequisites
- **Python 3.13+** installed on your system.
- **uv** package manager (`pip install uv`).
- **PostgreSQL** running locally (or via Docker).

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/mogesTesema/PM-Accelerator-Weather-App.git
cd PM-Accelerator-Weather-App/backend

# Sync and install all dependencies using uv
uv sync
```

### 2. Environment Configuration
Create a `.env` file in the `backend/` directory with the following variables:
```env
# Core Django Config
DJANGO_SETTINGS_MODULE=config.settings.dev
DJANGO_SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://user:password@localhost:5432/pma-weather-db

# External API Keys
OPEN_WEATHER_API_KEY=your_openweather_key
LOCATIONIQ_API_KEY=your_locationiq_key
YOUTUBE_API_KEY=your_youtube_key
GOOGLE_MAPS_API_KEY=your_google_maps_key
GOOGLE_API_KEY=your_google_api_key
STADIA_MAPS_API_KEY=your_stadia_maps_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=pma-weather-app-vector-db
PINECONE_HOST=your_pinecone_index_host

# LLM Provider (at least one required for AI agent)
OPENAI_API_KEY=your_openai_key
# Or use free/budget alternatives:
# GITHUB_OPENAI__API_TOKEN=your_github_token
# GROQ_API_KEY=your_groq_key
# DEEPSEEK_API_KEY=your_deepseek_key
```

### 3. Migrate, Seed & Run
```bash
# Run database migrations
uv run manage.py migrate

# Seed the Pinecone vector index with 120 world locations (one-time setup)
uv run manage.py seed_locations

# Start the development server
uv run manage.py runserver
```

---

<a id="api-endpoints--usage"></a>
## 📖 API Endpoints & Usage

This project automatically generates standard OpenAPI specifications using `drf-spectacular`.

### 🌐 Live Production API Docs
- **Swagger UI:** [https://pma-weather-app-ftol.onrender.com/api/docs/](https://pma-weather-app-ftol.onrender.com/api/docs/)
- **ReDoc:** [https://pma-weather-app-ftol.onrender.com/api/redoc/](https://pma-weather-app-ftol.onrender.com/api/redoc/)

### 💻 Local Development
Once the server is running locally:
- **Swagger UI:** `http://127.0.0.1:8000/api/docs/`
- **ReDoc:** `http://127.0.0.1:8000/api/redoc/`

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/weather/locations/` | List all locations |
| `POST` | `/api/weather/locations/` | Create a new location |
| `GET` | `/api/weather/records/` | List all weather records |
| `POST` | `/api/weather/records/` | Create a weather record (manual) |
| `POST` | `/api/weather/create/` | Create weather record via location query + date range |
| `GET` | `/api/weather/forecast/` | Get up to 5-day forecast (`?location_query=...&days=3`) |
| `GET` | `/api/weather/enrichment/` | Get YouTube videos & Google Maps data for a location |
| `GET` | `/api/weather/export/` | Export weather data (`?export_format=json\|csv\|pdf\|xml\|md`) |
| `POST` | `/api/weather/agent/query/` | AI agent natural language query |

*(Example: AI Orchestrator query)*
```bash
curl -X POST http://127.0.0.1:8000/api/weather/agent/query/ \
     -H "Content-Type: application/json" \
     -d '{"message": "What is the weather like near the Eiffel Tower?"}'
```

*(Example: 3-day forecast)*
```bash
curl "http://127.0.0.1:8000/api/weather/forecast/?location_query=London&days=3"
```

---

<a id="testing--cicd"></a>
## 🧪 Testing & CI/CD

The project strictly enforces linting rules and an automated testing suite using `pytest`.

```bash
# Run the complete test suite
uv run pytest

# Run Ruff linter
uv run ruff check .
```

A robust **GitHub Actions** CI/CD pipeline protects the `main` branch by enforcing test coverage and code style. To optimize cloud compute costs and avoid stuck Pull Requests under strict branch protection rules, the pipeline utilizes an advanced architecture:

- **Pipeline Decoupling:** The CI workflow (testing & linting) is entirely separated from the CD workflow, ensuring expensive Render deployments only trigger upon explicitly authorized merges to `main`.
- **Smart Branch Protection Bypass:** A dedicated dummy bypass workflow (`backend-bypass.yml`) intelligently satisfies `main` branch status checks when only non-backend files (like documentation or frontend assets) are modified. This prevents PR gridlock while maintaining strict security policies.

---

<a id="contributing-guidelines"></a>
## 🤝 Contributing Guidelines

We welcome contributions! Please follow these steps to securely contribute to the codebase:
1. Fork the repository and create a new feature branch (`git checkout -b feature/awesome-feature`).
2. Make your targeted changes, ensuring you pass strict formatting requirements (`uv run ruff check .`).
3. Maintain test coverage locally (`uv run pytest`).
4. Push your branch and open a Pull Request against `main`.

For more detailed rules, please see our [CONTRIBUTING.md](../CONTRIBUTING.md).

---

<a id="license"></a>
## 📜 License

This backend project is licensed under the **MIT License**. See the [LICENSE](../LICENSE) file in the root workspace directory for more details.

---

<a id="about"></a>
## 🎓 About

**Author:** Moges Tesema  
**Project Objective:** This system represents the technical capstone and backend engineering requirement for the **PM Accelerator AI Engineering Intern** assessment. It bridges the gap between scalable web infrastructure (Django) and modern Generative AI tooling architectures.
