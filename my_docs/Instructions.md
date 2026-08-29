## Phase-0

- Spin up the Legacy MSSQL Server
```
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=FdeEnterprisePass123!" -p 1433:1433 --name legacy-mssql -d mcr.microsoft.com/mssql/server:2022-latest

# or multi-line in windows 
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=FdeEnterprisePass123!" ^
   -p 1433:1433 --name legacy-mssql ^
   -d mcr.microsoft.com/mssql/server:2022-latest

# or multi-line unix
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=FdeEnterprisePass123!" \
   -p 1433:1433 --name legacy-mssql \
   -d mcr.microsoft.com/mssql/server:2022-latest

# or multi-line with volume inside EC2
docker run -v mssql_data:/var/opt/mssql \
  -e "ACCEPT_EULA=Y" \
  -e "MSSQL_SA_PASSWORD=FdeEnterprisePass123!" \
  -p 1433:1433 \
  --name legacy-mssql \
  -d mcr.microsoft.com/mssql/server:2022-latest

```

- Installation
```
# Create the isolated FDE environment
conda create -n fde_env_test python=3.12 -y

# Activate the environment
conda activate fde_env_test

# Install the core dependencies
pip install pandas sqlalchemy pyodbc
pip install streamlit langgraph langchain-openai
```
---

After running the above docker command and running
```
python scripts\ingest_legacy_data.py
```

we are getting below error (summary):
```
This error (pyodbc.InterfaceError: IM002 ... Data source name not found) means Windows cannot find the exact SQL Server network driver specified in your script.

The code is likely looking for DRIVER={ODBC Driver 18 for SQL Server}, but your machine either doesn't have it installed, or has a different version (like Version 17).
```

FIX :
```
Two Ways to Fix ThisTo achieve a true "zero-installation hassle" workflow, you have two strategic options:

- Option 1 (Fastest right now): Run the quick 1-minute Microsoft ODBC Driver installer on your Windows machine. This immediately satisfies your local Python environment's networking requirements.
>>> winget install "Microsoft ODBC Driver 18 for SQL Server" --accept-source-agreements --accept-package-agreements


- Option 2 (Pure Docker): Move your Python script inside a container too. By creating a custom Dockerfile or a docker-compose.yml file, you can bundle both your Python runtime environment and your SQL Server database together into a unified virtual network.
```

After going with Option-A : The system is working now.

## Phase-1 (On-Camera)

We need to query the database
- Download : https://github.com/microsoft/azuredatastudio
   - https://learn.microsoft.com/en-us/previous-versions/azure-data-studio/download-azure-data-studio?tabs=win-install%2Cwin-user-install%2Credhat-install%2Cwindows-uninstall%2Credhat-uninstall
- The recommendation is to use VS code extension : "SQL Server (mssql)" by microsoft
   - Click on icon that looks like server or refrigarator, not the one with cylinder 
   - Add connection
   - Fill the below :
   ```
   Profile Name: legacy-mssql
   Server name*: localhost
   Port: 1433
   Trust server certificate: 🟩 Check this box / turn it ON (Crucial for Docker)
   Authentication type*: SQL Login
   User name*: sa
   Password*: FdeEnterprisePass123!
   Save Password: 🟩 Check this box
   Database name: Type master (or leave it on "Select a database")
   Encrypt: ⚠️ Change this from Mandatory to Optional (or False)
   ```
   - Click connect
   - in VSCODE : CTRL + N -> create a new file
   - Look at the bottom right corner of your VS Code window. It probably says Plain Text.
   - Click on Plain Text > A search bar will open at the top. Type sql and hit Enter.
   - Look at the very bottom status bar of VS Code now; it will show localhost:master to confirm your file is linked
   - FDE-Hook:

   "If you want to build AI for the enterprise, you have to stop building toy RAG apps on clean text files. In the real world, you are handed systems like this."
   -  Paste and Run the Query
   ```
   SELECT COUNT(*) AS total_rows FROM dbo.TBL_SC_FLEET_HIST_RAW;
   
   Output : total_rows > 32065
   ```
   - Next try :
   ```
   SELECT TOP 100 * FROM dbo.TBL_SC_FLEET_HIST_RAW;
   ```
   - Highlight the columns: Hover your mouse over IOT_TEMP_VAL_C, CGO_COND_CD, and RISK_CLS_TXT.
   - The Problem Statement: "This is a 30-year-old logistics database. The column names are cryptic, the data types are mixed, and if you hand an LLM direct access to this raw schema, it's going to hallucinate. Worse, if you give an AI 'root' access, you are one prompt-injection away from an UPDATE command destroying live supply chain data."

## Phase-2


Create the Phase 2 Directory > scripts/

