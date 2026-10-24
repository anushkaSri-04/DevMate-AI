# 🧑‍💻 DevMate AI

> A repository-aware AI coding assistant designed to help developers understand, analyze, and interact with their GitHub repositories through intelligent tools.

**Project Status:** 🚧 Active Development

DevMate AI is being developed as a developer-focused AI assistant that combines **GitHub APIs, MCP, LLMs, and code retrieval** to help developers work with real software repositories.

The project is being built incrementally, starting with a reliable GitHub API backend and progressing toward an MCP-powered AI coding assistant.

---

## 🎯 Project Goal

The goal of DevMate AI is to create a repository-aware coding assistant capable of understanding a developer's GitHub repository and assisting with common development tasks.

Planned capabilities include:

- Retrieve repository information
- Analyze GitHub issues
- Search repository code
- Explain code
- Investigate bugs
- Suggest tests
- Answer repository-level questions
- Assist with developer workflows
- Interact with GitHub through controlled tools

The long-term architecture combines:

**GitHub REST API + MCP + LLM + Code Retrieval/RAG**

---

## 🏗️ Current Implementation

The current version focuses on building a reliable Python backend for interacting with the GitHub REST API.

### Implemented Features

- ✅ GitHub authentication using Personal Access Token
- ✅ Environment-based configuration
- ✅ Pydantic Settings configuration management
- ✅ Reusable GitHub API client using HTTPX
- ✅ GitHub repository listing
- ✅ Repository detail retrieval
- ✅ GitHub issue retrieval
- ✅ Issue pagination
- ✅ Pull request filtering
- ✅ Open issue counting
- ✅ Open issue aggregation across multiple repositories
- ✅ Input validation
- ✅ HTTP error handling
- ✅ GitHub rate-limit awareness
- ✅ `Retry-After` handling
- ✅ `X-RateLimit-Reset` handling
- ✅ Exponential backoff
- ✅ Bounded retry mechanism
- ✅ Automated testing using Pytest
- ✅ HTTP API mocking using Respx
- ✅ Testing of transient API failures
- ✅ Testing of exhausted retry scenarios

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| HTTPX | GitHub REST API communication |
| Pydantic | Data validation |
| Pydantic Settings | Environment-based configuration |
| Pytest | Automated testing |
| Respx | HTTP request mocking |
| GitHub REST API | Repository and issue data |
| Git | Version control |

---

## 📁 Project Structure

```text
DevMate-AI/
│
├── tools/
│   ├── __init__.py
│   ├── config.py
│   ├── github_client.py
│   └── github_tools.py
│
├── tests/
│   ├── test_github_client.py
│   ├── test_github_client_retry.py
│   ├── test_github_client_retry_exhausted.py
│   ├── test_github_tools.py
│   └── ...
│
├── .env.example
├── .gitignore
├── main.py
├── pyproject.toml
└── README.md
```

---

## 🔐 Authentication & Configuration

DevMate AI uses a GitHub Personal Access Token for authenticated API requests.

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_token
GITHUB_API_BASE_URL=https://api.github.com
```

The application loads configuration using **Pydantic Settings**.

### Security

Sensitive credentials are not stored directly in the source code.

The `.env` file is excluded from Git using `.gitignore`.

**Never commit your GitHub token or other credentials to the repository.**

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/DevMate-AI.git
cd DevMate-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

#### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -e .
```

For development dependencies:

```bash
pip install -e ".[dev]"
```

### 5. Configure environment variables

Create a `.env` file:

```env
GITHUB_TOKEN=your_github_token
GITHUB_API_BASE_URL=https://api.github.com
```

---

## 🧪 Testing

Run the complete test suite using:

```bash
python -m pytest -q
```

The project uses **Pytest** for automated testing.

Testing currently covers:

- GitHub authentication
- Repository operations
- Issue retrieval
- Input validation
- Pagination
- Pull request filtering
- Retry behavior
- Rate-limit handling
- Mocked GitHub API failures
- Exhausted retry scenarios

---

## 🔄 API Reliability

DevMate AI includes retry and rate-limit handling for temporary GitHub API failures.

For example:

```text
GitHub API Request
        │
        ▼
429 Too Many Requests
        │
        ▼
Read Retry-After
        │
        ▼
Wait / Backoff
        │
        ▼
Retry Request
        │
        ▼
200 OK
        │
        ▼
Successful Response
```

The client currently handles transient HTTP errors including:

```text
429 Too Many Requests
500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
```

