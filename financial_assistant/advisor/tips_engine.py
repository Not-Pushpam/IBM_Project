"""
TipsEngine — generates personalised financial-literacy tips from the student's data.
"""

from __future__ import annotations

from financial_assistant.constants import (
    DISCLAIMER,
    HIGH_SPEND_THRESHOLD,
    ExpenseCategory,
)
from financial_assistant.models.budget_profile import BudgetProfile
from financial_assistant.models.expense import Expense


class TipsEngine:
    """
    Produces a list of personalised financial-literacy tips.

    Tips are generated from the student's actual budget and expense data.
    No state is stored — all data is passed as arguments.
    """

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_tips(
        self,
        profile: BudgetProfile,
        expenses: list[Expense],
    ) -> list[str]:
        """
        Return a list of personalised tip strings (3–6 items).

        If no expenses exist, return generic beginner tips instead.
        """
        if not expenses:
            return self._generic_beginner_tips()

        tips: list[str] = []
        total_spent = sum(e.amount for e in expenses)
        remaining = profile.monthly_budget - total_spent
        budget = profile.monthly_budget
        sym = profile.currency_symbol

        # Category totals
        cat_totals: dict[str, float] = {cat.value: 0.0 for cat in ExpenseCategory}
        for expense in expenses:
            cat_totals[expense.category.value] += expense.amount
        top_cat = max(cat_totals, key=lambda k: cat_totals[k])
        top_amt = cat_totals[top_cat]

        # 1. Over-budget warning
        if remaining < 0:
            tips.append(
                f"⚠️ You are **over budget by {sym}{abs(remaining):,.2f}**. "
                f"Try to reduce spending in **{top_cat}** "
                f"({sym}{top_amt:,.2f} this month) — that is your biggest category."
            )
        else:
            pct_used = (total_spent / budget * 100) if budget > 0 else 0
            tips.append(
                f"You have used **{pct_used:.1f}%** of your budget so far. "
                f"You have **{sym}{remaining:,.2f}** left this month."
            )

        # 2. High-spend category warning
        for cat, amount in cat_totals.items():
            if amount > budget * HIGH_SPEND_THRESHOLD:
                tips.append(
                    f"💡 **{cat}** spending ({sym}{amount:,.2f}) is more than 50% of "
                    f"your budget. Consider setting a stricter limit for this category."
                )
                break  # one warning is enough

        # 3. Savings tip
        if profile.monthly_income > profile.monthly_budget and remaining > 0:
            tips.append(self.get_savings_tip(remaining, profile.monthly_income))

        # 4. Positive reinforcement
        if remaining > budget * 0.30:
            tips.append(
                "✅ You still have more than 30% of your budget remaining. "
                "Consider putting some of it into a small emergency fund."
            )

        # 5. Top-category specific tip
        tips.append(self.get_overspending_tip(top_cat))

        # Pad with a generic tip if we have fewer than 3
        generic = self._generic_beginner_tips()
        i = 0
        while len(tips) < 3 and i < len(generic):
            if generic[i] not in tips:
                tips.append(generic[i])
            i += 1

        return tips

    # ------------------------------------------------------------------
    # Individual tip generators
    # ------------------------------------------------------------------

    def get_overspending_tip(self, category: str) -> str:
        tips_map: dict[str, str] = {
            "Food": (
                "🍱 **Food tip:** Try meal-prepping on weekends to reduce daily "
                "takeaway spending. Cooking in bulk can cut food costs significantly."
            ),
            "Travel": (
                "🚌 **Travel tip:** Consider using public transport or a bike for "
                "short distances. Monthly passes are usually cheaper than per-trip fares."
            ),
            "Shopping": (
                "🛍️ **Shopping tip:** Before buying, wait 24 hours. Many impulse "
                "purchases feel less urgent the next day."
            ),
            "Education": (
                "📚 **Education tip:** Check your library for textbooks before "
                "buying. Many universities offer digital access to course materials."
            ),
            "Rent": (
                "🏠 **Rent tip:** If rent is a large portion of your budget, "
                "consider whether sharing accommodation could reduce costs."
            ),
            "Other": (
                "💡 **Tip:** Review your 'Other' expenses — these are often small "
                "one-off purchases that add up quickly. Categorise them to spot patterns."
            ),
        }
        return tips_map.get(
            category,
            "💡 Review your highest spending category and look for one area to cut back.",
        )

    def get_savings_tip(self, remaining_budget: float, income: float) -> str:
        if income > 0:
            save_pct = (remaining_budget / income) * 100
            return (
                f"💰 **Savings tip:** You could save up to "
                f"**{save_pct:.1f}%** of your income this month. "
                "Even saving a small fixed amount each month builds a strong habit."
            )
        return (
            "💰 **Savings tip:** Try to save at least 10% of your income each month, "
            "no matter how small the amount."
        )

    # ------------------------------------------------------------------
    # Generic tips (used when no expenses exist)
    # ------------------------------------------------------------------

    @staticmethod
    def _generic_beginner_tips() -> list[str]:
        return [
            (
                "📝 **Start by tracking every expense** — even small ones like coffee "
                "or snacks. After one month you will know exactly where your money goes."
            ),
            (
                "🎯 **Set a budget before the month starts.** Divide your income into "
                "needs (50%), wants (30%), and savings (20%)."
            ),
            (
                "🚨 **Build a small emergency fund.** Even $50–$100 saved separately "
                "can prevent a minor emergency from becoming a financial crisis."
            ),
            (
                "💳 **Avoid credit card debt.** If you use a credit card, pay the "
                "full balance every month to avoid interest charges."
            ),
            (
                "🏅 **Explore scholarships before taking loans.** Scholarships and "
                "grants don't need to be repaid — always apply first."
            ),
        ] + [DISCLAIMER]
