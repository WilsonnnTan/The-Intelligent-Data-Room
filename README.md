# The Intelligent Data Room

A multi-agent web application that allows users to upload data files and "talk" to their data using natural language. The system uses a Planner-Executor agent architecture powered by Google Gemini via LiteLLM proxy and PandasAI.

**Live Demo:** [https://the-intelligent-data-room.streamlit.app/](https://the-intelligent-data-room.streamlit.app/)

---

## Features

- **Data Upload** - Support for CSV and XLSX files (Max 10MB)
- **Natural Language Queries** - Ask questions about your data in plain English
- **Multi-Agent Architecture** - Planner + Executor agents working together
- **Auto Chart Generation** - PandasAI automatically generates visualizations
- **Context Memory** - Remembers last 5 messages for follow-up questions
- **Execution Plan Display** - See how the AI plans to answer your question

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│                      (Streamlit Web App)                            │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                                 │
│              (Coordinates agents and manages state)                 │
└───────────┬─────────────────────────────────────┬───────────────────┘
            │                                     │
            ▼                                     ▼
┌─────────────────────────┐         ┌─────────────────────────────────┐
│     PLANNER AGENT       │         │        EXECUTOR AGENT           │
│                         │         │                                 │
│ - Analyzes question     │         │ - Receives execution plan       │
│ - Reads data schema     │   ───►  │ - Uses PandasAI + Gemini        │
│ - Creates execution     │         │ - Generates charts (PNG)        │
│   plan with steps       │         │ - Returns answer + visuals      │
│ - Determines chart type │         │                                 │
└─────────────────────────┘         └─────────────────────────────────┘
            │                                     │
            │         ┌───────────────┐           │
            └────────►│ MEMORY MODULE │◄──────────┘
                      │ (Last 5 msgs) │
                      └───────────────┘
```

### Flow

1. User uploads a CSV/XLSX file
2. User asks a question in natural language
3. **Planner Agent** analyzes the question and creates an execution plan
4. **Executor Agent** uses PandasAI to execute the plan on the data
5. Charts are auto-generated and displayed alongside the answer

---

## Tech Stack

| Component     | Technology                        |
| ------------- | --------------------------------- |
| Frontend/UI   | Streamlit                         |
| AI/LLM        | Google Gemini (via LiteLLM proxy) |
| Data Analysis | PandasAI, Pandas                  |

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/The-Intelligent-Data-Room.git
cd The-Intelligent-Data-Room
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```env
LITELLM_API_KEY=your_api_key_here
LITELLM_API_BASE=https://your-litellm-proxy.com/v1
```

### 3. Run

```bash
streamlit run src/app.py
```

---

## Project Structure

```
The-Intelligent-Data-Room/
├── src/
│   ├── app.py                 # Main Streamlit application
│   ├── agents/
│   │   ├── planner.py         # Planner Agent - creates execution plans
│   │   ├── executor.py        # Executor Agent - runs plans with PandasAI
│   │   └── orchestrator.py    # Coordinates agents and manages state
│   └── utils/
│       ├── memory.py          # Conversation memory
│       └── data_loader.py     # CSV/XLSX file handling
├── exports/
│   └── charts/                # Auto-generated chart images
├── requirements.txt
└── README.md
```

---

## Sample Prompts

- "Create a bar chart showing total Sales by Category"
- "What are the top 5 products by profit?"
- "Show the sales trend over time"
- "Which region has the highest revenue?"
- "Create a scatter plot of Discount vs Profit"

---

## License

MIT License
