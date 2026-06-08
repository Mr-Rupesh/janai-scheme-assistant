# JanAI — Government Scheme Assistant
### सरकारी योजना सहायक

A bilingual AI assistant that helps Indian citizens discover and understand government schemes they are eligible for. Built with a dual retrieval approach — rule-based eligibility filtering combined with a RAG pipeline for natural language queries.

---

## Overview

JanAI solves a real problem: most people don't know which government schemes they qualify for, or how to apply. The app takes a user's profile (age, income, state, occupation, gender) and finds matching schemes instantly — then lets them ask free-text questions answered by an LLM with semantic search.

**Key highlights:**

- Dual retrieval — hard eligibility filter on profile data + FAISS vector search for open-ended questions
- Bilingual UI — full English and Hindi support, including LLM prompts and responses
- Rule-based matching on age, income brackets (EWS/LIG/MIG), gender, and occupation
- RAG pipeline: question → semantic search over scheme database → DeepSeek-V3 generates a grounded answer
- Direct apply links to official government portals for each scheme
- Three interaction modes: personalized scheme matching, free-text Q&A, and a browsable scheme catalog

---

## Tech Stack

- **Framework:** Streamlit
- **LLM:** DeepSeek-V3.2 via HuggingFace Endpoint
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Store:** FAISS
- **RAG Orchestration:** LangChain (core, community, HuggingFace)
- **Scheme Data:** Custom `schemes.json` with real government scheme details

---

## How It Works

```
User Profile (age, income, state, gender, occupation)
        ↓
Rule-Based Eligibility Filter (schemes.json)
        ↓
Matching schemes with reasons + documents + apply links
        
─────────────────────────────────────────────────────

User Question (free text, English or Hindi)
        ↓
FAISS Semantic Search → top 3 relevant scheme chunks
        ↓
Prompt with context → DeepSeek-V3
        ↓
Grounded answer with scheme names and benefits
```

---

## Schemes Covered

Includes real data for schemes across categories:

| Category | Examples |
|---|---|
| Housing | Pradhan Mantri Awas Yojana (PMAY) |
| Health | Ayushman Bharat PM-JAY |
| Agriculture | PM-KISAN Samman Nidhi |
| Financial Inclusion | PM Jan Dhan Yojana |
| Energy | PM Ujjwala Yojana |
| MSME / Loans | PM Mudra Yojana |
| Pension | Atal Pension Yojana |
| Girl Child | Sukanya Samriddhi Yojana |

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Mr-Rupesh/janai-scheme-assistant.git
cd janai-scheme-assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure secrets

Create a `.streamlit/secrets.toml` file:

```toml
HUGGINGFACEHUB_API_TOKEN = "your-huggingface-token"
```

Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

### 4. Run the app

```bash
streamlit run app.py
```

---

## Usage

**Find Schemes tab** — Fill in your profile in the sidebar (age, income, state, occupation, gender) and click *Find My Schemes*. The app shows every scheme you qualify for, why you qualify, required documents, and a direct apply link.

**Ask Questions tab** — Type any question in English or Hindi (e.g. *"What schemes are available for farmers?"*). The RAG pipeline retrieves the most relevant schemes and the LLM generates a clear answer.

**Browse All tab** — Filter schemes by category and explore the full database.

---

## Contact

**Rupesh Malhipparge** — [rupeshmalhipparge@gmail.com](mailto:rupeshmalhipparge@gmail.com)
