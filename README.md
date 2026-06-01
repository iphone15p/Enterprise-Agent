# Enterprise AI Agent System

A multi-agent AI system built with **LangGraph** and **FastAPI**, featuring a four-agent collaborative pipeline for intelligent task processing.

## Architecture

```
User Request
    │
    ▼
┌─────────────┐    simple    ┌──────────────┐
│   Router    │──────────────│  Chat / RAG  │────── END
│   Judge     │              └──────────────┘
└─────────────┘
    │ complex
    ▼
┌─────────────┐     ┌────────────────┐     ┌─────────────┐
│  Planner    │────▶│  Researcher    │────▶│   Coder     │
│  (PM)       │     │  (Analyst)     │     │  (Engineer) │
└─────────────┘     └────────────────┘     └─────────────┘
                                                    │
                                                    ▼
                                             ┌─────────────┐
                                             │  Executor   │
                                             │  (Sandbox)  │
                                             └─────────────┘
                                                    │
                                                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    END      │◀────│  Reviewer   │
                    └─────────────┘ PASS└─────────────┘
                           ▲                    │
                           │     FAIL (retry)   │
                           └────────────────────┘
```

## Agent Roles

| Agent | Role | Responsibility |
|-------|------|----------------|
| **Planner** | Project Manager | Analyzes tasks, produces execution plans |
| **Researcher** | Intelligence Analyst | Searches web + internal docs, gathers context |
| **Coder** | Software Engineer | Generates Python code based on plan + research |
| **Reviewer** | QA Engineer | Validates execution results, approves or requests fixes |

## Tech Stack

- **Backend**: FastAPI + LangGraph + LangChain
- **LLM**: Qwen-Plus (DashScope) via OpenAI-compatible API
- **Vector DB**: ChromaDB + HuggingFace embeddings (text2vec-base-chinese)
- **Tools**: DuckDuckGo Search, Playwright (Baidu/Bilibili scraping), Python sandbox
- **Frontend**: Vanilla HTML/CSS/JS with Tailwind CSS, Markdown rendering, SSE streaming

## Quick Start

### Prerequisites

- Python 3.11+
- [DashScope API Key](https://dashscope.console.aliyun.com/)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/iphone15p/Enterprise-Agent.git
cd Enterprise-Agent

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers (for web scraping)
playwright install chromium

# 5. Configure environment
cp .env.example .env
# Edit .env and add your API_KEY from DashScope

# 6. Run the server
uvicorn server_app:app --host 0.0.0.0 --port 7860
```

Open **http://localhost:7860** in your browser.

## Docker Deployment

```bash
docker build -t enterprise-agent .
docker run -p 7860:7860 --env-file .env enterprise-agent
```

## Project Structure

```
├── agents/              # Four AI agents (Planner, Researcher, Coder, Reviewer)
│   ├── planner_agent.py
│   ├── researcher_agent.py
│   ├── coder_agent.py
│   └── reviewer_agent.py
├── graph/               # LangGraph workflow orchestration
│   └── workflow.py
├── tools/               # Agent tools (search, browser, code executor, RAG)
│   ├── search_tool.py
│   ├── browser_tool.py
│   ├── execute_tool.py
│   ├── rag_tool.py
│   └── file_tool.py
├── core/                # Configuration
│   └── config.py
├── frontend/            # Web UI
│   └── index.html
├── docs/                # Internal knowledge base documents
│   └── company_docs.txt
├── data/                # Runtime data (SQLite, ChromaDB) — gitignored
├── server_app.py        # FastAPI application entry point
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | DashScope API Key | — |
| `BASE_URL` | DashScope endpoint | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `MODEL_NAME` | LLM model name | `qwen-plus` |
| `AUTH_TOKEN` | Frontend auth token | `demo_token` |

## License

MIT
