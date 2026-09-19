"""
app.py — Streamlit entry point for the AI Financial Literacy Assistant.

Run with:
    streamlit run app.py

Design principle
----------------
This file contains ONLY Streamlit UI code (st.* calls, forms, buttons, display).
All business calculations live in the logic/ and advisor/ packages.
Exceptions from those packages are caught here and shown as friendly messages.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Make the project importable when running from the repo root
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))

from financial_assistant.advisor.financial_advisor import FinancialAdvisor
from financial_assistant.advisor.loan_calculator import LoanCalculator
from financial_assistant.advisor.tips_engine import TipsEngine
from financial_assistant.constants import CURRENCY_OPTIONS, ExpenseCategory
from financial_assistant.exceptions import (
    BudgetNotSetError,
    EmptyExpenseListError,
    InvalidAmountError,
    InvalidCategoryError,
    InvalidLoanParameterError,
)
from financial_assistant.logic.affordability_checker import AffordabilityChecker
from financial_assistant.logic.budget_manager import BudgetManager
from financial_assistant.logic.expense_tracker import ExpenseTracker
from financial_assistant.logic.spending_analyzer import SpendingAnalyzer
from financial_assistant.storage.expense_repository import ExpenseRepository

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Financial Literacy Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Shared service instances (cached for the session)
# ---------------------------------------------------------------------------

@st.cache_resource
def get_services():
    """Create and cache all service instances once per Streamlit session."""
    repo = ExpenseRepository()
    return {
        "repo": repo,
        "budget_manager": BudgetManager(repo),
        "expense_tracker": ExpenseTracker(repo),
        "spending_analyzer": SpendingAnalyzer(repo),
        "affordability_checker": AffordabilityChecker(repo),
        "loan_calculator": LoanCalculator(),
        "financial_advisor": FinancialAdvisor(),
        "tips_engine": TipsEngine(),
    }


svc = get_services()
bm: BudgetManager = svc["budget_manager"]
et: ExpenseTracker = svc["expense_tracker"]
sa: SpendingAnalyzer = svc["spending_analyzer"]
ac: AffordabilityChecker = svc["affordability_checker"]
lc: LoanCalculator = svc["loan_calculator"]
fa: FinancialAdvisor = svc["financial_advisor"]
te: TipsEngine = svc["tips_engine"]

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.title("💰 Financial Assistant")
st.sidebar.caption("Your beginner-friendly money guide")
st.sidebar.markdown("---")

PAGES = [
    "🏠 Dashboard",
    "📋 Budget & Expenses",
    "📊 Spending Analysis",
    "🤔 Can I Afford This?",
    "🏦 Loan Basics",
    "🏅 Scholarships & Aid",
    "🤖 AI Financial Advisor",
]
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")

# AI status indicator in sidebar
if fa.is_ai_api_active():
    provider = os.getenv("AI_PROVIDER", "").upper()
    st.sidebar.success(f"✅ AI API active ({provider})")
else:
    st.sidebar.info("🔧 Using built-in rule-based advisor")

st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ This app is for educational purposes only. "
    "It does not provide professional financial advice."
)


# ===========================================================================
# Helper: currency symbol from stored profile (or default $)
# ===========================================================================

def _sym() -> str:
    try:
        return bm.get_profile().currency_symbol
    except BudgetNotSetError:
        return "$"


# ===========================================================================
# PAGE 1 — Dashboard
# ===========================================================================

if page == "🏠 Dashboard":
    st.title("🏠 Dashboard")
    st.markdown(
        "Welcome! Start by entering your **monthly income** and **budget** below, "
        "then add your expenses to track your spending."
    )

    # ------------------------------------------------------------------
    # Profile setup form
    # ------------------------------------------------------------------
    st.subheader("Set Your Monthly Budget")

    with st.form("profile_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            currency_label = st.selectbox(
                "Currency", list(CURRENCY_OPTIONS.keys()), index=0
            )
        with col2:
            income = st.number_input(
                "Monthly Income / Available Money",
                min_value=0.0,
                value=0.0,
                step=50.0,
                format="%.2f",
                help="Your total money available this month (salary, allowance, stipend…)",
            )
        with col3:
            budget = st.number_input(
                "Monthly Budget (spending limit)",
                min_value=0.0,
                value=0.0,
                step=50.0,
                format="%.2f",
                help="The maximum you plan to spend this month",
            )
        submitted = st.form_submit_button("💾 Save Profile", use_container_width=True)

    if submitted:
        try:
            sym = CURRENCY_OPTIONS[currency_label]
            bm.set_profile(income, budget, sym)
            st.success(
                f"✅ Profile saved! Income: {sym}{income:,.2f} | Budget: {sym}{budget:,.2f}"
            )
            if bm.budget_exceeds_income():
                st.warning(
                    f"⚠️ Your budget ({sym}{budget:,.2f}) exceeds your declared income "
                    f"({sym}{income:,.2f}). Make sure this is intentional."
                )
        except InvalidAmountError as e:
            st.error(f"❌ {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

    # ------------------------------------------------------------------
    # Summary cards
    # ------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📈 This Month at a Glance")

    try:
        profile = bm.get_profile()
        total_spent = et.get_total_spent()
        remaining = bm.get_remaining_budget(total_spent)
        sym = profile.currency_symbol

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Monthly Income", f"{sym}{profile.monthly_income:,.2f}")
        c2.metric("Monthly Budget", f"{sym}{profile.monthly_budget:,.2f}")
        c3.metric(
            "Total Spent",
            f"{sym}{total_spent:,.2f}",
            delta=f"-{sym}{total_spent:,.2f}" if total_spent > 0 else None,
            delta_color="inverse",
        )
        c4.metric(
            "Remaining Budget",
            f"{sym}{remaining:,.2f}",
            delta=f"{sym}{remaining:,.2f}" if remaining >= 0 else f"-{sym}{abs(remaining):,.2f}",
            delta_color="normal" if remaining >= 0 else "inverse",
        )

        if bm.is_over_budget(total_spent):
            st.error(
                f"🚨 You are **over budget by {sym}{abs(remaining):,.2f}**! "
                "Review your expenses and look for areas to cut back."
            )

    except BudgetNotSetError:
        st.info("👆 Enter your income and budget above to see your summary.")


# ===========================================================================
# PAGE 2 — Budget & Expenses
# ===========================================================================

elif page == "📋 Budget & Expenses":
    st.title("📋 Budget & Expenses")

    # Check budget is set
    try:
        bm.get_profile()
    except BudgetNotSetError:
        st.warning("⚠️ Please set your income and budget on the **Dashboard** first.")
        st.stop()

    sym = _sym()

    # ------------------------------------------------------------------
    # Add expense form
    # ------------------------------------------------------------------
    st.subheader("➕ Add an Expense")

    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", ExpenseCategory.values())
            description = st.text_input(
                "Description",
                max_chars=100,
                placeholder="e.g. Groceries at Walmart",
            )
        with col2:
            amount = st.number_input(
                "Amount",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f",
            )
            expense_date = st.date_input(
                "Date",
                value=date.today(),
                max_value=date.today() + timedelta(days=1),
            )
        add_btn = st.form_submit_button("➕ Add Expense", use_container_width=True)

    if add_btn:
        try:
            expense = et.add_expense(category, description, amount, expense_date)
            st.success(
                f"✅ Added: **{expense.description}** | "
                f"{sym}{expense.amount:,.2f} | {expense.category.value} | {expense.date}"
            )
        except (InvalidAmountError, InvalidCategoryError, BudgetNotSetError) as e:
            st.error(f"❌ {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

    # ------------------------------------------------------------------
    # Expense list
    # ------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📄 All Expenses")

    expenses = et.get_all_expenses()

    if not expenses:
        st.info("No expenses recorded yet. Add your first expense above.")
    else:
        total_spent = et.get_total_spent()
        st.metric("Total Spending", f"{sym}{total_spent:,.2f}")

        # Display table
        import pandas as pd  # imported here to keep the top of file clean

        rows = [
            {
                "Date": str(e.date),
                "Category": e.category.value,
                "Description": e.description,
                "Amount": f"{sym}{e.amount:,.2f}",
                "ID": e.expense_id,
            }
            for e in expenses
        ]
        df = pd.DataFrame(rows)
        st.dataframe(df.drop(columns=["ID"]), use_container_width=True)

        # Delete individual expense
        with st.expander("🗑️ Delete an Expense"):
            del_options = {
                f"{e.date} | {e.category.value} | {e.description} | {sym}{e.amount:,.2f}": e.expense_id
                for e in expenses
            }
            selected_label = st.selectbox("Select expense to delete", list(del_options.keys()))
            if st.button("Delete Selected Expense", type="secondary"):
                et.remove_expense(del_options[selected_label])
                st.success("✅ Expense deleted.")
                st.rerun()

        # CSV download
        st.markdown("---")
        csv_data = svc["repo"].expenses_to_csv_string()
        st.download_button(
            label="⬇️ Download Expenses as CSV",
            data=csv_data,
            file_name="my_expenses.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # CSV upload
        with st.expander("⬆️ Import Expenses from CSV"):
            uploaded = st.file_uploader("Upload a previously exported CSV", type=["csv"])
            if uploaded and st.button("Import Expenses"):
                try:
                    text = uploaded.read().decode("utf-8")
                    imported = svc["repo"].import_expenses_from_csv_string(text)
                    for exp in imported:
                        svc["repo"].add_expense(exp)
                    st.success(f"✅ Imported {len(imported)} expenses.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Import failed: {e}")


# ===========================================================================
# PAGE 3 — Spending Analysis
# ===========================================================================

elif page == "📊 Spending Analysis":
    st.title("📊 Spending Analysis")

    try:
        profile = bm.get_profile()
        sym = profile.currency_symbol
        total_spent = et.get_total_spent()
        remaining = bm.get_remaining_budget(total_spent)

        # Key metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Budget", f"{sym}{profile.monthly_budget:,.2f}")
        c2.metric("Spent", f"{sym}{total_spent:,.2f}")
        c3.metric(
            "Remaining",
            f"{sym}{remaining:,.2f}",
            delta_color="normal" if remaining >= 0 else "inverse",
        )

        # Category chart
        st.markdown("---")
        st.subheader("📂 Category-Wise Spending")

        try:
            import pandas as pd

            cat_totals = sa.get_category_totals()
            cat_df = pd.DataFrame(
                {"Category": list(cat_totals.keys()), "Amount": list(cat_totals.values())}
            ).sort_values("Amount", ascending=False)

            st.bar_chart(cat_df.set_index("Category")["Amount"])

            # Table with formatted amounts
            cat_df["Amount"] = cat_df["Amount"].apply(lambda x: f"{sym}{x:,.2f}")
            st.dataframe(cat_df, use_container_width=True, hide_index=True)

        except EmptyExpenseListError:
            st.info("Add some expenses to see category-wise spending.")

        # Spending patterns
        st.markdown("---")
        st.subheader("🔍 Spending Observations")

        try:
            patterns = sa.get_spending_patterns()
            for observation in patterns:
                st.info(observation)
        except (EmptyExpenseListError, BudgetNotSetError) as e:
            st.info(str(e))

        # Tips
        st.markdown("---")
        st.subheader("💡 Personalised Tips")
        try:
            tips = te.generate_tips(profile, et.get_all_expenses())
            for tip in tips:
                if tip.startswith("⚠️") or tip.startswith("❌"):
                    st.warning(tip)
                elif tip.startswith("✅"):
                    st.success(tip)
                elif "---" in tip:
                    st.caption(tip)
                else:
                    st.info(tip)
        except Exception as e:
            st.warning(f"Could not generate tips: {e}")

    except BudgetNotSetError:
        st.warning("⚠️ Please set your income and budget on the **Dashboard** first.")


# ===========================================================================
# PAGE 4 — Can I Afford This?
# ===========================================================================

elif page == "🤔 Can I Afford This?":
    st.title("🤔 Can I Afford This?")
    st.markdown(
        "Enter an item you are thinking about buying. "
        "This tool will tell you whether it fits within your remaining budget — "
        "**as a budgeting calculation, not financial advice**."
    )

    try:
        bm.get_profile()
    except BudgetNotSetError:
        st.warning("⚠️ Please set your income and budget on the **Dashboard** first.")
        st.stop()

    sym = _sym()

    with st.form("afford_form"):
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input(
                "What do you want to buy?",
                placeholder="e.g. New laptop, Concert ticket…",
                max_chars=100,
            )
        with col2:
            item_price = st.number_input(
                "Price",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f",
            )
        check_btn = st.form_submit_button("🔍 Check Affordability", use_container_width=True)

    if check_btn:
        try:
            total_spent = et.get_total_spent()
            affordable, message = ac.check(item_name or "item", item_price, total_spent)
            if affordable:
                st.success(message)
            else:
                st.warning(message)
        except (InvalidAmountError, BudgetNotSetError) as e:
            st.error(f"❌ {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")


# ===========================================================================
# PAGE 5 — Loan Basics
# ===========================================================================

elif page == "🏦 Loan Basics":
    st.title("🏦 Loan Basics")
    st.markdown(
        "Learn about common loan concepts and use the EMI calculator to understand "
        "the true cost of borrowing. **This section is educational only — we do not "
        "recommend any specific loan or lender.**"
    )

    # Loan glossary
    st.markdown(lc.get_loan_glossary())

    # EMI calculator
    st.markdown("---")
    st.subheader("🧮 EMI Calculator")

    sym = _sym()

    with st.form("emi_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            principal = st.number_input(
                "Loan Amount",
                min_value=1.0,
                value=1000.0,
                step=100.0,
                format="%.2f",
            )
        with col2:
            annual_rate = st.number_input(
                "Annual Interest Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=10.0,
                step=0.5,
                format="%.2f",
            )
        with col3:
            months = st.number_input(
                "Loan Tenure (months)",
                min_value=1,
                max_value=360,
                value=12,
                step=1,
            )
        calc_btn = st.form_submit_button("📐 Calculate", use_container_width=True)

    if calc_btn:
        try:
            explanation = lc.explain_emi(principal, annual_rate, int(months), sym)
            st.info(explanation)
        except InvalidLoanParameterError as e:
            st.error(f"❌ {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")


# ===========================================================================
# PAGE 6 — Scholarships & Aid
# ===========================================================================

elif page == "🏅 Scholarships & Aid":
    st.title("🏅 Scholarships & Financial Aid")
    st.markdown(
        "> The information below is **general educational guidance**. "
        "It is not a verified list of current scholarship opportunities. "
        "Always verify scholarship details through official university or government sources."
    )

    st.markdown(fa.get_scholarship_info())

    st.markdown("---")
    st.subheader("📋 Common Application Requirements")
    st.markdown(
        """