Create a file named setup_security_and_view.sql inside scripts/.

During the video recording, you will execute this script (or copy/paste it into DBeaver/Azure Data Studio) while explaining to the audience why you are doing it.

- Click on file : scripts\setup_security_and_view.sql
- VS-code will show you Start button directly on top else run like we were running the commands previously.
- Once done, create a new connection now with Agent-Profile
```
* Profile Name: agent-fde-ro
* Connection Group: Leave it on <Default>
* Input type: Select Parameters (Do not click "Load from Connection String", "Browse Azure", or "Browse Fabric")
* Server name*: localhost
* Port: 1433
* Trust server certificate: 🟩 Check this box / Turn it ON
* Authentication type*: SQL Login
* User name*: USR_FDE_RO
* Password*: AgentPassword2026!
* Save Password: 🟩 Check this box / Turn it ON
* Database name: Type master (or click "Select a database" and select master)
* Encrypt: Change this from Mandatory to Optional (or False)
```

Connect and test below commands :
```
-- TEST 1: This SHOULD work perfectly (Access to clean view)
SELECT TOP 5 * FROM FDE_VIEWS.VW_ACTIVE_FLEET;

-- TEST 2: This SHOULD fail instantly (Access to raw legacy table is DENIED)
SELECT TOP 5 * FROM dbo.TBL_SC_FLEET_HIST_RAW;
```

The Python Verification Script: 
- Altough tested from above but lets test this from python script
- To verify that the security actually works. Create scripts/test_agent_access.py
- Run : python scripts/test_agent_access.py

## Phase-3 (The Architecture TDD (On-Camera Briefing)

Before you write the next line of code in the video, you will spend 60 seconds explaining Phase 3.

What you say: "Now that the database is locked down, we need to build the brain. We are using LangGraph. We will equip our agent with three specific tools: a Text-to-SQL tool to read the live telemetry view, a Vector Search tool to read our compliance SOPs, and an API tool to check live weather routes."

Let's build those exact tools right now.

## Phase 4: Constructing the Agent Tools

We are going to create a modular file that contains all three tools. We will use LangChain's `@tool` decorator so LangGraph can natively understand and invoke them.

Also we are going to use pinecone to store vector of our DOC.

### The Multi-Developer Architecture Design
To prevent system crashes and vector coordinate distortion, we enforce a strict index separation layout based on environment variables:

- **Developer-A (Has OpenAI Key):** Ingests into `fde-sop-index-openai` using cloud `OpenAIEmbeddings` at **1536 dimensions**.
- **Developer-B (No OpenAI Key):** Ingests into `fde-sop-index-local` using the cutting-edge local **`BAAI/bge-m3`** open-source engine at **1024 dimensions**.

### Delta Loading & Chunking Blueprint
We are defining an advanced, format-aware chunking strategy in the ingestion script that handles **Markdown headers, plain text files, binary PDFs, and tabular data (CSV/Excel rows)** cleanly.

We also use a state tracking file (`data/cache/ingestion_hash_cache.json`) to enforce **Incremental Ingestion**. The script calculates an MD5 checksum fingerprint for every file. If a document hasn't changed, it is skipped (`✨ Skipped`), saving computing power and cloud token costs. If a file changes or gets deleted from the source folder, the script targets and purges old entries automatically before dropping in fresh data.

- Step 1 : Ingestion dependencies
```bash
pip install pypdf pandas openpyxl sentence-transformers langchain_huggingface
```

- Step 2 : Create the `.env` file
Place this file in your project root workspace:
```text
OPENAI_API_KEY=sk-your-actual-api-key-here (Optional)
PINECONE_API_KEY=your-pinecone-api-key-here
```

- Step 3 : Execute the ingestion
This scans the path, tracks file modifications via the local state cache folder, builds the appropriate Pinecone cloud index, and uploads text chunks:
```cmd
python scripts\ingest_sop_pinecone.py
```

- Step 4: Install RAG and Tools dependencies
```bash
pip install pinecone-client langchain-pinecone langchain-core requests sqlalchemy pyodbc
```

- Step 5: Create the Tools File
Create this file at `experiment/phase-4/agent_tools.py` or your designated scripts module. It matches the exact environment routing layout as the ingestion script so your agent queries the correct database index:


## Phase-5 : The LangGraph Orchestrator

Since the database is locked down (Phase 2) and the tools/vector DB are built and verified (Phase 4), it is time to build the "brain" of the FDE Agent.

We will create a LangGraph state machine that observes the user's prompt, decides which of your three tools to use (and in what order), and synthesizes a final operational plan.

