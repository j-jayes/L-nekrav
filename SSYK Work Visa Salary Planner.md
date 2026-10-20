# **SSYK Work Visa Salary Planner**

[https\://gemini.google.com/app/28aa3db75b1fc5a4](https://gemini.google.com/app/28aa3db75b1fc5a4)

*User prompt: Feature planning: In Sweden, if you come from outside the EU, to get a work visa, you need to apply with a specific job code in mind, ssyk designation for a specific job. https\://www\.scb.se/dokumentation/klassifikationer-och-standarder/standard-for-svensk-yrkesklassificering-ssyk/ In order for your work visa to be accepted, you need to have been offered a salary that first above the minimum threshold of 90% of the median salary (outside of a set of exempted occupations) and above this, is in line with what the union would say is reasonable (check me on the specifics of this). But what it means in effect is that if you are looking for a job in Sweden out of e.g. university you need to be armed with some info in order that you negotiate your salary so that your work permit can be accepted. You need to know which ssyk the job that you are applying for would fall under, then you need to know stats about the salaries for individuals who have that job, and then get an offer in line with what is reasonable. I am thinking of designing a web-based tool that can help prospective job seekers get this info in a digestible way. First, we should explain the law clearly (min threshold, requirements, legal changes over time etc) Then, we want to have a tool where the person can describe the job that they are searching for, in natural language, and we do some vector search across the titles and descriptions for the ssyk classification schema, to find the closest matches. then we need to display salary info related to these occupations, perhaps in some sort of plot with a dotted line for the minimum, and then some distribution. We can include e.g. gender and age as I believe that SCB produces that information stratified in some way. That way the person if they feel it might be useful can apply for a ssyk with lower requirements that you could argue still fits the job description. We should research the information from SCB, and the jobtechdev.se team who have a lot of digital services that could be beneficial. I think they have a whack of job ads, so perhaps we can create a dashboard with some stats about jobs advertised by ssyk over time and by region, as an extension to the project. https\://arbetsformedlingen.se/other-languages/english-engelska/about-the-website/apis-and-open-data Does this make sense?? Can you research widely, try and understand the brief, and then help me come up with a spec that is very detailed for this project?? Ask me as many questions as you wish\!\!*

Response: This concept makes complete sense, and it addresses a massive, high-stakes information asymmetry for non-EU graduates and professionals in Sweden. When navigating *Migrationsverket*, the difference between choosing one 4-digit SSYK code over an adjacent one can literally be the difference between an approved work permit and a deportation order.

## **1\. Fact-Checking the Legal & Regulatory Reality (As of Late 2026\)**

Your understanding of the two-tiered legal requirement is spot on. Both conditions must be met simultaneously, and the rules underwent a major tightening on **June 1, 2026**:

> 1. **Tier 1: The Statutory Floor (*Försörjningskrav*):**  
   * **Current Rule (since June 1, 2026):** The applicant must be offered a gross monthly salary of at least **90% of Sweden's official median wage** published by SCB at the time of application. Based on the current SCB median wage of **37,100 SEK**, the hard floor is **33,390 SEK/month**. *(Note: For extension applications, a transitional rule applies until December 1, 2026).*  
   * **Historical Context for the Tool:** Prior to Nov 2023, the floor was a flat 13,000 SEK. In Nov 2023, it jumped to 80% of the median wage (27,360 SEK, later adjusted to 29,680 SEK).  
   * **The Part-Time Trap:** This 33,390 SEK floor is an *absolute income requirement*, not prorated by work hours. Even if someone is hired at 50% or 80% part-time, their actual gross payout must still clear 33,390 SEK/month.  
   * **Exemptions & Exclusions:** The June 2026 reform introduced a mechanism for government-designated shortage occupations (e.g., certain licensed healthcare roles or specific high-demand categories) to be exempted or held to a lower threshold (such as 75%), while excluding certain high-abuse sectors (like berry picking and personal assistance) altogether. Furthermore, alternative permits like the **EU Blue Card** have their own specific thresholds and rules.  
> 2. **Tier 2: Collective Agreement & Market Practice (*Kollektivavtalsenlig lön / Branschpraxis*):**  
   * Even if a salary offer clears the 33,390 SEK statutory floor, *Migrationsverket* sends the offer (Anställningserbjudande) to the relevant trade union (e.g., *Sveriges Ingenjörer*, *Unionen*, *Akavia*) for a formal statement of opinion (*yttrande*).  
   * The union checks the **4-digit SSYK code** and the job duties against their collective bargaining agreements and internal wage statistics for that specific role, experience level, and age/graduation cohort.  
   * **Why your "SSYK Arbitrage" idea works:** Suppose a fresh graduate takes a hybrid role doing data analytics and business ops. If the employer classifies them under SSYK 2512 (*Mjukvaru- och systemutvecklare*) or 2120 (*Matematiker, aktuarier och statistiker*), the union might look at the 10th percentile for that code and demand 38,000+ SEK. If the role is instead legitimately framed and classified under SSYK 2421 (*Organisationsutvecklare, utredare*) or a broader business analyst code where entry-level union benchmarks sit at 34,500 SEK, the offer clears both the 33,390 SEK floor and the union check.

## **2\. The Data Ecosystem: SCB & JobTechDev**

Both SCB and Arbetsförmedlingen's **JobTechDev** initiative offer free, open APIs (mostly CC0 licensed) that fit together cleanly for this architecture:

| Source | Endpoint / Dataset | What It Gives Us & Limitations |
| :---- | :---- | :---- |
| **SCB PxWeb API** (AM0110) | **Table LoneSpridSektYrk4AN** *(Dispersion by 4-digit SSYK)* | Gives **Mean, Median, 10th, 25th, 75th, and 90th percentiles** by 4-digit SSYK2012, **Sector** (Private white-collar, State, Municipal, etc.), and **Sex**. |
| **SCB PxWeb API** (AM0110) | **Age & Education Stratified Tables** (LonYrkeAlder4AN, LonYrkeUtbildningAN) | **Crucial Nuance:** Because of cell-size disclosure rules (..), SCB does *not* publish percentiles simultaneously cross-tabulated by 4-digit SSYK *and* Age in a single table. Instead, they publish **Dispersion (P10–P90) by SSYK \+ Sector \+ Sex** in one table, and **Mean Salary by SSYK \+ Age Group \+ Sex** (or Education) in sister tables. |
| **SCB Classifications** | **SSYK 2012 Metadata & Descriptions** | Official hierarchy (1- to 4-digit), official descriptions of main tasks, inclusion/exclusion rules, and standard example job titles. |
| **JobTech Taxonomy API** | taxonomy.api.jobtechdev.se | A GraphQL/REST API mapping thousands of specific Swedish/English job titles (occupation-name), skills, and keywords directly to their parent **4-digit SSYK-2012** groups (occupation-group). |
| **JobSearch & JobStream API** | jobsearch.api.jobtechdev.se | Live active job ads in Sweden, pre-tagged with occupation-group (SSYK), municipality, region, and employer organization numbers. |
| **Historical Ads & Links API** | historical.api.jobtechdev.se | Complete archive of Swedish job ads from **2006 to 2026**, enriched with ML-classified SSYK codes, geographic coordinates, and extracted skills. |

## **3\. Proposed System Architecture & Feature Spec**

### **Module 1: The Interactive Legal Guide & Eligibility Simulator**

> * **Visual Timeline of the Law:** A clear scrollytelling or interactive graphic showing the shift from the old 13,000 SEK rule → 80% median (Nov 2023\) → **90% median / 33,390 SEK (June 2026\)**.  
> * **The "Part-Time & Benefits" Calculator:** Users input their proposed monthly base pay, FTE percentage (sysselsättningsgrad), and taxable benefits. The calculator flags immediately if a part-time role drops them below the absolute 33,390 SEK floor, or if their salary sits in the "Union Danger Zone".

### **Module 2: Semantic SSYK Matcher & "Adjacent Code" Explorer**

> * **Hybrid Search Pipeline:**  
  * **Corpus Construction:** For each of the \~430 4-digit SSYK codes, we build a rich document combining: (a) Official SCB SSYK 2012 descriptions & task lists, (b) All mapped occupation-name synonyms and skill tags from the **JobTech Taxonomy API**, and (c) Synthetic or translated **English equivalents** (since almost all non-EU job seekers will search in English or paste an English job description).  
  * **Retrieval:** Combine dense vector embeddings (e.g., multilingual embeddings) with BM25 lexical search so both exact Swedish/English job titles ("Data Engineer", "Systemutvecklare") and free-text duty descriptions match accurately.  
> * **The "Arbitrage / Negotiation" Comparison Matrix:**  
  * Instead of returning a single SSYK code, the UI presents the **Top 3–5 Plausible SSYK Matches** side-by-side with a similarity score, key overlapping tasks, and—"crucially"—how their entry-level salary benchmarks compare.  
  * Example: Showing a user that their role matches 88% with SSYK Code A (P10 salary: 39,500 SEK) and 82% with SSYK Code B (P10 salary: 34,200 SEK), highlighting the specific task descriptions from SCB they should emphasize in their employment contract to justify Code B.

### **Module 3: Salary Distribution & Negotiation Visualizer**

For any selected SSYK code(s), render an interactive chart with user toggles for **Sector** (e.g., *Privatanställda tjänstemän* vs. *Statlig sektor*), **Sex**, and **Age Group**:

> * **The Distribution Layer:** A horizontal boxplot / quantile fan showing the **10th, 25th, 50th (Median), 75th, and 90th percentiles** for that SSYK.  
> * **Reference Lines (The Thresholds):**  
  * **Red Dashed Line:** Statutory Work Permit Floor (**33,390 SEK** — 90% of national median).  
  * **Amber Shaded Zone:** The **P10 to P25 band** for that specific SSYK, representing the typical entry-level/junior market range that unions evaluate against.  
  * **Age Cohort Marker:** Overlay the specific mean salary for the user's age bracket (e.g., 18–24 or 25–34) from SCB's age-stratified table so recent graduates can see exactly where their age peers sit relative to the overall occupational P10/P25.

### **Module 4: Job Market Demand Dashboard (JobTech Extension)**

Once a user identifies their target SSYK codes, they can flip to the **Market Pulse** tab powered by JobTechDev:

> * **Demand Over Time:** Seasonality and multi-year hiring trends (2020–2026) for those SSYK codes using the Historical Job Ads dataset.  
> * **Geographic Heatmap:** Where in Sweden (by *Län* or *Kommun*, e.g., Stockholm vs. Skåne vs. Västra Götaland) these SSYK roles are most heavily advertised.  
> * **Top Hiring Employers & Live Ads:** Pulling top employers by organisationsnummer from historical ads (helpful for targeting companies accustomed to hiring in that SSYK) alongside a live feed of current openings via JobSearch API.

## **4\. Key Questions to Lock Down the Detailed Spec**

To turn this into a concrete technical specification and data pipeline design, let's nail down your preferences on a few architectural and product choices:

> 1. **Handling the SCB Age \+ Percentile Data Split:** Since SCB publishes *Percentiles (P10/P25/P50/P75/P90) by SSYK \+ Sector \+ Sex* in one table, and *Mean Salary by SSYK \+ Age \+ Sex* in another, how would you like to present this visually?  
   * *Option A:* Plot the exact SCB boxplot (P10–P90) for the overall occupation/sector, and plot the Age-Group Means (25–34, 35–44, etc.) as distinct callout markers on top of that distribution.  
   * *Option B:* Estimate an age-adjusted distribution (e.g., shifting or scaling the occupational percentiles using the ratio of the age-group mean to the overall mean, clearly labeled as an estimate).  
> 2. **Bilingual Search & LLM Augmentation:** The official SCB SSYK 2012 descriptions and JobTech taxonomies are primarily in Swedish. Since the target users are non-EU nationals (mostly searching in English), should we run a one-time offline batch job using an LLM to generate rich **English translations \+ common English corporate job titles/jargon** for all 429 SSYK codes before embedding them?  
> 3. **Tech Stack & Hosting Footprint:** Are you envisioning a lightweight, zero-cost static/serverless setup or a containerized microservice architecture?  
   * Given that there are only **429 four-digit SSYK codes**, the entire SCB salary dataset \+ embedded SSYK taxonomy is tiny (a few megabytes). We could easily pre-compute the embeddings and SCB tables into a local DuckDB / SQLite / Qdrant instance or a FastAPI backend, or even run major parts client-side, while querying JobTech's REST API live for current job ads. What stack do you want to build this in?  
> 4. **Scope of the Historical Job Ads Dashboard:** JobTech's historical archive is massive (millions of ads in JSONL/zip dumps per year), whereas their live JobSearch API lets you query current counts and facets dynamically in milliseconds. For the MVP, do you want to ingest and pre-aggregate the multi-year historical dumps by (year, month, ssyk\_4, region) into a lightweight summary table, or start with live market snapshots?  
> 5. **Union & Exception Nuances:** Would you like to include a mapping of **which SSYK codes typically belong to which Saco/TCO/LO union** (e.g., mapping engineering/IT SSYKs to *Sveriges Ingenjörer* / *Unionen*) and flagging which SSYK codes qualify for the **EU Blue Card** or the June 2026 **shortage occupation exemptions**?

**Sources**

> 1. [Nya regler för arbetskraftsinvandring från juni 2026 | EY Sverige](https://www.ey.com/sv_se/insights/tax/nya-regler-for-arbetskraftsinvandring-fran-juni-2026)  
> 2. [Sweden 2026 work permit salary threshold: HR guide \- Zalaris](https://zalaris.com/resources/blog/new-salary-thresholds-for-swedish-work-permits-in-2026-what-changed-on-1-june-and-what-to-do-now)  
> 3. [Genomsnittlig månadslön och lönespridning efter sektor, yrkesgrupp](https://www.statistikdatabasen.scb.se/goto/sv/ssd/LoneSpridSektorYrkAN)  
> 4. [main · Arbetsförmedlingen / Job Ads / jobsearch-apis \- GitLab](https://gitlab.com/arbetsformedlingen/job-ads/jobsearch-apis/-/blob/main/docs/GettingStartedJobSearchEN.md)

---

*User prompt: Excellent, can you create a development plan for this project please, and come up with a name for the project, please\!\! Think about spec-kit, what would we need to decide before we start, talk me through it and ask many short questions if you wish*

## **Response: 1\. Project Name Candidates**

Here are five directions depending on the vibe you want for the repo and UI:

> * **Lönekrav** (lonekrav.se / lonekrav) — *Direct & Authoritative.* Literally "Salary Requirement." Instantly clear to anyone dealing with *Migrationsverket* and *Försörjningskrav*.  
> * **Yrkeskompassen** (yrkeskompassen) — *Navigational.* "The Occupation Compass." Captures the core mechanic of navigating between adjacent SSYK codes to find the safest path.  
> * **Gränslön** (granslon) — *Double Entendre.* Plays on *gräns* (threshold/cutoff *and* border) \+ *lön* (salary). Short, memorable, and punchy for a data product.  
> * **Kodbyten** (kodbyten) — *Clever & Insider.* "Code Switches." A nod to switching between SSYK codes (and code-switching between English corporate titles and Swedish bureaucracy).  
> * **Kravkollen** (kravkollen) — *Accessible Consumer Tool.* Follows the classic Swedish civic-tech naming pattern (*Lönekollen*, *Valmyndigheten* tools). Very approachable.

*(My personal pick for a repo \+ domain is **Gränslön** or **Lönekrav**, with a subtitle like: "The SSYK & Salary Navigator for Swedish Work Permits.")*

## **2\. How spec-kit Structures Our Workflow (and What We Must Decide First)**

GitHub's **Spec Kit** (specify-cli) enforces **Spec-Driven Development (SDD)** so your coding agent doesn't hallucinate architecture or drift across features. When you run specify init, it scaffolds .specify/ (holding your constitution, templates, and feature specs) and .github/ or agent command bindings.

To make Spec Kit sing, we have to feed its four core lifecycle gates in strict order. **Crucially, Spec Kit separates the *What/Why* (/speckit.specify) from the *How* (/speckit.plan):**

| Spec Kit Phase | Artifact Created | What We Need to Decide Before Running It |
| :---- | :---- | :---- |
| **1\. Constitution** (/speckit.constitution) | .specify/memory/constitution.md | **Global project laws:** Repo structure (monorepo vs. single app), testing strictness, data freshness/provenance rules (never hallucinate SCB stats), legal disclaimer rules, and code style/typing standards (e.g., strict Pydantic / TypeScript). |
| **2\. Feature Specs** (/speckit.specify \+ /speckit.clarify) | specs/001-.../spec.md | **Pure behavior & user stories (Zero tech stack details):** Exact inputs, edge cases (part-time math, missing SCB cells ..), visual threshold lines, and acceptance criteria. |
| **3\. Technical Plan** (/speckit.plan) | specs/001-.../plan.md, data-model.md, contracts/ | **The Architecture & Stack:** Frontend framework, backend API, vector \+ lexical search engine, database/storage format, and ETL scripts for SCB \+ JobTechDev. |
| **4\. Task Breakdown** (/speckit.tasks → /speckit.implement) | specs/001-.../tasks.md | **Execution sequence:** Ordered, dependency-aware tasks so the agent builds schemas → data ingestion → endpoints → UI components. |

## **3\. Recommended Feature Breakdown (Our 4 Spec Kit Cycles)**

Rather than feeding the entire app into a single monolithic /speckit.specify prompt (which bloats tasks.md and degrades agent accuracy), we should split the development plan into **4 sequential Spec Kit features**:

### **Feature 001-data-and-taxonomy-pipeline (Foundation & ETL)**

> * **Goal:** Ingest, clean, join, and index the static/semi-static data from SCB and JobTech Taxonomy into a fast local store.  
> * **Deliverables:**  
  1. Reproducible ingestion script pulling SCB AM0110 tables (percentile dispersion by 4-digit SSYK/Sector/Sex \+ age-group means) and handling suppressed values (..).  
  2. Ingestion script pulling the JobTech Taxonomy GraphQL API (occupation-name ↔ ssyk-level-4 mappings, skills, and descriptions).  
  3. Offline LLM enrichment script to generate English translations, common English tech/corporate title synonyms, and union mappings for all 429 SSYK codes.  
  4. Hybrid search index creation (dense embeddings \+ BM25) over the 429 SSYK profiles.

### **Feature 002-legal-guide-and-eligibility-calc (Tier 1 & Tier 2 Explainer)**

> * **Goal:** Interactive legal explainer and instant salary/hours sanity checker.  
> * **Deliverables:**  
  1. Scrollytelling / visual timeline of the Swedish work permit threshold evolution (13,000 SEK → 80% median → June 2026 90% median / 33,390 SEK \+ transitional extension rules).  
  2. Interactive calculator where users enter gross offered salary, FTE percentage (sysselsättningsgrad), and application type (first-time vs. extension before/after Dec 1, 2026\) to see if they clear the statutory floor.

### **Feature 003-ssyk-matcher-and-salary-viz (The Core Arbitrage Engine)**

> * **Goal:** Natural language job search → side-by-side SSYK comparison → SCB salary quantile visualizations.  
> * **Deliverables:**  
  1. Search endpoint & UI accepting free-text English/Swedish job descriptions or titles, returning the top 3–5 candidate 4-digit SSYK codes with match explanations.  
  2. Side-by-side "Arbitrage Matrix" comparing candidate SSYK codes by P10/P25/Median salary, sector, and official SCB duty bullets (highlighting which duties justify a lower-threshold code).  
  3. Salary distribution chart (P10–P90 boxplot/fan) with the 33,390 SEK statutory floor line, the P10–P25 "Union Scrutiny Zone," and age-cohort mean markers (18–24, 25–34, etc.).

### **Feature 004-jobtech-market-pulse (Live & Historical Demand Extension)**

> * **Goal:** Show real-world hiring volume and regional demand for the selected SSYK codes.  
> * **Deliverables:**  
  1. Integration with JobTech's JobSearch API to display currently active job ads and top hiring regions (*Län* / *Kommun*) for the selected SSYK code(s).  
  2. Historical trend chart showing monthly/annual ad volume by SSYK and region.

## **4\. Rapid-Fire Questions to Lock In Our .specify Files**

To draft your constitution.md and the first /speckit.specify \+ /speckit.plan prompts right now, give me quick answers on these:

**A. Project Identity & Coding Agent**

> 1. **Name:** Which of the project names above (or a variation) do you want to go with?  
> 2. **Coding Agent:** Which agent will you bind Spec Kit to when running specify init (e.g., Claude Code, GitHub Copilot, Cursor)?

**B. Technical Stack (For constitution.md & /speckit.plan)** 3\. **Frontend & Viz:** Do you want a decoupled web app (e.g., **Next.js / React / Tailwind** with Observable Plot, Vega-Lite, or Recharts), a Python-native UI (e.g., **Streamlit / Shiny for Python / FastHTML**), or a hybrid **Quarto \+ interactive JS/OJS** setup? 4\. **Backend & Data Store:** Since 429 SSYK codes \+ SCB wage rows total only a few thousand records, do you want a **FastAPI \+ DuckDB/SQLite** backend, **PostgreSQL \+ pgvector**, or **Qdrant** for the hybrid search? 5\. **Embedding Model:** For the bilingual (English/Swedish) SSYK search, do you want a local open-weight multilingual model (e.g., intfloat/multilingual-e5-base or BAAI/bge-m3 running in-container) or an API embedding call (OpenAI / Gemini / Azure)? 6\. **Deployment Target:** Where will this live (e.g., Docker Compose on your own server/VPS, Azure Container Apps, or static/serverless)?

**C. Product & Data Edge Cases (For /speckit.specify & /speckit.clarify)** 7\. **Missing SCB Data (..):** When SCB suppresses the 10th/25th percentile for a tiny SSYK code in a specific sector/gender cut, should the UI automatically fall back to the "All Sectors / Both Sexes" distribution for that SSYK with a warning badge? 8\. **Age Adjustment:** Do you prefer **Option A** (plotting the exact SCB P10–P90 boxplot and overlaying the 25–34 Age Group Mean as a distinct marker) or **Option B** (mathematically scaling an estimated P10–P90 band for the user's age group)? 9\. **Language of the UI:** Should the web interface itself be English-first (with Swedish SSYK titles/codes and legal terms kept alongside in parentheses so users can copy-paste them into *Migrationsverket* forms), or fully bilingual with a language toggle? 10\. **JobTech Historical Scope:** For Feature 004, should we start with a lightweight pre-aggregated summary table of historical ads (year, month, ssyk\_4, lan, ad\_count) \+ live active ads from JobSearch API, rather than hosting raw multi-gigabyte historical JSON dumps?

**Sources**

> 1. [GitHub Spec-Kit: From Vibe Coding to Spec-Driven Development](https://dev.to/petersaktor/github-spec-kit-from-vibe-coding-to-spec-driven-development-1pgd)  
> 2. [GitHub Spec Kit Workflow: A Practical Guide \- Shiplight AI](https://www.shiplight.ai/blog/spec-driven-development-with-spec-kit)

---

*User prompt: Great, lets go with Lönekrav we will use claude code. I want to focus on making the backend super modular and clear, I might even want to make a MCP server for this info, that we can plug in to a chat model. Or look into Agent Communication/Context Protocol (ACP) and see if that might be better here. Everyone knows how to make a web app, perhaps I should demonstrate that I can create a really good ACP system with a fastAPI python inspired backend. Search the web for me. For the frontend, we can build a very simple acp client and use openrouter to supply the llm. I would build that in react I think. But we should be agnostic for the moment on the frontend, research ACP more and inform me. 4\. look at milvus for the vector db, I want to use it. 5\. lets experiment with a multimodal embedding model that works really well, and then a swedish cased bert model https\://huggingface.co/KB/bert-base-swedish-cased. I want to have it quickly calculate the similarieis as the user types in more descriptions of the job. they should easily be able to paste in a linkedin description, it should filter out the company description and look at the role description, this can be a fun additional component of the project. 6\. docer compose for sure, likely as a cloud run on GCP app, or perhaps even locally hosted if we can get it small and compact to run on an old laptop. 7\. yes let's then drop the gender and sector cut, and try and focus on the distributions. 8\. you advise me, maybe let's do both and see what looks better. 9\. UI should be in English, it's for people who are coming from outside of Sweden, and I want to show clearly that the language of input doesn't matter for the similarity search; we should test this. 10\. sure \- lets make this an extension, not core to the project.*

Response: **Lönekrav** is locked in. Building this with a protocol-first FastAPI backend and Milvus multi-vector search makes it a much stronger engineering showcase than a standard CRUD app.

## **1\. Deep-Dive: The "ACP" Landscape in 2026 (And What You Should Build)**

If you search for **ACP** right now, you will hit a classic naming collision across **three completely different protocols**. Understanding this distinction is gold for how you position the repo:

> 1. **Agent Communication Protocol (IBM / BeeAI → Merged into Linux Foundation A2A):**  
   * *What it is:* Launched by IBM Research in early 2025 (acp-sdk) as a RESTful, async-first HTTP protocol for multi-agent orchestration (using standard MIME types and agent manifests at /agents/{name}/run).  
   * *2026 Status:* IBM officially merged ACP into the Linux Foundation's **A2A (Agent2Agent)** standard. While acp-sdk still works and is super clean (FastAPI under the hood), the industry has consolidated around **MCP** for *vertical tool/data access* and **A2A** (or ACP-compatible REST endpoints) for *horizontal agent delegation*.  
> 2. **Agent Client Protocol (Zed / JetBrains / Google):**  
   * *What it is:* The pip install agent-client-protocol standard. It is "LSP for coding agents" (JSON-RPC 2.0 over stdio) so agents like Claude Code, Gemini CLI, or OpenHands can plug into IDEs like Zed or PyCharm. Not meant for web apps.  
> 3. **Model Context Protocol (MCP \- Anthropic / Industry Standard):**  
   * *What it is:* The universal standard for exposing **Data Resources, Prompts, and Tools** (FastMCP) to any LLM client, chat UI, or agent.

### **The Winning Architecture for Lönekrav: The Tri-Headed FastAPI Core**

Because FastAPI makes it trivial to mount sub-applications, you don't have to choose just one. We design a **Pure Python Domain Service** at the center, and expose **three thin protocol adapters** on the same FastAPI server:

> * /api/v1/\* — **High-Speed REST & WebSocket/SSE API:** Powers the real-time keystroke-by-keystroke Milvus similarity search and the React visualizers (since you don't want an LLM roundtrip slowing down a live search bar).  
> * /mcp — **Streamable HTTP MCP Server (FastMCP):** Exposes tools like extract\_role\_from\_job\_ad, search\_ssyk\_hybrid, get\_scb\_salary\_distribution, and evaluate\_work\_permit\_offer. Any MCP client (Claude Desktop, Cursor, or your React chat widget via OpenRouter) can plug straight into it.  
> * /acp (or /a2a) — **Agent Endpoint:** Exposes a stateful "Negotiation & SSYK Strategist Agent" (powered by OpenRouter) that accepts a messy LinkedIn job paste \+ salary offer and autonomously runs the multi-step workflow (strip company fluff → query Milvus across models → check SCB percentiles → return an SSYK arbitrage strategy).

## **2\. Embeddings, Milvus, and the Cross-Lingual Benchmark**

Your idea to test whether input language (English vs. Swedish) affects retrieval quality across models is a fantastic feature. Here is how we engineer it so it runs smoothly on both an old laptop and GCP Cloud Run:

### **Crucial Catch on KB/bert-base-swedish-cased vs. KBLab/sentence-bert-swedish-cased**

> * Base KB/bert-base-swedish-cased is a masked language model (MLM) trained *only* on Swedish text. If you mean-pool its raw token embeddings without sentence-level fine-tuning, cosine similarity degrades—and if a user types in English, it will fail to align with Swedish SSYK descriptions.  
> * However, KBLab also released **KBLab/sentence-bert-swedish-cased**, which was specifically trained using cross-lingual knowledge distillation (*Making Monolingual Sentence Embeddings Multilingual*) to align **Swedish and English sentences into the exact same vector space** (768 dimensions)\!  
> * **What we should do:** In Milvus 2.5+, a single collection supports **Multi-Vector Hybrid Search**. For each of the 429 SSYK codes, we can store **three vector fields** in the same Milvus collection:  
  1. vec\_kblab (768d): From KBLab/sentence-bert-swedish-cased (or raw KB/bert-base-swedish-cased if you specifically want to prove how raw monolingual BERT breaks on English queries compared to distilled models\!).  
  2. vec\_multimodal (768d or 1024d): A modern multilingual/multimodal embedding model (e.g., **Jina Embeddings v3 / CLIP**, **SigLIP**, or **BGE-M3** / Gemini Embedding).  
  3. vec\_sparse (BM25): Built-in Milvus 2.5 sparse BM25 vectors for exact keyword/code hits.  
> * **The UI "Arena" Mode:** As the user types in English or Swedish, the API queries both vector spaces in Milvus simultaneously (taking \<15ms for 429 records) and can optionally toggle or blend (RRF \- Reciprocal Rank Fusion) the results so the user can *see* the cross-lingual robustness live.

### **Running Milvus on an Old Laptop *and* GCP Cloud Run**

Full Milvus Standalone requires etcd \+ MinIO \+ Pulsar/RocksDB (eating 4–6 GB RAM alone). Instead, we use **pymilvus with milvus-lite**:

> * Calling MilvusClient("./data/lonekrav\_milvus.db") embeds the exact same Milvus C++ core directly inside the FastAPI container backed by a local file, using **\<150 MB of RAM**.  
> * Better yet, if you ever scale to a remote Milvus cluster, **zero lines of query code change**—you only change MILVUS\_URI in .env.

## **3\. Two High-Value Features Based on Your Ideas**

### **A. The LinkedIn Job-Ad "Fluff Stripper" (Signal vs. Noise)**

When users paste a 600-word LinkedIn job ad, 60% of it is usually employer branding (*"We are a fast-growing sustainable fintech unicorn in Stockholm with free breakfast and ping-pong..."*) and equal-opportunity boilerplate. If you embed the whole paste, words like *"finance"*, *"food"*, or *"sustainability"* pollute the vector and pull the wrong SSYK codes\!

> * **Fast Local Mode (Real-time as you paste):** We split the pasted text into sentences/paragraphs and score each chunk against a "Role Duty Prototype" vs. "Company Boilerplate Prototype" using our local embedding model (or a fast heuristic/classifier), highlighting the kept role duties in green and striking through the ignored company fluff in gray.  
> * **Deep Agent Mode (via OpenRouter / ACP):** Extracts a structured Pydantic JobRoleProfile(core\_tasks: list\[str\], required\_skills: list\[str\], seniority\_signals: list\[str\], stripped\_company\_noise: list\[str\]) before matching.

### **B. Advice on Question \#8: Visualizing Age-Adjusted Salaries**

Dropping the Sector and Sex cuts makes the UX **10x cleaner** and practically eliminates SCB cell suppression (..)\! Here is my recommendation for **Age**: **Let's combine Option A and Option B on a single chart with a toggle.**

> * **Default View (Empirical Truth):** Show the solid horizontal boxplot for the overall SSYK (P10, P25, Median, P75, P90) alongside the red vertical dashed line at **33,390 SEK** (the 90% statutory floor). Directly on top of that bar, plot the official SCB **Age-Group Mean Markers** (18–24, 25–34, 35–44, 45–54, 55–64) as distinct connected dots.  
> * **Toggle: "Simulate Age-Adjusted Distribution (Experimental)":** When toggled on, we render a second "ghost" boxplot right below the main one, scaling the SSYK's P10–P90 quantiles by the ratio MeanSSYK, All Ages​MeanSSYK, Age *a*​​. That gives a recent graduate (e.g., age 25–34) both the hard official SCB numbers *and* a realistic visual estimate of what the 10th–25th percentile looks like specifically for people their age.

## **4\. The Complete spec-kit Development Plan for Claude Code**

Here is the exact sequence to initialize the project and drive Claude Code through Spec Kit:

### **Step 0: Initialize Spec Kit for Claude Code**

`uvx --from git+https://github.com/github/spec-kit.git specify init lonekrav --ai claude`  
`cd lonekrav`

### **Phase 1: Establish the Project Constitution (/speckit.constitution)**

In Claude Code, run /speckit.constitution with these core principles:

> 1. **Modular Protocol-First Architecture:** All business logic, Milvus retrieval, and SCB salary math must live in a framework-agnostic core package (src/lonekrav/core/). FastAPI REST routes (/api/v1), MCP tools (/mcp), and ACP agent handlers (/acp) must be thin adapters over core.  
> 2. **Strict Data Provenance:** Never fabricate or interpolate SCB salary figures without explicit metadata flags (is\_estimated: bool). Always attach the official SCB reference year and statutory median threshold (37,100 SEK median → 33,390 SEK 90% floor as of June 2026).  
> 3. **Compact & Portable Footprint:** The full stack (FastAPI \+ Milvus Lite \+ local embedding inference \+ React UI) must build via docker compose up and run comfortably within **2 GB RAM** so it works identically on an old laptop and GCP Cloud Run.  
> 4. **Type Safety & Reproducibility:** Python 3.12+, managed via uv, strict pydantic v2 schemas for all internal and external contracts, and pytest unit \+ cross-lingual retrieval evaluation suites.

### **Phase 2: The 4 Sequential Spec Kit Feature Specs**

#### **Feature 001-scb-jobtech-milvus-etl (Data Pipeline & Multi-Vector Index)**

> * **What it builds:**  
  * Python CLI pipeline (uv run lonekrav-etl) that fetches:  
    1. Official SSYK 2012 4-digit titles, task descriptions, and inclusions/exclusions from SCB.  
    2. Mapped job titles (occupation-name), synonyms, and skills from the JobTech Taxonomy API.  
    3. SCB Salary Dispersion (P10, P25, P50, P75, P90, Mean) across all sectors/sexes combined per 4-digit SSYK, plus SCB Mean Salary by 4-digit SSYK × Age Group.  
  * Bilingual synthetic enrichment step (via OpenRouter batch script, cached to JSON in repo) so every 4-digit SSYK has clean English translations and English corporate title equivalents alongside the official Swedish text.  
  * Milvus Lite indexer that embeds every SSYK record using both the Swedish BERT model and the Multimodal/Multilingual embedding model \+ Sparse BM25, saving to a portable lonekrav.db artifact and DuckDB/SQLite for relational salary lookups.  
  * **Cross-Lingual Benchmark Script (tests/eval\_cross\_lingual.py):** Tests 50 paired English/Swedish job descriptions to quantify and prove retrieval parity across languages and compare the two embedding models.

#### **Feature 002-jd-parser-and-hybrid-search (Real-Time Search & LinkedIn Fluff Stripper)**

> * **What it builds:**  
  * **Job Description Signal Extractor:** Takes a raw pasted LinkedIn job ad, classifies sentences into role\_duties vs. company\_boilerplate, and strips the noise before embedding.  
  * **Sub-50ms Real-Time Search Endpoint (POST /api/v1/search):** Accepts partial or full job descriptions as the user types, runs multi-vector similarity search in Milvus (vec\_kblab, vec\_multimodal, vec\_sparse), and returns the top 5 SSYK candidates with per-model similarity scores and matched duty highlights.

#### **Feature 003-mcp-and-acp-agent-server (The Agentic Protocol Layer)**

> * **What it builds:**  
  * **MCP Server (/mcp):** Exposes search\_ssyk, strip\_job\_ad\_boilerplate, get\_ssyk\_salary\_stats, and compare\_ssyk\_arbitrage via FastMCP.  
  * **ACP Agent Server (/acp):** Implements the RESTful Agent Communication Protocol spec (/acp/agents, /acp/agents/lonekrav-advisor/runs) backed by OpenRouter. Given a user's background, a job ad, and a target salary, the agent streams back an interactive SSYK negotiation strategy.

#### **Feature 004-english-web-client (React \+ OpenRouter Frontend)**

> * **What it builds:**  
  * **Section 1: The Visual Legal Explainer:** Interactive breakdown of the June 2026 90% median rule (33,390 SEK), the part-time trap calculator, and how union statements (*yttranden*) work.  
  * **Section 2: Live SSYK Search & LinkedIn Paste Box:** Live keystroke search with an "Embedding Model & Language Arena" badge showing similarity scores from both models in real time, plus visual highlighting of stripped company fluff vs. core role duties.  
  * **Section 3: The Arbitrage & Salary Distribution Visualizer:** Side-by-side SSYK cards with P10–P90 quantile plots, the 33,390 SEK cutoff line, official Age-Group Mean markers, the toggleable Age-Adjusted ghost distribution, and an integrated ACP Chat Drawer powered by OpenRouter.

## **5\. Three Quick Decisions Before I Generate Your Ready-to-Paste Spec Kit Prompts**

> 1. **The Two Embedding Models:**  
   * For the **Swedish BERT slot**, should we use KBLab/sentence-bert-swedish-cased (which is fine-tuned for sentence similarity and Swedish-English alignment) or raw KB/bert-base-swedish-cased (or both, as an experiment)?  
   * For the **Multimodal Embedding slot**, since it needs to run fast on a laptop CPU or Cloud Run as the user types, do you want a compact local multimodal model (like **jinaai/jina-clip-v2** or **google/siglip** which embed both text and images—e.g., if a user uploads a screenshot of a job ad\!), or an API-based multimodal embedding model?  
> 2. **ACP Flavour:**  
   * For the /acp routes, do you want the **RESTful HTTP Agent Communication Protocol** style (GET /acp/agents, POST /acp/runs with streaming SSE events—super clean to consume from React and curl) alongside the /mcp server?  
> 3. **Ready for the Artifacts?**  
   * Once you confirm \#1 and \#2, would you like me to write out the exact **constitution.md** and the **001–004 specification prompts** so you can drop them straight into Claude Code?

**Sources**

> 1. [ACP vs MCP: What's the difference for agentic coding? \- CircleCI](https://circleci.com/blog/acp-vs-mcp-whats-the-difference-for-agentic-coding/)  
> 2. [Agent Communication Protocol (ACP): The HTTP of AI Agents](https://antoniocortes.com/en/2025/07/02/agent-communication-protocol-acp-the-http-of-ai-agents/)  
> 3. [A2A vs. MCP vs. ACP: the protocol war that's costing your team](https://dev.to/alex_aslam/a2a-vs-mcp-vs-acp-the-protocol-war-thats-costing-your-team-months-of-rework-38ga)  
> 4. [Agent Client Protocol (ACP) Explained: ACP vs MCP, Editor ... \- Morph](https://www.morphllm.com/agent-client-protocol)  
> 5. [Run Milvus Lite Locally Milvus v2.5.x documentation](https://milvus.io/docs/v2.5.x/milvus_lite.md)

---

*User prompt: Excellent work, to answer your questions: 1\. lets use the KBLab/sentence-bert-swedish-cased model, as well as a multimodal model that tops the leaderboard and can run lcoally. I don't think we need text and image capability, just text is fine. ​2. sure, sounds good\! 3\. yes, lets get to it\!\!*

Response: Here is the complete **Spec-Kit Execution Blueprint** for **Lönekrav**, including the local embedding pairing and ready-to-paste prompts for Claude Code.

### **The Embedding Pair We Are Locking In**

Since we only need text (not images) and want sub-50ms local CPU inference that fits in a compact Docker container alongside KBLab/sentence-bert-swedish-cased (768d):

> * **Model 1 (Swedish-Centric Distilled BERT):** KBLab/sentence-bert-swedish-cased (\~500 MB, 768d).  
> * **Model 2 (SOTA Multilingual MTEB Leader for Compact Local CPU):** **Qwen/Qwen3-Embedding-0.6B** (\~639 MB, 1024d with Matryoshka dimension scaling down to 768d/512d, Apache 2.0) **OR** **jinaai/jina-embeddings-v3** (570M params, task-specific LoRA adapters for retrieval.query vs. retrieval.passage, 1024d).  
  * *Recommendation:* Let's configure the embedder registry to load **KBLab/sentence-bert-swedish-cased** \+ **Qwen/Qwen3-Embedding-0.6B** (truncated to 768d via Matryoshka representation learning so both dense vectors share the exact same dimensionality in Milvus\!), plus Milvus 2.5's native **Sparse BM25** function. Together, both models take \~1.1 GB of RAM, meaning the entire container runs effortlessly on an old ThinkPad or GCP Cloud Run\!

## **Step 1: Bootstrap the Repo & Spec Kit**

Run this in your terminal to initialize the repository and bind Spec Kit to Claude Code:

`uvx --from git+https://github.com/github/spec-kit.git specify init lonekrav --ai claude`  
`cd lonekrav`  
`claude`

## **Step 2: The Project Constitution (/speckit.constitution)**

Paste this directly into Claude Code to establish .specify/memory/constitution.md:

`/speckit.constitution Establish the constitution for "Lönekrav" (The SSYK & Salary Navigator for Swedish Work Permits) with these non-negotiable architectural and product principles:`

`1. Domain-Driven Protocol-First Architecture:`  
   ``- All core domain logic, SCB statistical transformations, job-ad noise filtering, and Milvus vector search MUST live in a framework-agnostic Python package (`src/lonekrav/core/`).``  
   ``- Expose three thin protocol adapters over `core` mounted on a single FastAPI application:``  
     ``a) `/api/v1/*`: High-speed REST & SSE endpoints for sub-50ms live search, linked-in paste parsing, and salary quantile visualization.``  
     ``b) `/mcp`: A Model Context Protocol server (`FastMCP` over Streamable HTTP) exposing tools and resources for external LLM clients.``  
     ``c) `/acp`: A RESTful Agent Communication Protocol server (`/acp/agents`, `/acp/runs` with SSE streaming) powered by OpenRouter for multi-step SSYK negotiation strategy.``

`2. Multi-Vector Milvus Architecture & Compact Footprint:`  
   ``- Use `pymilvus` with `milvus-lite` (`./data/lonekrav_milvus.db`) by default so the entire stack runs without external etcd/MinIO dependencies, while supporting remote Milvus via a single `MILVUS_URI` env var.``  
   `- Every 4-digit SSYK record in Milvus MUST store three vector representations:`  
     ``a) `vec_kblab` (768d float32): Generated locally by `KBLab/sentence-bert-swedish-cased`.``  
     ``b) `vec_sota` (768d float32): Generated locally by `Qwen/Qwen3-Embedding-0.6B` (using Matryoshka 768d output) or `jinaai/jina-embeddings-v3`.``  
     ``c) `vec_bm25` (Sparse): Milvus built-in BM25 lexical vector over bilingual titles, descriptions, and JobTech keywords.``  
   `- Total runtime memory of the Docker container (FastAPI + Milvus Lite + dual local embedding models) MUST stay under 2.5 GB RAM to run on a budget laptop or GCP Cloud Run.`

`3. Strict SCB & Legal Data Integrity:`  
   `- Never fabricate or silently interpolate official Statistics Sweden (SCB) salary figures.`  
   `- Drop gender and sector stratifications to maximize cell coverage across all 429 4-digit SSYK codes.`  
   `- Always store and return both:`  
     ``a) Official SCB Empirical Percentiles (`p10`, `p25`, `p50`, `p75`, `p90`, `mean`) for each 4-digit SSYK across all sectors/sexes.``  
     ``b) Official SCB Age-Group Means (`18-24`, `25-34`, `35-44`, `45-54`, `55-64`) per 4-digit SSYK.``  
     ``c) Computed Age-Adjusted Simulated Quantiles (scaling `[p10..p90]` by `age_group_mean / overall_mean`), explicitly flagged with `is_simulated: true`.``  
   ``- Maintain an explicit `LegalConstants` registry tracking Sweden's work permit thresholds over time, anchored to the June 1, 2026 rule: 90% of Sweden's median salary (37,100 SEK median -> 33,390 SEK absolute gross monthly minimum, non-prorated for part-time work).``

`4. Code Quality, Tooling & Testing:`  
   ``- Python 3.12+ managed strictly with `uv`, strict `pydantic` v2 models for every boundary, `ruff` for linting/formatting, and `pytest` for unit and cross-lingual retrieval benchmarks.``  
   `- Frontend in React + TypeScript + Vite + Tailwind CSS, communicating strictly via typed API/ACP contracts.`

## **Step 3: Feature Cycle 1 — Data Pipeline, Dual Embeddings & Cross-Lingual Eval**

Spec Kit requires separating **What/Why** (/speckit.specify) from **How** (/speckit.plan). Paste these two commands in sequence for Feature 001:

### **3A. Run /speckit.specify for Feature 001**

``/speckit.specify Build the data ingestion, bilingual enrichment, multi-vector indexing pipeline, and cross-lingual retrieval benchmark for Lönekrav (`001-data-and-milvus-index`).``

`User & System Stories:`  
``1. Complete 4-Digit SSYK 2012 Catalog: The system must ingest all ~429 4-digit SSYK 2012 occupations from SCB and the JobTech Taxonomy API, capturing official Swedish titles, official task descriptions, inclusion/exclusion notes, and JobTech specific job title synonyms (`occupation-name`) and skill keywords.``  
`2. Bilingual English Enrichment: Because target users are non-EU job seekers searching primarily in English, every 4-digit SSYK record must be enriched with an accurate English title, translated task descriptions, and 10-15 common English corporate/tech job titles (e.g., mapping "Data Scientist", "ML Engineer", "Quantitative Analyst" to their respective SSYK codes) cached cleanly as a versioned JSON artifact in the repo.`  
``3. SCB Salary Distributions & Age Means: The system must pull the latest annual SCB salary dispersion data (`p10`, `p25`, `p50`, `p75`, `p90`, `mean`) per 4-digit SSYK (aggregated across sectors and sexes to minimize suppressed `..` cells) alongside SCB mean salary by 4-digit SSYK and Age Group (`18-24`, `25-34`, `35-44`, `45-54`, `55-64`). Where an age group mean or percentile is suppressed (`..`), record it as `null` and flag fallback behavior explicitly.``  
``4. Dual-Model + BM25 Milvus Indexing: Index all 429 SSYK profiles into a portable Milvus Lite database containing two dense vectors (`KBLab/sentence-bert-swedish-cased` and `Qwen/Qwen3-Embedding-0.6B`) plus a sparse BM25 vector.``  
`5. Cross-Lingual Parity Benchmark: Provide an automated evaluation suite of 40 paired English and Swedish job queries (ranging from short titles to multi-sentence role descriptions) that measures Recall@1, Recall@5, and Mean Reciprocal Rank (MRR) across both models and proves language-agnostic retrieval parity.`

### **3B. Run /speckit.plan for Feature 001**

``/speckit.plan Implement Feature 001 using Python 3.12 and `uv`:``  
``- Create CLI entrypoints (`uv run lonekrav-etl fetch`, `enrich`, `index`, `benchmark`).``  
``- Use `httpx` to query the SCB PxWeb API v1/v2 (`AM0110` tables for 4-digit SSYK wage dispersion and age-stratified means) and JobTech Taxonomy GraphQL API (`https://taxonomy.api.jobtechdev.se/v1/taxonomy/graphql`).``  
``- Use OpenRouter (`OPENROUTER_API_KEY`) in a repeatable, idempotent batch script to generate the English SSYK translations and corporate job title synonyms, saving the canonical enriched dataset to `data/processed/ssyk_2012_enriched.json`.``  
``- Store structured relational salary stats and age-cohort scaling ratios in SQLite/DuckDB (`data/lonekrav_stats.ddb`) or directly in Milvus scalar metadata fields so lookups require zero joins at query time.``  
``- Build `src/lonekrav/core/embeddings.py` to load both `KBLab/sentence-bert-swedish-cased` and `Qwen/Qwen3-Embedding-0.6B` via `sentence-transformers` with L2 normalization and 768-dimension output.``  
``- Build `src/lonekrav/core/milvus_store.py` using `pymilvus.MilvusClient` (`./data/lonekrav_milvus.db`) with a unified collection `ssyk_2012` supporting single-model search (`kblab` vs `qwen3`), sparse `bm25`, and Reciprocal Rank Fusion (`RRF`) hybrid search.``  
``- Output the cross-lingual benchmark results as both a terminal table and a JSON artifact (`data/processed/benchmark_results.json`) that the frontend can later display to prove language independence.``

*(After running /speckit.plan, run /speckit.tasks and /speckit.implement to let Claude Code build and test Feature 001).*

## **Step 4: Feature Cycle 2 — LinkedIn "Fluff Stripper" & Real-Time Search Core**

### **4A. Run /speckit.specify for Feature 002**

``/speckit.specify Build the Job Description Signal Extractor ("LinkedIn Fluff Stripper"), the Salary & Eligibility Domain Calculator, and the real-time FastAPI search endpoints (`002-jd-parser-and-search-api`).``

`User & System Stories:`  
`1. LinkedIn Job Ad Signal vs. Noise Filtering: When a user pastes a raw LinkedIn or corporate job description (in English or Swedish), the system must segment the text and classify segments into Core Role Duties & Skills (Signal) versus Company Branding, Perks, & EEO Boilerplate (Noise). The API must return the annotated segments so the UI can visually highlight kept role duties and strike through ignored company fluff, preventing company industry buzzwords (e.g., "sustainable food delivery unicorn") from polluting the SSYK vector match.`  
``2. Live Keystroke Similarity Search & Model Arena: As a user types or edits a job description, the system must return the Top 5 matching 4-digit SSYK codes in under 50ms, returning individual similarity scores from Model A (`KBLab/sentence-bert-swedish-cased`), Model B (`Qwen3-Embedding-0.6B`), Sparse BM25, and the fused RRF rank.``  
``3. SSYK Arbitrage Comparison & Dual Age Distributions: For any set of candidate SSYK codes and an optional user age bracket (e.g., `25-34`), gross salary offer, and FTE percentage (`sysselsättningsgrad`), the system must return:``  
   `- Whether the offer passes Tier 1 (the absolute 33,390 SEK/month 90% median statutory floor as of June 1, 2026, warning explicitly if part-time hours pull actual monthly pay below 33,390 SEK).`  
   `- How the offer compares against Tier 2 (the SSYK's empirical P10, P25, Median, P75, P90 distribution).`  
   ``- Both Age Visualizations: (Option A) Official SCB age-group mean markers overlaid on the empirical boxplot, and (Option B) Simulated Age-Adjusted quantiles (`P10_age` .. `P90_age`) scaled by `Mean(SSYK, Age) / Mean(SSYK, All)`.``  
   `- An "Arbitrage Diff" highlighting which adjacent SSYK code has a lower entry-level (P10/P25) salary benchmark while still matching the user's core duties.`

### **4B. Run /speckit.plan for Feature 002**

``/speckit.plan Implement Feature 002 in `src/lonekrav/core/` and `src/lonekrav/api/`:``  
``- Implement a fast, zero-LLM-latency local heuristic + embedding prototype classifier in `src/lonekrav/core/fluff_stripper.py` that splits pasted job ads into sentences/bullet points and compares them against pre-computed "Role Duty/Skill" vs. "Employer Branding/Benefits/Boilerplate" anchor vectors using the loaded local embedding model (completing in <15ms on CPU).``  
``- Create `src/lonekrav/core/arbitrage.py` to compute Tier 1 eligibility (historical and current June 2026 90% median rules, transitional extension rules) and Tier 2 quantile positioning (both Empirical + Age-Cohort Mean overlay and Simulated Age-Adjusted Quantiles).``  
``- Expose FastAPI REST routes under `/api/v1/`:``  
  ``- `POST /api/v1/parse-job-ad`: Returns annotated text spans (`keep: bool`, `category: "role_duty" | "skill" | "company_fluff" | "benefits"`).``  
  ``- `POST /api/v1/search`: Accepts query text, optional `strip_fluff: bool`, and returns Top-K SSYK matches with per-model similarity scores (`score_kblab`, `score_qwen3`, `score_bm25`, `score_rrf`) plus full salary distributions.``  
  ``- `POST /api/v1/compare`: Accepts 2-5 SSYK codes, user age group, offered salary, and FTE % to generate a structured side-by-side arbitrage matrix.``  
  ``- `GET /api/v1/legal-timeline`: Returns structured historical and current statutory thresholds and rules.``  
  ``- `GET /api/v1/benchmark`: Returns the pre-computed cross-lingual evaluation metrics from Feature 001.``

## **Step 5: Feature Cycle 3 — The MCP & ACP Agent Server**

### **5A. Run /speckit.specify for Feature 003**

``/speckit.specify Build the Model Context Protocol (`/mcp`) server and the RESTful Agent Communication Protocol (`/acp`) server backed by OpenRouter (`003-mcp-and-acp-protocols`).``

`User & System Stories:`  
``1. Plug-and-Play MCP Server: Any MCP-compatible client (Claude Desktop, Claude Code, Cursor, or custom clients) must be able to connect to `/mcp` to search SSYK codes, strip job ad fluff, inspect SCB salary distributions, and evaluate work permit salary offers using deterministic tools.``  
``2. Stateful ACP Negotiation Strategist Agent: Frontend clients or external orchestrators must be able to discover the `lonekrav-strategist` agent via `GET /acp/agents` and invoke stateful or streaming runs via `POST /acp/runs`.``  
`3. Agentic SSYK Arbitrage Workflow: When a user sends a raw job ad, their background/age, and a proposed salary to the ACP agent, the agent must autonomously invoke the domain tools (strip fluff -> run multi-vector search -> compare SSYK salary distributions -> check union/P10 benchmarks) and stream back:`  
   `- Structured tool-call events (so the UI can automatically update the charts and SSYK cards on screen as the agent thinks!).`  
   ``- A tailored negotiation and contract-framing memo explaining which 4-digit SSYK code gives them the safest margin above P10/P25 and which official SCB task descriptions their employer should emphasize on the Migrationsverket employment offer (`Anställningserbjudande`).``

### **5B. Run /speckit.plan for Feature 003**

``/speckit.plan Implement Feature 003 in `src/lonekrav/protocols/`:``  
``- Build `src/lonekrav/protocols/mcp_server.py` using `FastMCP` mounted at `/mcp` on the main FastAPI app, exposing 5 strongly-typed tools wrapping `lonekrav.core`: `search_occupations`, `extract_job_ad_signal`, `get_occupation_salary_stats`, `evaluate_permit_eligibility`, and `compare_ssyk_arbitrage`.``  
``- Build `src/lonekrav/protocols/acp_server.py` implementing the RESTful Agent Communication Protocol endpoints:``  
  ``- `GET /acp/agents`: Returns the JSON manifest for `lonekrav-strategist` (capabilities, input/output schemas, supported MIME types).``  
  ``- `POST /acp/runs` & `GET /acp/runs/{run_id}/events`: Supports both synchronous JSON responses and Server-Sent Events (`text/event-stream`) streaming.``  
``- Implement the agent loop using the OpenAI-compatible async client pointed at OpenRouter (`https://openrouter.ai/api/v1`, configurable default model e.g. `anthropic/claude-3.7-sonnet` or `google/gemini-2.5-flash`), binding the exact same core domain tools and emitting structured ACP event frames (`agent.thought`, `agent.tool_call`, `agent.ui_sync`, `agent.message.delta`, `agent.run.completed`).``

## **Step 6: Feature Cycle 4 — The English React Web Client & Docker Packaging**

### **6A. Run /speckit.specify for Feature 004**

``/speckit.specify Build the English-first React web application and compact Docker Compose packaging for Lönekrav (`004-react-acp-web-client`).``

`User & System Stories:`  
``1. Interactive Legal Guide & Part-Time Trap Calculator: Clear visual timeline of Sweden's work permit salary rules (13,000 SEK -> Nov 2023 80% median -> June 2026 90% median / 33,390 SEK) and an interactive calculator where users adjust gross salary and FTE % (`sysselsättningsgrad`) to immediately see how part-time work interacts with the non-prorated 33,390 SEK floor.``  
`2. Live Multi-Vector Search & LinkedIn Paste Studio:`  
   `- Instant debounced search as the user types in English or Swedish.`  
   `- When pasting a full LinkedIn job ad, toggleable "Signal vs. Fluff View" that highlights extracted role duties in green and dims stripped company boilerplate.`  
   ``- Live "Cross-Lingual Embedding Arena" bar showing similarity scores from `KBLab Swedish SBERT` vs. `Qwen3-Embedding` vs. `BM25` side-by-side, plus a modal displaying the benchmark proof that query language does not degrade retrieval.``  
`3. Salary Distribution & Arbitrage Visualizer:`  
   ``- Interactive horizontal quantile chart (`P10`, `P25`, `Median`, `P75`, `P90`) comparing up to 4 selected SSYK codes side-by-side.``  
   ``- Vertical reference line at `33,390 SEK` (90% Median Statutory Floor) and shaded `P10-P25` "Union Scrutiny Zone".``  
   `- View Switcher allowing the user to view (A) Empirical Boxplot + Official Age-Group Mean dots, (B) Simulated Age-Adjusted Boxplot for their selected age bracket, or (C) Both overlaid.`  
``4. Integrated ACP Strategist Drawer: An interactive chat/strategy panel connected to `/acp/runs` where the agent can analyze the user's pasted job ad, recommend the optimal SSYK arbitrage code, and dynamically update the selected SSYK codes on the main chart via `agent.ui_sync` events.``

### **6B. Run /speckit.plan for Feature 004**

``/speckit.plan Implement Feature 004 in `frontend/` and root Docker files:``  
``- Scaffold `frontend/` with Vite + React 19 + TypeScript + Tailwind CSS + Lucide icons.``  
`- Build a custom SVG/Canvas or Recharts/Visx Horizontal Quantile & Age Overlay plot that cleanly renders the P10-P90 boxplot, the 33,390 SEK vertical threshold line, the P10-P25 shaded union zone, the connected Age-Group Mean markers, and the toggleable ghost boxplot for the simulated age-adjusted distribution.`  
``- Build a clean TypeScript `ACPClient` in `frontend/src/lib/acpClient.ts` that consumes `POST /acp/runs` via `fetch` + `ReadableStream` SSE parsing and dispatches `agent.ui_sync` payloads directly to the React state store so the agent can control the comparison dashboard.``  
``- Create a multi-stage `Dockerfile` and `docker-compose.yml` that pre-downloads the two HuggingFace embedding models during image build (or mounts a persistent cache volume), serves the compiled React static bundle via FastAPI or Nginx, and runs on a single command (`docker compose up --build`) within a 2.5 GB memory limit for seamless local laptop or GCP Cloud Run deployment.``

### **Pro-Tip Before You Hit Enter on Step 3**

When you run specify init lonekrav \--ai claude, Spec Kit will create .claude/commands/speckit.\*.md.

> 1. Run /speckit.constitution first.  
> 2. Then run /speckit.specify → /speckit.clarify (if you want Claude to ask edge-case checks) → /speckit.plan → /speckit.tasks → /speckit.implement for **Feature 001** before starting Feature 002\. That keeps each context window razor-sharp and guarantees your SCB \+ JobTech \+ Milvus foundation is verified before a single line of UI code is written.

**Sources**

> 1. [Jina Embeddings v3: A Frontier Multilingual Embedding Model](https://jina.ai/news/jina-embeddings-v3-a-frontier-multilingual-embedding-model/)

---

