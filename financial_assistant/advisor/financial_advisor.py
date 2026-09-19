"""
FinancialAdvisor — keyword-based Q&A and static educational content.

Design notes
------------
* No ML model or external API required for the core rule-based advisor.
* Optionally, if an IBM watsonx / OpenAI API key is supplied via the
  environment variable  AI_API_KEY  (and AI_PROVIDER is set to "watsonx"
  or "openai"), the advisor will call the real API and use the rule-based
  fallback when the call fails or credentials are absent.
* The rest of the application never knows which backend is active —
  all callers use `answer_question()`.
"""

from __future__ import annotations

import os
from typing import Optional

from financial_assistant.constants import DISCLAIMER


# ---------------------------------------------------------------------------
# Keyword → educational response mapping
# ---------------------------------------------------------------------------

_KNOWLEDGE_BASE: dict[str, str] = {
    "budget": (
        "### 💡 Managing Your Budget\n\n"
        "A budget is a plan that tells your money where to go instead of wondering "
        "where it went.\n\n"
        "**Tips for students:**\n"
        "1. Write down all your sources of income (stipend, part-time job, allowance).\n"
        "2. List all fixed expenses first (rent, course fees).\n"
        "3. Allocate a fixed amount to variable expenses (food, travel, entertainment).\n"
        "4. Track every expense — even small ones add up.\n"
        "5. Review your budget at the end of each month and adjust."
    ),
    "overspend": (
        "### ⚠️ Why Am I Spending Too Much?\n\n"
        "Common reasons students overspend:\n"
        "- No written budget — spending without a plan.\n"
        "- Impulse purchases — buying without asking 'Do I need this now?'\n"
        "- Eating out frequently instead of cooking.\n"
        "- Subscription services that are forgotten but still charged.\n\n"
        "**Quick fix:** For one week, write down every purchase. "
        "You will likely find 2–3 categories you can easily reduce."
    ),
    "food": (
        "### 🍱 Reducing Food Spending\n\n"
        "Food is one of the most flexible budget categories for students.\n\n"
        "- Meal-prep on Sundays to reduce daily takeaway temptation.\n"
        "- Use a grocery list and stick to it.\n"
        "- Compare prices at different stores.\n"
        "- Cook in bulk and freeze portions.\n"
        "- Limit eating out to a set number of times per month."
    ),
    "emi": (
        "### 📐 What is EMI?\n\n"
        "**EMI** stands for **Equated Monthly Instalment**.\n\n"
        "When you take a loan, you repay it in equal monthly instalments. "
        "Each instalment includes:\n"
        "- A portion of the **principal** (the money you borrowed)\n"
        "- A portion of the **interest** (the lender's fee)\n\n"
        "The EMI is fixed for the entire loan tenure, making it easier to plan "
        "your monthly budget."
    ),
    "interest": (
        "### 💰 Principal vs Interest\n\n"
        "**Principal** is the original amount you borrow.\n\n"
        "**Interest** is the extra amount the lender charges for giving you the loan. "
        "It is calculated as a percentage of the outstanding principal.\n\n"
        "Example:\n"
        "- You borrow $1,000 at 12% annual interest for 12 months.\n"
        "- Total interest paid ≈ $66.\n"
        "- Total repayment ≈ $1,066.\n\n"
        "The higher the interest rate and the longer the tenure, the more you pay."
    ),
    "principal": (
        "### 🏦 What is Principal?\n\n"
        "**Principal** is the original sum of money you borrow from a lender.\n\n"
        "When you repay a loan, each payment reduces the principal while also "
        "covering the interest charged on the outstanding balance. "
        "The faster you repay the principal, the less total interest you pay."
    ),
    "loan": (
        "### 🎓 Student Loan Basics\n\n"
        "Before taking a student loan, consider:\n\n"
        "1. **Do you really need it?** Explore scholarships and grants first — "
        "they don't need to be repaid.\n"
        "2. **Interest rate** — Lower is better. Government loans often have lower "
        "rates than private lenders.\n"
        "3. **Repayment terms** — When do payments start? After graduation? "
        "During studies?\n"
        "4. **Total repayment amount** — Use an EMI calculator to understand the "
        "full cost before signing.\n"
        "5. **Your future income** — Only borrow what you can realistically repay "
        "from your expected post-graduation salary."
    ),
    "scholarship": (
        "### 🏅 Scholarships & Financial Aid\n\n"
        "**What is a scholarship?** Money awarded to students to help pay for "
        "education — it does **not** need to be repaid.\n\n"
        "**Common eligibility factors:**\n"
        "- Academic merit (GPA, grades)\n"
        "- Financial need (family income)\n"
        "- Field of study or specific subject\n"
        "- Nationality, ethnicity or community membership\n"
        "- Athletic or artistic talent\n\n"
        "**Where to look:**\n"
        "- Your university's financial aid office\n"
        "- Government education department websites\n"
        "- Reputable scholarship databases\n"
        "- Professional associations in your field of study\n\n"
        "Always apply through official channels."
    ),
    "save": (
        "### 🐖 How to Start Saving Money\n\n"
        "Even saving a small amount regularly builds a great habit.\n\n"
        "**The 50/30/20 rule (simplified for students):**\n"
        "- **50%** of income → essential needs (rent, food, transport)\n"
        "- **30%** → wants (entertainment, dining out)\n"
        "- **20%** → savings or paying off debt\n\n"
        "**Practical tips:**\n"
        "- Open a separate savings account and transfer a fixed amount on payday.\n"
        "- Build a small emergency fund (1–2 months of expenses) before investing.\n"
        "- Automate savings so you never have to think about it."
    ),
    "credit": (
        "### 💳 Credit Cards & Debt\n\n"
        "A credit card lets you spend money you haven't earned yet — and charges "
        "interest if you don't repay the full balance each month.\n\n"
        "**Student tips:**\n"
        "- Always pay the **full balance** every month to avoid interest.\n"
        "- Never use a credit card for money you don't have in your account.\n"
        "- A good credit history helps you get loans at better rates later.\n"
        "- Minimum payments are a trap — you pay mostly interest and barely reduce "
        "the principal."
    ),
    "track": (
        "### 📒 How to Track Your Expenses\n\n"
        "Tracking expenses is the foundation of good financial habits.\n\n"
        "**Methods (choose what suits you):**\n"
        "- Use this app! Add every expense as soon as you make it.\n"
        "- Keep receipts and log them weekly.\n"
        "- Use a simple spreadsheet with date, category and amount.\n\n"
        "**Why it matters:**\n"
        "Tracking shows you exactly where your money goes. Most people are "
        "surprised by how much they spend on small daily items."
    ),
    "emergency": (
        "### 🚨 Emergency Fund\n\n"
        "An emergency fund is savings set aside for unexpected expenses "
        "(medical, broken laptop, sudden travel).\n\n"
        "**Goal for students:** Save at least 1–2 months of living expenses.\n\n"
        "Keep it in a separate savings account you don't touch unless it's a "
        "genuine emergency. Even saving $20–$50 per month gets you there."
    ),
}

