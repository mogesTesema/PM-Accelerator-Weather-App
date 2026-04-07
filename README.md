# 🌤️ PM Accelerator Weather App

[![Backend CI](https://github.com/mogesTesema/PM-Accelerator-Weather-App/actions/workflows/backend-CI.yml/badge.svg)](https://github.com/mogesTesema/PM-Accelerator-Weather-App/actions/workflows/backend-CI.yml)
[![Backend CD](https://github.com/mogesTesema/PM-Accelerator-Weather-App/actions/workflows/backend-CD.yml/badge.svg)](https://github.com/mogesTesema/PM-Accelerator-Weather-App/actions/workflows/backend-CD.yml)
[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-6.0%2B-092E20.svg?logo=django)](https://www.djangoproject.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Deployment](https://img.shields.io/badge/render-deployed-success?logo=render)](https://pma-weather-app-ftol.onrender.com)

**PM Accelerator Mission Statement**  
*To accelerate the transition into product management and empower the next generation of tech leaders through hands-on, practical experience.*

A production-grade, AI-powered weather intelligence system engineered for the **PM Accelerator AI Engineering Intern assessment**. This backend exposes a highly scalable RESTful API built with Django, powered by full CRUD operations, multi-format exports, and an autonomous LLM orchestration layer that fetches and contextualizes weather, location, and multimedia data in real-time.

*(Note: The frontend implementation has been deferred. The application is served and fully functional purely via its robust backend and REST API endpoints.)*

---

## 🌟 Live Deployed API Documentation

The API has been successfully deployed and is available online. You can effortlessly test all endpoints and review schemas via the following live documentation links:

- **Swagger UI (Interactive API Tests):** [https://pma-weather-app-ftol.onrender.com/api/docs/](https://pma-weather-app-ftol.onrender.com/api/docs/)
- **ReDoc (Detailed Schema Reference):** [https://pma-weather-app-ftol.onrender.com/api/redoc/](https://pma-weather-app-ftol.onrender.com/api/redoc/)

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

---

<a id="visuals"></a>
## 📸 Visuals

*(Include an animated GIF or architectural diagram of your API workflow here)*

![API Architecture / Demo Placeholder](https://via.placeholder.com/800x400.png?text=API+Architecture+Diagram+Placeholder)

---

<a id="architectural-highlights--features"></a>
## 🏗️ Architectural Highlights & Features

- **🤖 Autonomous LLM Orchestration:** Integrates the OpenAI Agent SDK to parse complex natural language queries, dynamically invoking distinct tools to return structured weather intelligence.
- **🔍 Vector Database Integration (Pinecone):** Leverages embeddings for fuzzy location matching, instantly resolving natural language searches (e.g., *"The Great Pyramids"*) into explicit coordinates.
- **🌍 Extensive Third-Party APIs:** Orchestrates data from **OpenWeatherMap**, **LocationIQ**, **Google Maps**, and **YouTube** to provide a rich, multimedia-enriched weather context.
- **📄 Extensible Export System:** Includes a robust, custom abstraction for exporting weather records seamlessly into CSV, JSON, PDF, XML, and Markdown.
- **⚙️ 100% Test Coverage & Automated CI/CD:** Protected by a smart GitHub Actions workflow separating CI and CD layers, strictly enforcing Pytest coverage and Ruff linting rules prior to Render deployment.

<a id="tech-stack"></a>
## 🛠️ Tech Stack

| Category         | Technology / Dependency |
|------------------|-------------------------|
| **Core**         | Python 3.13, Django 6.0, Django REST Framework, PostgreSQL |
| **Package Mgr**  | `uv` (Ultra-fast Python package installer) |
| **AI / Data**    | `openai-agents`, Pinecone |
| **Integrations** | `httpx`, `requests` (OpenWeather, Google Maps, YouTube) |
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
Create a `.env` file in the `backend/` directory. Use `.env.example` as a template.
```env
# Core Django Config
DJANGO_SETTINGS_MODULE=config.settings.dev
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://user:password@localhost:5432/pma-weather-db

# API Integrations
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
OPENWEATHER_API_KEY=your_openweather_key
GOOGLE_MAPS_API_KEY=your_google_maps_key
YOUTUBE_API_KEY=your_youtube_key
LOCATIONIQ_API_KEY=your_locationiq_key
```

### 3. Migrate & Run
```bash
# Run database migrations
uv run manage.py migrate

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
Once the server is running locally, you can view the fully interactive documentation:
- **Swagger UI:** `http://127.0.0.1:8000/api/schema/swagger-ui/`
- **Redoc:** `http://127.0.0.1:8000/api/schema/redoc/`

### Core Endpoints
- `GET /api/weather/records/` - List all validated weather queries.
- `POST /api/weather/records/` - Create a new weather record (triggers external API orchestration).
- `GET /api/weather/locations/` - CRUD endpoints for managed location entities.
- `GET /api/weather/records/{id}/export/?format=pdf` - Export specific records to targeted formats.

*(Example query to the AI Orchestrator)*
```bash
curl -X POST http://127.0.0.1:8000/api/weather/records/ \
     -H "Content-Type: application/json" \
     -d '{"location_query": "What is the weather like near the Eiffel Tower?"}'
```

---

<a id="testing--cicd"></a>
## 🧪 Testing & CI/CD

The project strictly enforces linting rules and an automated testing suite using `pytest`.

```bash
cd backend

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
3. Maintain 100% test coverage locally (`uv run pytest`).
4. Push your branch and open a Pull Request against `main`.

For more detailed rules, please see our [CONTRIBUTING.md](CONTRIBUTING.md).

---

<a id="license"></a>
## 📜 License

This backend project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file in the root directory for more details.

---

<a id="about"></a>
## 🎓 About

**Author:** Moges Tesema  
**Project Objective:** This system represents the technical capstone and backend engineering requirement for the **PM Accelerator AI Engineering** assessment. It bridges the gap between scalable web infrastructure (Django) and modern Generative AI tooling architectures.
