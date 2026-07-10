import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go

from app.constants import CATEGORIES

WARNING_THRESHOLD = 0.8

# Traffic-light colors for the budget-vs-actual chart — chosen to exactly match
# the .status-pill colors used on the same page (frontend/src/index.css),
# not the 8-hue categorical palette (this chart isn't about category identity).
OK_COLOR = "#126c43"       # matches --success
WARNING_COLOR = "#9a6400"  # matches --warning
OVER_COLOR = "#b42318"     # matches --danger
CONTEXT_COLOR = "#c3c2b7"  # matches analytics_service's neutral reference-bar gray

CHART_FONT = dict(family="Inter, ui-sans-serif, system-ui, -apple-system, sans-serif", color="#4d5565", size=12)
GRIDLINE_COLOR = "#dfe3ec"

STATUS_COLORS = {"ok": OK_COLOR, "warning": WARNING_COLOR, "over": OVER_COLOR}


def evaluate_status(spent: float, limit: Optional[float]) -> str:
    if not limit or limit <= 0:
        return "no_budget"
    if spent >= limit:
        return "over"
    if spent >= limit * WARNING_THRESHOLD:
        return "warning"
    return "ok"


def project_month_end(spent_so_far: float, days_elapsed: int, days_in_month: int) -> float:
    """Straight-line projection shared by the whole-month pace insight
    (analytics_service) and the per-category trending-over-budget rule
    (decision_engine_service) — same formula, two different scopes of `spent_so_far`."""
    if days_elapsed <= 0:
        return 0.0
    return spent_so_far / days_elapsed * days_in_month


def month_totals_by_category(receipts: List[dict], month_str: str) -> Dict[str, float]:
    """Category totals for one calendar month (e.g. "2026-07"). Shared by the
    current-month budget overview and the decision engine's month-over-month rule."""
    if not receipts:
        return {}

    df = pd.DataFrame(receipts)
    df["total"] = pd.to_numeric(df.get("total"), errors="coerce").fillna(0.0)
    df["category"] = df.get("category").fillna("Other") if "category" in df else "Other"

    date_parsed = pd.to_datetime(df.get("date"), format="%Y-%m-%d", errors="coerce")
    fallback_dates = pd.to_datetime(df.get("created_at"), errors="coerce")
    date_parsed = date_parsed.fillna(fallback_dates)
    month = date_parsed.dt.strftime("%Y-%m")

    month_df = df[month == month_str]
    if month_df.empty:
        return {}
    return month_df.groupby("category")["total"].sum().to_dict()


def _current_month_totals_by_category(receipts: List[dict], now: Optional[datetime] = None) -> Dict[str, float]:
    now = now or datetime.now()
    return month_totals_by_category(receipts, now.strftime("%Y-%m"))


def build_budget_insights(current_cat_totals: Dict[str, float], budgets: List[dict]) -> List[dict]:
    """Shared with the /api/budgets overview — same thresholds, single source of truth."""
    limits = {b["category"]: b.get("monthly_limit") for b in budgets}

    worst_over = None
    worst_warning = None
    for category, limit in limits.items():
        spent = float(current_cat_totals.get(category, 0.0))
        status = evaluate_status(spent, limit)
        if status == "over":
            pct = spent / limit if limit else 0
            if worst_over is None or pct > worst_over[0]:
                worst_over = (pct, category, spent, limit)
        elif status == "warning":
            pct = spent / limit if limit else 0
            if worst_warning is None or pct > worst_warning[0]:
                worst_warning = (pct, category, spent, limit)

    insights: List[dict] = []
    if worst_over:
        _, category, spent, limit = worst_over
        insights.append({
            "type": "budget_over",
            "message": f"You've gone over your Rs. {limit:,.0f} monthly budget for {category} — Rs. {spent:,.2f} spent so far.",
            "detail": (
                f"{category}'s monthly budget is Rs. {limit:,.0f}. You've spent Rs. {spent:,.2f} so far this month, "
                f"which is Rs. {spent - limit:,.2f} over the limit."
            ),
            "chart": "budget_vs_actual",
        })
    if worst_warning:
        _, category, spent, limit = worst_warning
        pct = spent / limit * 100
        insights.append({
            "type": "budget_warning",
            "message": f"{category} is at {pct:.0f}% of its Rs. {limit:,.0f} monthly budget — Rs. {spent:,.2f} spent.",
            "detail": (
                f"{category}'s monthly budget is Rs. {limit:,.0f}. You've spent Rs. {spent:,.2f} so far ({pct:.0f}%), "
                f"leaving Rs. {limit - spent:,.2f} remaining this month."
            ),
            "chart": "budget_vs_actual",
        })
    return insights


def build_budget_overview(receipts: List[dict], budgets: List[dict], now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now()
    spent_by_category = _current_month_totals_by_category(receipts, now)
    limits = {b["category"]: b.get("monthly_limit") for b in budgets}

    rows = []
    for category in CATEGORIES:
        limit = limits.get(category)
        spent = float(spent_by_category.get(category, 0.0))
        status = evaluate_status(spent, limit)
        remaining = round(limit - spent, 2) if limit else None
        pct_used = round(spent / limit * 100, 1) if limit else None
        rows.append({
            "category": category,
            "limit": limit,
            "spent": round(spent, 2),
            "remaining": remaining,
            "pct_used": pct_used,
            "status": status,
        })

    budgeted_rows = [r for r in rows if r["limit"] is not None]
    summary = {
        "total_budgeted": round(sum(r["limit"] for r in budgeted_rows), 2) if budgeted_rows else 0.0,
        "total_spent": round(sum(r["spent"] for r in budgeted_rows), 2) if budgeted_rows else 0.0,
        "over_count": sum(1 for r in rows if r["status"] == "over"),
        "warning_count": sum(1 for r in rows if r["status"] == "warning"),
    }

    return {
        "categories": rows,
        "summary": summary,
        "figure": _budget_vs_actual_figure(budgeted_rows),
    }


def _budget_vs_actual_figure(budgeted_rows: List[dict]) -> Optional[dict]:
    if not budgeted_rows:
        return None

    # Ascending so the most at-risk category (highest % used) sits on top —
    # this chart is about what needs attention, not raw magnitude.
    ordered = sorted(budgeted_rows, key=lambda r: r["pct_used"] or 0)
    categories = [r["category"] for r in ordered]
    limits = [r["limit"] for r in ordered]
    spent = [r["spent"] for r in ordered]
    spent_colors = [STATUS_COLORS[r["status"]] for r in ordered]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=categories, x=limits, orientation="h", name="Budget",
        marker=dict(color=CONTEXT_COLOR),
        hovertemplate="%{y} budget: Rs. %{x:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=categories, x=spent, orientation="h", name="Spent",
        marker=dict(color=spent_colors),
        hovertemplate="%{y} spent: Rs. %{x:,.2f}<extra></extra>",
    ))

    max_total = max(limits + spent) if (limits or spent) else 0
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=CHART_FONT,
        margin=dict(l=8, r=24, t=40, b=8),
        showlegend=True,
        legend=dict(orientation="h", y=1.15, x=0),
        barmode="group",
        bargap=0.3,
        bargroupgap=0.1,
        xaxis=dict(
            showgrid=True, gridcolor=GRIDLINE_COLOR, zeroline=False,
            separatethousands=True, tickformat=",.0f", range=[0, max_total * 1.2],
        ),
        yaxis=dict(showgrid=False),
    )
    return json.loads(fig.to_json())