# Order matters: check longer/more-specific terms before shorter ones
_KEYWORD_ORDER: list[str] = [
    "overspend", "scholarship", "principal", "interest", "emergency",
    "emi", "loan", "budget", "food", "save", "credit", "track",
]


class FinancialAdvisor:
    """
    Answers student financial-literacy questions.

    Uses a keyword-matching rule base by default.
    If  AI_PROVIDER  and  AI_API_KEY  environment variables are set,
    it will attempt to call the configured AI API.

    Parameters
    ----------
    use_ai_api : bool
        If True, attempt to use the configured AI API.
        Defaults to auto-detect from environment variables.
    """

    def __init__(self, use_ai_api: Optional[bool] = None) -> None:
        self._provider = os.getenv("AI_PROVIDER", "").lower()
        self._api_key = os.getenv("AI_API_KEY", "")
        if use_ai_api is None:
            self._use_api = bool(self._provider and self._api_key)
        else:
            self._use_api = use_ai_api

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def answer_question(
        self,
        user_input: str,
        context: Optional[str] = None,
    ) -> str:
        """
        Return an educational response to the student's question.

        Parameters
        ----------
        user_input : str
            The student's free-text question.
        context : str, optional
            Additional context such as the student's budget/spending summary.
            Passed to the AI API if one is configured.

        Returns
        -------
        str
            A formatted markdown string with the educational response.
        """
        if not user_input.strip():
            return "Please type a question to get started." + DISCLAIMER

        if self._use_api:
            response = self._call_ai_api(user_input, context)
            if response:
                return response + DISCLAIMER

        # Fall back to rule-based response
        return self._rule_based_response(user_input)

    # ------------------------------------------------------------------
    # Rule-based fallback
    # ------------------------------------------------------------------

    def _rule_based_response(self, user_input: str) -> str:
        lower = user_input.lower()
        for keyword in _KEYWORD_ORDER:
            if keyword in lower:
                return _KNOWLEDGE_BASE[keyword] + DISCLAIMER

        return (
            "### 🤔 I'm not sure about that specific question.\n\n"
            "Here are some topics I can help with:\n\n"
            "- **Budget** — how to plan and manage your monthly budget\n"
            "- **Expenses / Track** — how to track and reduce spending\n"
            "- **Save / Savings** — how to start saving money\n"
            "- **EMI** — what EMI means and how it is calculated\n"
            "- **Loan** — what to consider before taking a student loan\n"
            "- **Interest / Principal** — understanding loan costs\n"
            "- **Scholarship** — how to find and apply for scholarships\n"
            "- **Credit** — credit cards and debt management\n"
            "- **Emergency** — building an emergency fund\n\n"
            "Try asking about one of these topics!"
        ) + DISCLAIMER

    # ------------------------------------------------------------------
    # AI API backend (optional)
    # ------------------------------------------------------------------

    def _call_ai_api(self, user_input: str, context: Optional[str]) -> Optional[str]:
        """
        Attempt to call the configured AI API.

        Supported providers (set via environment variables):
            AI_PROVIDER=openai   AI_API_KEY=sk-...
            AI_PROVIDER=watsonx  AI_API_KEY=...  (also set WATSONX_URL, WATSONX_PROJECT_ID)

        Returns None on any error so the caller falls back to rule-based responses.
        """
        try:
            if self._provider == "openai":
                return self._call_openai(user_input, context)
            elif self._provider == "watsonx":
                return self._call_watsonx(user_input, context)
        except Exception:
            pass
        return None

    def _call_openai(self, user_input: str, context: Optional[str]) -> Optional[str]:
        """Call the OpenAI chat completions API."""
        try:
            import openai  # type: ignore
        except ImportError:
            return None

        client = openai.OpenAI(api_key=self._api_key)
        system_prompt = (
            "You are a friendly financial literacy assistant for college students. "
            "Explain financial concepts in simple, beginner-friendly language. "
            "Never make specific investment or loan recommendations. "
            "Always encourage students to verify important information with official sources."
        )
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "system", "content": f"Student context: {context}"})
        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content

    def _call_watsonx(self, user_input: str, context: Optional[str]) -> Optional[str]:
        """Call the IBM watsonx.ai API."""
        try:
            from ibm_watsonx_ai import Credentials  # type: ignore
            from ibm_watsonx_ai.foundation_models import ModelInference  # type: ignore
        except ImportError:
            return None

        watsonx_url = os.getenv("WATSONX_URL", "")
        project_id = os.getenv("WATSONX_PROJECT_ID", "")
        if not watsonx_url or not project_id:
            return None

        credentials = Credentials(url=watsonx_url, api_key=self._api_key)
        model = ModelInference(
            model_id="ibm/granite-13b-chat-v2",
            credentials=credentials,
            project_id=project_id,
        )
        system = (
            "You are a financial literacy assistant for college students. "
            "Answer in simple, educational language. "
            "Do not make specific financial recommendations."
        )
        prompt = f"{system}\n\n"
        if context:
            prompt += f"Student context: {context}\n\n"
        prompt += f"Student question: {user_input}\n\nAnswer:"

        response = model.generate_text(prompt=prompt, guardrails=False)
        return response

    # ------------------------------------------------------------------
    # Static educational content
    # ------------------------------------------------------------------

    def get_scholarship_info(self) -> str:
        return _KNOWLEDGE_BASE["scholarship"] + DISCLAIMER

    def get_loan_basics(self) -> str:
        return _KNOWLEDGE_BASE["loan"] + DISCLAIMER

    def is_ai_api_active(self) -> bool:
        """Return True if a real AI API backend is configured and in use."""
        return self._use_api
