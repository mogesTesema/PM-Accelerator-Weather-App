# Contributing to PMA Weather API

First of all, thank you for considering contributing to the **PMA Weather API**! We welcome community contributions, whether they are bug fixes, feature enhancements, or documentation improvements.

This document provides a set of guidelines to ensure the contribution process is smooth and standard across all developers.

## 🛠️ Project Structure
This repository is a monorepo containing:
- **`backend/`**: Our scalable Django REST API powered by OpenAI and Pinecone.
- **`frontend/`**: The React-based user interface.

## 🌱 Getting Started

### 1. Fork & Clone
1. Fork this repository to your own GitHub account.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/PM-Accelerator-Weather-App.git
   cd PM-Accelerator-Weather-App
   ```

### 2. Branching Strategy
Create a new branch for your work. Use descriptive names highlighting the scope:
- **Features:** `feature/add-weather-history`
- **Bug Fixes:** `bugfix/fix-pinecone-query`
- **Docs:** `docs/update-architecture-diagram`

```bash
git checkout -b feature/your-feature-name
```

## 💻 Development Requirements

### Backend Development (`/backend`)
We strictly utilize Python 3.13+ and `uv` for package management. 

1. **Install dependencies:**  
   ```bash
   cd backend
   uv sync
   ```
2. **Linting & Formatting:**  
   We strictly enforce code styling utilizing [Ruff](https://docs.astral.sh/ruff/). Ensure your code passes before committing:
   ```bash
   uv run ruff check .
   uv run ruff format .
   ```
3. **Testing:**  
   We require **100% test coverage** for backend logic. Our CI pipeline will automatically fail if coverage drops. Run the test suite natively:
   ```bash
   uv run pytest
   ```

### Frontend Development (`/frontend`)
*(Check the `frontend/` directory for specific node instructions on starting the React application).*

## 📤 Submitting a Pull Request (PR)

Before submitting your PR, please ensure:
1. You have successfully updated your branch with the latest changes from `main`:
   ```bash
   git fetch origin
   git rebase origin/main
   ```
2. You have successfully run all linting and test commands without errors.
3. Your PR title is descriptive and concisely maps to the issue it resolves.
4. Your PR description clearly explains **what** changed and **why**.

Once submitted, our decoupled **GitHub Actions CI Pipeline** (`backend-CI.yml`) will automatically fire to check your formatting and tests. The CD deployment pipeline is strictly protected and will only trigger once your code is merged into `main` by an administrator.

## 🤝 Community Respect
Please be respectful and professional in code reviews and issue discussions. Let's build something fantastic together!
