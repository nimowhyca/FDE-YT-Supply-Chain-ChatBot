# End-to-End FDE Project : Logistics Telemetry to SOP Agent

---

## 1. Project Overview & Narrative Arc

* **Target Goal:** Create a high-converting, realistic video showcasing how a Forward Deployed Engineer (FDE) operates in production.
* **Core Difference Highlighted:** Move beyond toy RAG and isolated LLM demos by combining **legacy data ingestion, client discovery, technical risk mitigation, hybrid tools (SQL + RAG + API), LangGraph agentic orchestration, and a deployable UI**.
* **The Business Scenario:** A regional cold-chain logistics operator in Southern California is suffering severe cargo spoilage and SLA delay penalties across their transport corridors. Operations analysts cannot cross-reference real-time vehicle telemetry against company SOPs during transit emergencies.

---

## 2. Step-by-Step Implementation Roadmap

```
[Phase 1: Ingestion & Setup] ──► [Phase 2: Discovery & Scoping] ──► [Phase 3: Architecture & TDD]
                                                                            │
[Phase 6: Frontend & Deploy] ◄── [Phase 5: LangGraph Agents]  ◄── [Phase 4: Tool Construction]

```

---

### Phase 1: Legacy Data & Environment Setup

1. **Load Raw Telemetry:** Ingest the 15.4MB Southern California logistics dataset (`supply_chain_telemetry.csv`) into a local SQLite database (`legacy_fleet.db`), simulating an on-premise relational database.
2. **Schema & Indexing:** Ensure primary columns (`timestamp`, `vehicle_gps_latitude`, `vehicle_gps_longitude`, `iot_temperature`, `delay_probability`, `risk_classification`, `cargo_condition_status`) are properly indexed for rapid filtering.
3. **Draft the Unstructured Policy Document:** Author `Cold_Chain_Incident_SOP_v2.md` covering:
* Mandatory temperature breach thresholds ($> 4.0^\circ\text{C}$ for fresh perishables; $> -18.0^\circ\text{C}$ for frozen freight).
* High port/route congestion diversion protocols (e.g., redirecting Long Beach freight to Inland Empire depots).
* Driver fatigue management protocols when `fatigue_monitoring_score > 0.75`.



---

### Phase 2: Client Discovery & Requirements Scoping

1. **The FDE Consultation Scene:**
* **Question:** *"Who will interact with this system—external customers or internal operations analysts?"*
* **Client Response:** *"Internal operations analysts and dispatchers."*
* **FDE Architectural Decision:**
* Since this is internal analytical/BI workflow rather than automated customer-facing transaction execution, use **parameterized Text-to-SQL on a Read-Only Replica** rather than building static CRUD API endpoints for every ad-hoc query.




2. **Security & Risk Guardrails:**
* Restrict database permissions to `SELECT`-only to prevent accidental data modification.
* Mandate query execution timeouts and parameter sanitization to block SQL injection.



---

### Phase 3: Technical Design Document (TDD) & Stakeholder Deck

1. **Executive Presentation Structure (Slide Outline):**
* **Slide 1: Problem Statement & Cost of Inaction** (Spoilage rates, SLA penalties).
* **Slide 2: Architectural Gap** (Why vanilla vector RAG fails on raw numeric time-series data).
* **Slide 3: Proposed Dual-Engine Architecture** (Structured SQL + Unstructured SOP RAG + Live Weather API).
* **Slide 4: Security & Compliance Posture** (Zero-write access, read-only replica, deterministic safeguards).
* **Slide 5: Expected ROI & Delivery Timeline** (Estimated reduction in incident resolution time from 45 min to 90 sec).



---

### Phase 4: Constructing the Three Core Tools

1. **Tool 1: `query_telemetry_db(sql_query: str)**`
* Executes read-only SQL queries against `legacy_fleet.db`.
* Enforces regex checks ensuring queries start strictly with `SELECT`.
* Returns structured tabular data (e.g., vehicles with temperature anomalies or high disruption risk).


2. **Tool 2: `fetch_corridor_conditions(latitude: float, longitude: float)**`
* Queries a live external weather/traffic API (or deterministic mock endpoint) for current conditions, visibility, and road hazards at specific coordinates.


3. **Tool 3: `search_compliance_sop(query: str)**`
* Performs semantic vector search (via Chroma/FAISS with dense embeddings) over `Cold_Chain_Incident_SOP_v2.md`.
* Extracts actionable standard operating procedures and escalation paths.



---

### Phase 5: LangGraph Agentic Orchestration

1. **State Definition:** Maintain conversation history, active vehicle coordinates, retrieved telemetry state, and retrieved policy context.
2. **ReAct Workflow & Routing:**
* **Step 1 (Analyze User Intent):** Determine required information sources.
* **Step 2 (Telemetry Execution):** Query the legacy database for real-time sensor metrics and coordinates.
* **Step 3 (Anomaly Trigger):** If anomalies exist, query the weather/corridor tool and retrieve relevant SOP compliance clauses.
* **Step 4 (Structured Synthesis):** Return an executive summary, diagnostic breakdown, and recommended operational intervention.



---

### Phase 6: Frontend Interface & Docker Deployment

1. **Streamlit Operations Console:**
* **Left Panel:** Chat interface for natural-language dispatch queries.
* **Right Panel:** Interactive map (`st.map` / PyDeck) plotting GPS coordinates with dynamic color markers (Green: Normal, Orange: Moderate Risk, Red: Critical Cold-Chain Breach), alongside live sensor telemetry gauges.


2. **Containerization (`Dockerfile`):**
* Package Python backend, Streamlit frontend, SQLite database, and vector index into a single, reproducible container image ready for cloud or on-premise deployment.

---