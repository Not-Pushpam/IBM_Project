# AI Financial Literacy Assistant for Students

A beginner-friendly web application that helps college students understand and manage
their personal finances. Built with Python, OOP principles, Streamlit, and pytest.

---

## Features

| Section | What it does |
|---|---|
| 🏠 Dashboard | Set monthly income & budget, view at-a-glance summary |
| 📋 Budget & Expenses | Add/delete expenses by category, export/import CSV |
| 📊 Spending Analysis | Category chart, spending observations, personalised tips |
| 🤔 Can I Afford This? | Check whether an item fits your remaining budget |
| 🏦 Loan Basics | EMI calculator + plain-English glossary of loan terms |
| 🏅 Scholarships & Aid | General guidance on scholarships and financial aid |
| 🤖 AI Advisor | Ask financial-literacy questions; AI API or built-in fallback |

---

## Project Structure

```
financial_assistant/
├── app.py                          # Streamlit UI entry point
├── constants.py                    # ExpenseCategory enum, thresholds, DISCLAIMER
├── exceptions.py                   # Custom exception classes
├── models/
│   ├── expense.py                  # Expense dataclass
│   └── budget_profile.py           # BudgetProfile dataclass
├── logic/
│   ├── budget_manager.py           # Income/budget management
│   ├── expense_tracker.py          # Add/list/total expenses
│   ├── spending_analyzer.py        # Category analysis & observations
│   └── affordability_checker.py   # "Can I afford this?" logic
├── advisor/
│   ├── loan_calculator.py          # EMI formula + educational explanation
│   ├── financial_advisor.py        # Keyword Q&A + optional AI API
│   └── tips_engine.py              # Personalised tips from user data
├── storage/
│   └── expense_repository.py       # CSV persistence + in-memory store
├── tests/
│   ├── conftest.py                 # Shared pytest fixtures
│   ├── test_budget_manager.py
│   ├── test_expense_tracker.py
│   ├── test_spending_analyzer.py
│   ├── test_affordability_checker.py
│   └── test_loan_calculator.py
└── requirements.txt
```

---

## Installation

### 1. Clone or download the project

```bash
git clone <repo-url>
cd <repo-folder>
```

### 2. (Recommended) Create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r financial_assistant/requirements.txt
```

---

## Running the Application

```bash
streamlit run financial_assistant/app.py
```

The app will open in your browser at **http://localhost:8501**.

---

## Running the Tests

```bash
python -m pytest financial_assistant/tests/ -v
```

Expected output: **75 passed**.

---

## AI API Configuration (Optional)

By default the app uses a built-in rule-based educational advisor that works with
**no configuration**. To connect a real AI API, set these environment variables
**before** starting the app:

### OpenAI

```bash
# Windows PowerShell
$env:AI_PROVIDER = "openai"
$env:AI_API_KEY  = "sk-..."
streamlit run financial_assistant/app.py
```

```bash
# macOS / Linux
AI_PROVIDER=openai AI_API_KEY=sk-... streamlit run financial_assistant/app.py
```

### IBM watsonx.ai

```bash
AI_PROVIDER=watsonx
AI_API_KEY=<your-ibm-api-key>
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_PROJECT_ID=<your-project-id>
```

Install the optional SDK first:

```bash
pip install ibm-watsonx-ai
```

> **Never hard-code API keys in source files.**

---

## Data Persistence

- Expenses and the budget profile are automatically saved to `financial_assistant/data/`
  as CSV files (`expenses.csv`, `profile.csv`).
- Data is loaded back when you restart the application.
- Use the **Download Expenses as CSV** button on the Budget & Expenses page to export
  your data for backup or use in a spreadsheet.

---

## Limitations & Potential v2 Features

| Limitation | Potential improvement |
|---|---|
| Single user — no login | Add user accounts with a database backend |
| Session-scoped in-memory store | Replace `st.cache_resource` with a proper DB for multi-user support |
| Keyword-only AI fallback | Integrate a more capable LLM for richer answers |
| No recurring expenses | Auto-add fixed monthly expenses (rent, subscriptions) |
| Single currency display | Add live currency conversion via an exchange-rate API |
| No budget history | Store monthly snapshots to show spending trends over time |

---

## Disclaimer

This application is for **educational and financial-literacy purposes only**.
It does not constitute professional financial advice. Always consult a qualified
financial advisor before making important financial decisions.