### The Agentic Reasoning Engine
Unlike traditional linear scripts, we are deploying a **ReAct (Reasoning + Acting)** architecture. The orchestrator uses a cyclic `StateGraph` where the LLM evaluates the `AgentState`, determines if it needs external data, triggers the `ToolNode`, and recursively evaluates the tool's output until it has enough context to solve the user's problem.

### Multi-Model Execution & Stateful Memory
To make this robust for enterprise environments, we included two major architectural features:
1. **Dynamic Model Binding:** The brain can seamlessly swap between cloud OpenAI (`gpt-4o`), flagship DeepSeek (`deepseek-v4-flash`), or a completely local Ollama instance (`qwen2.5:7b`), proving the system is vendor-agnostic.
2. **Persistent Checkpointing:** By injecting LangGraph's `MemorySaver()` and assigning a `thread_id`, the agent maintains conversation history. It doesn't just answer one-off questions; it acts as a stateful, continuous copilot for the logistics dispatcher.

Step-1 : Create
```
src/orchestrator.py
```

Step-2 : Pass below in the dispatcher >
- Question-1 (The "Domino Effect" Test)
```
Find any active shipments near Los Angeles (Latitude ~33.8, Longitude ~-118.1). Check the local weather there, and tell me if the current cargo temperature violates the SOP for fresh perishables.
```

- Question-2 (The "Restraint" Test (No-Tool Routing))
```
I'm a new dispatcher on the night shift. Can you quickly explain the difference between a Tier 1 and Tier 2 escalation?
```
- Question-2.1 (The "Memory & Context" Test)
```
Okay, based on that, draft a short 2-sentence email I can send to the driver.
```

- Question-3 (The "Data Hallucination" Trap)
```
What is the exact port congestion index in Miami right now, and what does the SOP say we should do about it?
```

- Question-4 (The "Temporal Filter" Test (Your Date Range Request))
```
Analyze the database and tell me how many shipments were recorded in the first 15 days of January 2021. What was the average temperature of those specific shipments?
```

Step-3 : All tested and they all worked.

## Phase-6 : Building the Streamlit UI & Secure Audit Logging Pipeline

Since the LangGraph orchestrator (Phase 5) is fully operational and capable of multi-tool reasoning, memory management, and multi-model execution, we need an UI interface to test the system.

We built a Streamlit Dispatch Console featuring real-time event tracing, secure multi-user state handling, and a custom database auditing pipeline that respects the principle of least privilege.

Also Separation of Concerns via Dual-Database Roles

The Agent/Dispatcher Layer (USR_FDE_RO): Has strict SELECT rights on the fleet telemetry view (VW_ACTIVE_FLEET) and fine-grained INSERT rights to record its own thought processes and execution traces. It has zero UPDATE, DELETE, or DROP capabilities.

The Administrative Layer (SQL_ADMIN_USER): Isolated behind an authentication gate in the UI, requiring explicit high-privilege credentials to query and inspect historical audit trails.

Persistent Visual Tracing: Unlike standard chat apps where intermediate agent steps vanish upon rerun, the UI captures tool inputs (generated SQL queries and API payloads) and raw outputs, storing them persistently in session state alongside the markdown responses.

- Step-1 : Create the Audit Table in SQL Server for agent to insert the traces.

```
Go to VS-code > CTRL + N > 'click on plain-text' and use 'sql'

Select the su user and write below :

CREATE TABLE FDE_VIEWS.AgentAuditLog (
    LogID INT IDENTITY(1,1) PRIMARY KEY,
    Timestamp DATETIME DEFAULT GETDATE(),
    SessionID VARCHAR(50),
    NodeExecuted VARCHAR(50),
    ToolName VARCHAR(100),
    Content NVARCHAR(MAX) -- NVARCHAR to safely handle JSON strings and large LLM outputs
);

-- Grant the agent user permission to write only to this specific table
GRANT INSERT ON FDE_VIEWS.AgentAuditLog TO USR_FDE_RO;
```


- Step-2 : Configure Secure .env Credentials
```
# Least-Privilege Agent Account (Write-only for logs, read-only for data)
SQL_AGENT_USER=USR_FDE_RO
SQL_AGENT_PASSWORD=AgentPassword2026!

# High-Privilege Admin Account (For reviewing logs in Tab 2)
SQL_ADMIN_USER=sa
SQL_ADMIN_PASSWORD=AdminPassword2026!
```

- Step-3 : 
Validation for agent-access : 
```
SELECT 
    o.name AS ObjectName,
    dp.permission_name AS PermissionName,
    dp.state_desc AS PermissionState
FROM sys.database_permissions dp
JOIN sys.objects o ON dp.major_id = o.object_id
WHERE dp.grantee_principal_id = USER_ID('USR_FDE_RO');
```

- Step-4 : Launch and Validate the Streamlit Command Center
```
streamlit run src/ui.py
```