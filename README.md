# 🚀 Agent Vikram – LinkedIn Profile Search Orchestrator

Agent Vikram is an **AI-powered search automation tool** that takes a **natural language query** and:
1. **Parses** it into structured search parameters
2. **Generates** precise Google search queries targeting LinkedIn profiles
3. **Runs** those queries using the Serper.dev Google Search API
4. **Stores** results in MySQL for later use
5. **(Optional)** Enriches LinkedIn profiles using SalesQL API

---

## 📌 Example Use Case

**User Input**:  
```
Find profiles of senior Python developers in Hyderabad on LinkedIn
```

**Agent Vikram Output**:  
- Generated Google Search Query:
```
site:linkedin.com/in ("Python developer" OR "Python engineer") Hyderabad
```
- Executes query → saves results in MySQL
- Optionally enriches each LinkedIn profile with SalesQL API

---

## ✨ Features

- **Natural Language to Search Query**  
  Uses an LLM-based **Parser Agent** to extract `tech_stack[]` and `locations[]`
- **LinkedIn-Focused Query Generation**  
  Formats search queries in:
  ```
  site:linkedin.com/in ("<role>" OR "<alternate role>") <location>
  ```
- **Database-Driven Workflow**  
  - `search_query_queue` – stores generated queries with status
  - `google_search_results` – stores SERP results
  - `linkedin_profiles` – stores enriched LinkedIn data
- **Workers for Background Tasks**
- **LinkedIn Profile Enrichment** (optional) via SalesQL
- **Swagger UI** for API testing
- **Future Web UI** (Jinja2 templates)

---

## 🏗 Architecture

```
          ┌─────────────────┐
          │  User Input API │
          └───────┬─────────┘
                  │
                  ▼
           ┌────────────┐
           │ Parser     │
           │  Agent     │
           └─────┬──────┘
                 │ {tech_stack[], locations[]}
                 ▼
           ┌────────────┐
           │ Query      │
           │ Generator  │
           │ Agent      │
           └─────┬──────┘
                 │ Google-style LinkedIn search queries
                 ▼
    ┌─────────────────────────┐
    │ search_query_queue (DB) │
    └───────────┬─────────────┘
                │
        ┌───────▼────────┐
        │ Search Worker  │──> Serper.dev API
        └───────┬────────┘
                ▼
    ┌──────────────────────────┐
    │ google_search_results(DB)│
    └───────┬──────────────────┘
            │
   (Optional│ Enrichment)
            ▼
    ┌──────────────────────────┐
    │ linkedin_profiles (DB)   │
    └──────────────────────────┘
```

---

## 🔌 API Endpoints

### 1. **Generate Search Queries**
**POST** `/agentic-query-generator`  
Generates queries from a natural language request.

Example Request:
```json
{
  "user_input": "Find profiles of senior Python developers in Hyderabad on LinkedIn"
}
```

Example Response:
```json
{
  "search_id": 12,
  "queries_generated": 2,
  "status": "queued"
}
```

---

### 2. **Run Google Search Worker**
Pulls from `search_query_queue`, executes search, stores results in `google_search_results`.

---

### 3. **Enrich LinkedIn Profiles**
**POST** `/linkedin-enrich`  
Fetches profile data from SalesQL API.

Example Request:
```json
{
  "linkedin_url": "https://linkedin.com/in/john-doe"
}
```

Example Response:
```json
{
  "linkedin_url": "https://linkedin.com/in/john-doe",
  "status": "enriched",
  "name": "John Doe",
  "location": "Hyderabad, India"
}
```

---

## 🗄 Database Schema

**`search_query_queue`**
| id | query | status | created_at |
|----|-------|--------|------------|

**`google_search_results`**
| id | search_id | title | link | snippet | created_at |
|----|-----------|-------|------|---------|------------|

**`linkedin_profiles`**
| id | linkedin_url | name | location | headline | enriched_at |
|----|--------------|------|----------|----------|-------------|

---

## ⚙️ Installation

### 1️⃣ Clone Repository
```bash
git clone https://github.com/yourusername/agent-vikram.git
cd agent-vikram
```

### 2️⃣ Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Environment Configuration
Create `.env` file:
```env
OPENAI_API_KEY=your_openai_key
SERPER_API_KEY=your_serper_key
SALESQL_API_KEY=your_salesql_key
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DB=agent_vikram
```

### 5️⃣ Initialize Database
```bash
python scripts/init_db.py
```

### 6️⃣ Run FastAPI Server
```bash
uvicorn main:app --reload
```
Swagger UI:  
```
http://127.0.0.1:8000/docs
```

---

## 💻 Example Usage

### Using `curl`:
```bash
curl -X POST http://127.0.0.1:8000/agentic-query-generator -H "Content-Type: application/json" -d '{"user_input": "Find profiles of React developers in Bangalore on LinkedIn"}'
```

### Using Python:
```python
import requests

payload = {
    "user_input": "Find profiles of React developers in Bangalore on LinkedIn"
}
res = requests.post("http://127.0.0.1:8000/agentic-query-generator", json=payload)
print(res.json())
```

---

## 🛠 Tech Stack

- **Backend**: FastAPI
- **Database**: MySQL (`aiomysql`)
- **Search Provider**: Serper.dev API
- **LLM**: OpenAI API
- **Enrichment**: SalesQL API
- **Docs**: Swagger UI

---

## 📅 Roadmap

- [ ] Web UI (Jinja2)
- [ ] Bulk LinkedIn enrichment
- [ ] Proxy support for search
- [ ] Multi-agent orchestration

---

## 👨‍💻 Author
**Sai B** – Backend Developer & AI Agent Builder