Most scholarship applications ask for some or all of the following:

| Document | Purpose |
|---|---|
| Academic transcripts | Proof of grades / GPA |
| Personal statement / essay | Explain why you deserve the award |
| Letters of recommendation | References from teachers or employers |
| Proof of enrolment | Confirm you are an active student |
| Financial need statement | Evidence of household income (for need-based awards) |
| CV / résumé | For professional or merit-based scholarships |
| Portfolio or work samples | For art, design or creative scholarships |

**Tips for applications:**
- Start early — many scholarships have deadlines months before the academic year.
- Tailor your personal statement to each specific scholarship.
- Ask a teacher or advisor to review your application before submitting.
- Apply for multiple scholarships — there is no limit on how many you can try.
- Never pay to apply for a scholarship. Legitimate scholarships are free to apply for.
"""
    )

    st.info(
        "💡 **Where to find scholarships:** Start with your university's financial aid "
        "office, then search your national government's student support website, and "
        "professional associations related to your field of study."
    )


# ===========================================================================
# PAGE 7 — AI Financial Advisor
# ===========================================================================

elif page == "🤖 AI Financial Advisor":
    st.title("🤖 AI Financial Literacy Advisor")

    if fa.is_ai_api_active():
        provider = os.getenv("AI_PROVIDER", "").upper()
        st.success(f"✅ Connected to {provider} AI — responses are AI-generated.")
    else:
        st.info(
            "🔧 Using built-in educational advisor. "
            "For AI-powered responses, set the `AI_PROVIDER` and `AI_API_KEY` "
            "environment variables (see README)."
        )

    st.markdown(
        "Ask any question about personal finance, budgeting, loans or scholarships. "
        "The advisor explains concepts in simple, student-friendly language."
    )

    # Quick question buttons
    st.subheader("💬 Quick Questions")
    quick_questions = [
        "How can I manage my monthly budget?",
        "Why am I spending too much on food?",
        "What is EMI?",
        "What is the difference between principal and interest?",
        "How should I track my expenses?",
        "What should I consider before taking a student loan?",
        "How can I start saving money?",
        "Tell me about scholarships",
    ]

    cols = st.columns(4)
    quick_q = None
    for i, q in enumerate(quick_questions):
        if cols[i % 4].button(q, use_container_width=True, key=f"qq_{i}"):
            quick_q = q

    # Free-text input
    st.markdown("---")
    st.subheader("✍️ Ask Your Own Question")

    with st.form("advisor_form"):
        user_question = st.text_input(
            "Your question",
            value=quick_q or "",
            placeholder="e.g. How do I build an emergency fund?",
        )
        ask_btn = st.form_submit_button("🤖 Ask", use_container_width=True)

    question_to_answer = None
    if ask_btn and user_question.strip():
        question_to_answer = user_question
    elif quick_q:
        question_to_answer = quick_q

    if question_to_answer:
        # Build a brief context string from the student's data
        context: str | None = None
        try:
            profile = bm.get_profile()
            total_spent = et.get_total_spent()
            remaining = bm.get_remaining_budget(total_spent)
            sym = profile.currency_symbol
            context = (
                f"Student has a monthly budget of {sym}{profile.monthly_budget:,.2f}, "
                f"has spent {sym}{total_spent:,.2f} so far, "
                f"and has {sym}{remaining:,.2f} remaining."
            )
        except BudgetNotSetError:
            pass

        with st.spinner("Thinking…"):
            response = fa.answer_question(question_to_answer, context)
        st.info(response)

    # Personalised tips section
    st.markdown("---")
    st.subheader("💡 Get Personalised Tips")
    if st.button("✨ Generate Tips Based on My Data", use_container_width=True):
        try:
            profile = bm.get_profile()
            expenses = et.get_all_expenses()
            tips = te.generate_tips(profile, expenses)
            for tip in tips:
                if tip.startswith("⚠️"):
                    st.warning(tip)
                elif tip.startswith("✅"):
                    st.success(tip)
                elif "---" in tip:
                    st.caption(tip)
                else:
                    st.info(tip)
        except BudgetNotSetError:
            st.warning("⚠️ Please set your budget on the Dashboard first.")
        except Exception as e:
            st.error(f"❌ {e}")