Retries are bounded to prevent infinite retry loops.

---

## 🧩 GitHub Tools

The current backend provides reusable functions for interacting with GitHub.

### Repository Tools

```python
list_repositories()
```

Retrieves repositories belonging to the authenticated GitHub user.

```python
get_repository_details(owner, repo)
```

Retrieves details about a specific repository.

### Issue Tools

```python
list_issues(owner, repo)
```

Retrieves repository issues with support for:

- Open issues
- Closed issues
- All issues
- Pagination
- Input validation
- Pull request filtering

```python
count_open_issues(owner, repo)
```

Counts open issues for a repository.

```python
count_open_issues_across_repositories(repositories)
```

Aggregates open issue counts across multiple repositories.

---

## 🔁 Current Architecture

The current implementation follows a modular structure:

```text
Application
     │
     ▼
GitHub Tools
     │
     ▼
GitHub Client
     │
     ▼
HTTPX
     │
     ▼
GitHub REST API
```

This separation keeps API communication separate from application-level tool logic and makes the system easier to test and extend.

---

## 🧪 Testing Without GitHub

External APIs should not need to be contacted for every test.

DevMate AI uses **Respx** to mock HTTP requests made through HTTPX.

For example, a GitHub rate-limit failure can be simulated:

```text
Mock GitHub API
       │
       ▼
429 Response
       │
       ▼
Retry
       │
       ▼
200 Response
```

This makes tests:

- Faster
- Repeatable
- Independent of internet connectivity
- Independent of GitHub availability
- Safer with respect to API rate limits

---

## 🗺️ Roadmap

### Phase 1 — GitHub Integration

- [x] GitHub authentication
- [x] Environment configuration
- [x] GitHub API client
- [x] Repository tools
- [x] Issue tools
- [x] Pagination
- [x] Input validation
- [x] Pull request filtering
- [x] Error handling
- [x] Rate-limit handling
- [x] Retry mechanism
- [x] Automated testing
- [x] Mocked API failure testing
- [x] Exhausted retry testing

### Phase 2 — MCP Integration

- [ ] MCP fundamentals
- [ ] MCP server
- [ ] MCP tool registration
- [ ] Tool schemas
- [ ] Structured tool responses
- [ ] MCP ↔ GitHub integration
- [ ] Tool discovery and invocation

### Phase 3 — AI Developer Assistant

- [ ] LLM integration
- [ ] Intelligent tool selection
- [ ] Code search
- [ ] Code explanation
- [ ] Bug investigation
- [ ] Test suggestions
- [ ] Multi-step developer workflows

### Phase 4 — Repository Intelligence

- [ ] Repository code ingestion
- [ ] Code retrieval
- [ ] RAG pipeline
- [ ] Context-aware code analysis
- [ ] Repository-level question answering

### Phase 5 — Evaluation & Deployment

- [ ] Task-based evaluation benchmark
- [ ] Tool-selection evaluation
- [ ] Retrieval evaluation
- [ ] Answer correctness evaluation
- [ ] Failure-handling evaluation
- [ ] Observability
- [ ] Documentation
- [ ] Deployment

---

## 🔒 Security Principles

DevMate AI follows basic security and reliability principles:

- Credentials are stored using environment variables.
- `.env` is excluded from version control.
- GitHub API access follows the principle of least privilege.
- API requests use bounded retries.
- Rate limits are respected.
- External API failures are handled explicitly.
- Write operations will require additional safety controls.
- Sensitive credentials should never be included in source code.

---

## 📚 Learning Focus

This project is also being used to develop practical skills in:

- Python backend development
- REST APIs
- GitHub API integration
- API authentication
- Error handling
- Rate limiting
- Retry strategies
- Automated testing
- HTTP mocking
- MCP
- LLM-based tool use
- RAG
- AI-assisted software development

---

## 👩‍💻 Author

**Anushka Srivastava**

B.Tech — Artificial Intelligence & Data Science

### Interests

- Artificial Intelligence
- Machine Learning
- Generative AI
- Large Language Models
- MCP
- Backend Development
- Cloud & Deployment

---

## 📌 Project Status

**🚧 Active Development**

DevMate AI is currently being developed incrementally.

The GitHub integration and API reliability layer are implemented and tested. The next stages focus on integrating **Model Context Protocol (MCP)**, followed by **LLM-powered tool selection, repository intelligence, code retrieval, and RAG-based code understanding**.

---

⭐ If you find this project interesting, feel free to explore the repository and follow its development.