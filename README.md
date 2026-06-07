# 🧠 AI 智能体协作平台

基于 **LangGraph + FastAPI** 的多智能体协作系统，四位 AI Agent 接力完成从规划到编码的全流程任务。

## 架构说明

```
用户请求
    │
    ▼
┌─────────────┐    简单问题   ┌──────────────┐
│  路由判断    │──────────────│  聊天 / RAG  │────── 结束
│  (Router)   │              └──────────────┘
└─────────────┘
    │ 复杂任务
    ▼
┌─────────────┐     ┌────────────────┐     ┌─────────────┐
│  规划者      │────▶│  研究员        │────▶│  编码者      │
│  (PM)       │     │  (Analyst)     │     │  (Engineer) │
└─────────────┘     └────────────────┘     └─────────────┘
                                                    │
                                                    ▼
                                             ┌─────────────┐
                                             │  执行器      │
                                             │  (沙箱)     │
                                             └─────────────┘
                                                    │
                                                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   结束       │◀────│  审核者      │
                    └─────────────┘ 通过 └─────────────┘
                           ▲                    │
                           │    不通过（重试）    │
                           └────────────────────┘
```

## Agent 角色说明

| Agent | 角色 | 职责 |
|-------|------|------|
| **Planner（规划者）** | 项目经理 | 分析任务，制定执行计划 |
| **Researcher（研究员）** | 情报分析员 | 搜索网页和内部文档，收集上下文信息 |
| **Coder（编码者）** | 软件工程师 | 基于计划和研究成果生成 Python 代码 |
| **Reviewer（审核者）** | QA 工程师 | 验证执行结果，批准或要求修复 |

## 技术栈

- **后端**：FastAPI + LangGraph + LangChain
- **大模型**：Qwen-Plus（通过 DashScope 的 OpenAI 兼容 API）
- **向量数据库**：ChromaDB + HuggingFace 嵌入模型（text2vec-base-chinese）
- **工具集**：DuckDuckGo 搜索、Playwright（百度/哔哩哔哩爬虫）、Python 沙箱执行
- **前端**：原生 HTML/CSS/JS + Tailwind CSS + Markdown 渲染 + SSE 流式传输

## 快速开始

### 环境要求

- Python 3.11+
- [DashScope API Key](https://dashscope.console.aliyun.com/)

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/iphone15p/Enterprise-Agent.git
cd Enterprise-Agent

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装 Playwright 浏览器（用于网页爬虫）
playwright install chromium

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 DashScope API_KEY

# 6. 启动服务
uvicorn server_app:app --host 0.0.0.0 --port 7860
```

在浏览器中打开 **http://localhost:7860** 即可使用。

## Docker 部署

```bash
docker build -t enterprise-agent .
docker run -p 7860:7860 --env-file .env enterprise-agent
```

## 项目结构

```
├── agents/              # 四个 AI Agent（规划者、研究员、编码者、审核者）
│   ├── planner_agent.py
│   ├── researcher_agent.py
│   ├── coder_agent.py
│   └── reviewer_agent.py
├── graph/               # LangGraph 工作流编排
│   └── workflow.py
├── tools/               # Agent 工具集（搜索、浏览器、代码执行器、RAG）
│   ├── search_tool.py
│   ├── browser_tool.py
│   ├── execute_tool.py
│   ├── rag_tool.py
│   └── file_tool.py
├── core/                # 配置模块
│   └── config.py
├── frontend/            # Web 前端界面
│   └── index.html
├── docs/                # 内部知识库文档
│   └── company_docs.txt
├── data/                # 运行时数据（SQLite、ChromaDB）— 已加入 .gitignore
├── server_app.py        # FastAPI 应用入口
├── api.py               # API 入口（uvicorn api:app 方式启动）
├── Dockerfile
├── requirements.txt
└── .env.example
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `API_KEY` | DashScope API 密钥 | — |
| `BASE_URL` | DashScope 接口地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `MODEL_NAME` | 大模型名称 | `qwen-plus` |
| `AUTH_TOKEN` | 前端认证令牌 | `demo_token` |

## 开源协议

MIT
