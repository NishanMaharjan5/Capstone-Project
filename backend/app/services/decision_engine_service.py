import calendar
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.constants import CATEGORIES, ESSENTIAL_CATEGORIES
from app.services import budget_service
from app.services.analytics_service import _category_comparison_figure

CATEGORY_GROWTH_THRESHOLD = 20  # percent — matches Insights' category_increase rule
MAX_SUGGESTIONS = 3
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def build_suggestions(receipts: List[dict], budgets: List[dict], now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now()
    overview = budget_service.build_budget_overview(receipts, budgets, now)
    rows = overview["categories"]
    summary = overview["summary"]

    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_elapsed = now.day

    last_month_date = now.replace(day=1) - timedelta(days=1)
    last_month_totals = budget_service.month_totals_by_category(receipts, last_month_date.strftime("%Y-%m"))

    suggestions: List[dict] = []

    for row in rows:
        category = row["category"]
        limit = row["limit"]
        spent = row["spent"]

        if limit is None:
            previous = last_month_totals.get(category, 0)
            if previous > 0:
                pct_change = (spent - previous) / previous * 100
                if pct_change >= CATEGORY_GROWTH_THRESHOLD:
                    suggestions.append({
                        "type": "suggest_budget",
                        "headline": f"Consider setting a budget for {category}",
                        "reasoning": (
                            f"{category} spending is up {pct_change:.0f}% vs last month "
                            f"(Rs. {spent:,.2f} vs Rs. {previous:,.2f}), and there's no budget set for it yet. "
                            f"Setting one would make it easier to catch this kind of jump early."
                        ),
                        "chart": "category_comparison",
                        "severity": "medium",
                    })
            continue

        if row["status"] == "over":
            over_by = spent - limit
            is_essential = category in ESSENTIAL_CATEGORIES
            if is_essential:
                headline = f"Keep an eye on {category}"
                action = "This is a harder category to cut back on, but it's worth reviewing what's driving the increase."
            else:
                headline = f"Consider spending less on {category}"
                action = "Trimming a few purchases here would bring you back under budget."
            suggestions.append({
                "type": "over_budget",
                "headline": headline,
                "reasoning": (
                    f"{category}'s monthly budget is Rs. {limit:,.0f}, and you've already spent "
                    f"Rs. {spent:,.2f} this month — Rs. {over_by:,.2f} over. {action}"
                ),
                "chart": "budget_vs_actual",
                "severity": "high",
            })
        else:
            projected = budget_service.project_month_end(spent, days_elapsed, days_in_month)
            if projected > limit:
                over_by = projected - limit
                suggestions.append({
                    "type": "trending_over_budget",
                    "headline": f"At this pace, {category} will go over budget",
                    "reasoning": (
                        f"You've spent Rs. {spent:,.2f} of your Rs. {limit:,.0f} {category} budget over the first "
                        f"{days_elapsed} days of the month. At that rate, you're on track to spend "
                        f"Rs. {projected:,.2f} by month end — about Rs. {over_by:,.2f} over."
                    ),
                    "chart": "budget_vs_actual",
                    "severity": "medium",
                })

    if summary["total_budgeted"] > 0 and summary["total_spent"] > summary["total_budgeted"]:
        over_by = summary["total_spent"] - summary["total_budgeted"]
        suggestions.append({
            "type": "overall_over_budget",
            "headline": "Overall, you're over your combined monthly budgets",
            "reasoning": (
                f"Across all categories with a budget set, you've spent Rs. {summary['total_spent']:,.2f} "
                f"against a combined limit of Rs. {summary['total_budgeted']:,.0f} — "
                f"Rs. {over_by:,.2f} over. Worth reviewing where to adjust."
            ),
            "chart": "budget_vs_actual",
            "severity": "high",
        })

    suggestions.sort(key=lambda s: SEVERITY_ORDER.get(s["severity"], 99))
    suggestions = suggestions[:MAX_SUGGESTIONS]

    # Only build the (mildly expensive) comparison figure if a surviving
    # suggestion — after the cap above — actually points at it.
    needs_category_comparison = any(s["chart"] == "category_comparison" for s in suggestions)

    category_comparison_figure = None
    if needs_category_comparison:
        current_totals = {row["category"]: row["spent"] for row in rows}
        comparison = [
            {"category": c, "current": current_totals.get(c, 0), "previous": last_month_totals.get(c, 0)}
            for c in CATEGORIES
        ]
        category_comparison_figure = _category_comparison_figure(comparison)

    return {
        "suggestions": suggestions,
        "figures": {
            "budget_vs_actual": overview["figure"],
            "category_comparison": category_comparison_figure,
        },
    }
