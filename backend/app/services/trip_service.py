import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go

from app.constants import TRIP_CATEGORY_COLORS
from app.services.budget_service import evaluate_status

TREND_COLOR = "#2d6ef5"  # app's --accent
CONTEXT_COLOR = "#c3c2b7"  # dataviz skill's neutral gray, for the budget-pace reference line
DEFAULT_CATEGORY_COLOR = "#7b8496"

CHART_FONT = dict(family="Inter, ui-sans-serif, system-ui, -apple-system, sans-serif", color="#4d5565", size=12)
GRIDLINE_COLOR = "#dfe3ec"


def _base_layout(**overrides) -> dict:
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=CHART_FONT,
        margin=dict(l=8, r=24, t=8, b=8),
        showlegend=False,
    )
    layout.update(overrides)
    return layout


def _figure_to_json_safe(fig: go.Figure) -> dict:
    return json.loads(fig.to_json())


def validate_trip_budgets(total_budget: Optional[float], budgets: Dict[str, float]) -> None:
    """Same two-part rule as the main app's budget management (app/routers/budget.py):
    a total must exist before any category gets a slice of it, and the slices
    can't add up to more than the total. Raises ValueError with a user-facing
    message on violation; a no-op if no category budgets are being set."""
    if total_budget is not None and total_budget <= 0:
        raise ValueError("Trip budget must be greater than zero.")

    allocated = round(sum(budgets.values()), 2)
    if allocated <= 0:
        return

    if not total_budget:
        raise ValueError("Set a trip budget first, then divide it across categories.")
    if allocated > total_budget:
        raise ValueError(
            f"Category budgets add up to Rs. {allocated:,.2f}, which is more than your "
            f"Rs. {total_budget:,.2f} trip budget — lower them to fit."
        )


def build_trip_totals(receipts: List[dict]) -> Dict[str, Any]:
    """Cheap per-trip totals for the trip list view — no charts, no budget rows."""
    if not receipts:
        return {"total_spent": 0.0, "receipt_count": 0}
    total = sum(float(r.get("total") or 0) for r in receipts)
    return {"total_spent": round(total, 2), "receipt_count": len(receipts)}


def _trip_date_range(trip: dict, receipts: List[dict]) -> tuple:
    start = datetime.strptime(trip["start_date"], "%Y-%m-%d").date()
    ended_at = trip.get("ended_at")
    end = datetime.fromisoformat(ended_at).date() if ended_at else datetime.now().date()
    if end < start:
        end = start

    # A receipt dated before the trip's official start (a pre-trip purchase)
    # or after "today" shouldn't be silently dropped from the day-by-day
    # figures — it should extend the visible window instead.
    receipt_dates = []
    for r in receipts:
        raw = r.get("date") or (r.get("created_at") or "")[:10]
        try:
            receipt_dates.append(datetime.strptime(raw, "%Y-%m-%d").date())
        except (ValueError, TypeError):
            continue
    if receipt_dates:
        start = min([start] + receipt_dates)
        end = max([end] + receipt_dates)

    return start, end


def build_trip_summary(trip: dict, receipts: List[dict]) -> Dict[str, Any]:
    start, end = _trip_date_range(trip, receipts)
    day_count = (end - start).days + 1

    df = pd.DataFrame(receipts)
    if not df.empty:
        df["total"] = pd.to_numeric(df.get("total"), errors="coerce").fillna(0.0)
        df["category"] = df.get("category").fillna("Other") if "category" in df else "Other"
        df["vendor"] = df.get("vendor").fillna("Unknown vendor") if "vendor" in df else "Unknown vendor"
        date_parsed = pd.to_datetime(df.get("date"), format="%Y-%m-%d", errors="coerce")
        fallback_dates = pd.to_datetime(df.get("created_at"), errors="coerce")
        df["date_parsed"] = date_parsed.fillna(fallback_dates)

    total_spent = round(float(df["total"].sum()), 2) if not df.empty else 0.0
    stats = {
        "total_spent": total_spent,
        "receipt_count": int(len(df)),
        "day_count": day_count,
        "avg_daily_spend": round(total_spent / day_count, 2) if day_count else 0.0,
    }

    spent_by_category = df.groupby("category")["total"].sum().to_dict() if not df.empty else {}
    budget_progress = []
    for category, limit in (trip.get("budgets") or {}).items():
        spent = float(spent_by_category.get(category, 0.0))
        budget_progress.append({
            "category": category,
            "limit": limit,
            "spent": round(spent, 2),
            "remaining": round(limit - spent, 2),
            "status": evaluate_status(spent, limit),
        })

    # The declared trip budget, not the sum of category limits — a user can set
    # a total without dividing all of it across categories, so the pace line
    # should track against what they actually committed to, not what's allocated.
    total_budget = float(trip.get("total_budget") or 0)
    allocated_budget = round(sum((trip.get("budgets") or {}).values()), 2)

    return {
        "stats": stats,
        "total_budget": total_budget if total_budget > 0 else None,
        "allocated_budget": allocated_budget,
        "budget_progress": budget_progress,
        "figures": {
            "cumulative_spend": _cumulative_spend_figure(df, start, end, total_budget),
            "by_day": _by_day_figure(df, start, end),
            "by_category": _by_category_figure(spent_by_category),
            "top_vendors": _top_vendors_figure(df),
        },
        "receipts": _build_receipts_list(receipts),
    }


def _build_receipts_list(receipts: List[dict]) -> List[dict]:
    def sort_key(r):
        return r.get("date") or (r.get("created_at") or "")[:10] or ""

    ordered = sorted(receipts, key=sort_key)
    return [
        {
            "_id": r.get("_id"),
            "vendor": r.get("vendor"),
            "date": r.get("date") or (r.get("created_at") or "")[:10],
            "category": r.get("category"),
            "total": round(float(r.get("total") or 0), 2),
            "items": r.get("items", []),
            "source": r.get("source"),
        }
        for r in ordered
    ]


def _daily_totals(df: pd.DataFrame, start: date, end: date) -> tuple:
    """Per-day totals across [start, end], reindexed so days with no receipts
    show as 0 rather than being skipped. Shared by the cumulative chart (which
    cumsums this) and the by-day chart (which uses it directly)."""
    days = pd.date_range(start, end, freq="D")
    if df.empty or "date_parsed" not in df or not df["date_parsed"].notna().any():
        return days, [0.0] * len(days)
    daily = df.groupby(df["date_parsed"].dt.date)["total"].sum()
    totals = [round(float(daily.get(d.date(), 0.0)), 2) for d in days]
    return days, totals


def _cumulative_spend_figure(df: pd.DataFrame, start: date, end: date, total_budget: float) -> Optional[dict]:
    """Running total across the trip — the trend/pace job. A trend needs at
    least two points to say anything, so single-day trips fall back to no
    chart rather than one meaningless dot."""
    days, day_totals = _daily_totals(df, start, end)
    if df.empty or len(days) < 2:
        return None

    cumulative = list(pd.Series(day_totals).cumsum().round(2))
    labels = [d.strftime("%b %d") for d in days]

    fig = go.Figure()
    has_budget = total_budget > 0
    if has_budget:
        pace = [round(total_budget * (i + 1) / len(days), 2) for i in range(len(days))]
        fig.add_trace(go.Scatter(
            x=labels, y=pace, mode="lines", name="Budget pace",
            line=dict(color=CONTEXT_COLOR, width=2, dash="dash"),
            hovertemplate="%{x}: budget pace Rs. %{y:,.2f}<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=labels, y=cumulative, mode="lines+markers", name="Actual spend",
        line=dict(color=TREND_COLOR, width=2),
        marker=dict(size=6, color=TREND_COLOR),
        hovertemplate="%{x}: Rs. %{y:,.2f}<extra></extra>",
    ))

    max_total = max(cumulative + (pace if has_budget else []))
    fig.update_layout(**_base_layout(
        showlegend=has_budget,
        legend=dict(orientation="h", y=1.15, x=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True, gridcolor=GRIDLINE_COLOR, zeroline=False,
            separatethousands=True, tickformat=",.0f", range=[0, max_total * 1.2 if max_total else 1],
        ),
        margin=dict(l=8, r=24, t=40 if has_budget else 8, b=8),
    ))
    return _figure_to_json_safe(fig)


def _by_day_figure(df: pd.DataFrame, start: date, end: date) -> Optional[dict]:
    """Compare-magnitude view of daily spending — a different job from the
    cumulative trend above (which day was biggest vs. the running total), and
    the one the frontend pairs with click-to-drill-down into that day's
    receipts. `customdata` carries the exact ISO date per bar so the frontend
    can match a click back to receipts without re-parsing the display label."""
    if df.empty:
        return None

    days, totals = _daily_totals(df, start, end)
    if len(days) < 2:
        return None

    labels = [d.strftime("%b %d") for d in days]
    iso_dates = [d.strftime("%Y-%m-%d") for d in days]

    fig = go.Figure(go.Bar(
        x=labels, y=totals,
        customdata=iso_dates,
        marker=dict(color=TREND_COLOR),
        text=[f"Rs. {v:,.0f}" for v in totals],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{x}: Rs. %{y:,.2f}<extra></extra>",
    ))
    max_total = max(totals)
    fig.update_layout(**_base_layout(
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True, gridcolor=GRIDLINE_COLOR, zeroline=False,
            separatethousands=True, tickformat=",.0f", range=[0, max_total * 1.2 if max_total else 1],
        ),
        bargap=0.35,
    ))
    return _figure_to_json_safe(fig)


def _by_category_figure(spent_by_category: Dict[str, float]) -> Optional[dict]:
    items = [(c, round(float(v), 2)) for c, v in spent_by_category.items() if v]
    if not items:
        return None

    items.sort(key=lambda x: x[1])
    categories = [c for c, _ in items]
    totals = [t for _, t in items]
    colors = [TRIP_CATEGORY_COLORS.get(c, DEFAULT_CATEGORY_COLOR) for c in categories]

    fig = go.Figure(go.Bar(
        x=totals, y=categories, orientation="h",
        marker=dict(color=colors),
        text=[f"Rs. {t:,.0f}" for t in totals],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}: Rs. %{x:,.2f}<extra></extra>",
    ))
    max_total = max(totals)
    fig.update_layout(**_base_layout(
        xaxis=dict(
            showgrid=True, gridcolor=GRIDLINE_COLOR, zeroline=False,
            separatethousands=True, tickformat=",.0f", range=[0, max_total * 1.2],
        ),
        yaxis=dict(showgrid=False),
        bargap=0.35,
        margin=dict(l=8, r=60, t=8, b=8),
    ))
    return _figure_to_json_safe(fig)


def _top_vendors_figure(df: pd.DataFrame, limit: int = 5) -> Optional[dict]:
    if df.empty:
        return None

    grouped = df.groupby("vendor")["total"].sum().reset_index()
    grouped = grouped.sort_values("total", ascending=False).head(limit)
    if grouped.empty:
        return None
    ordered = grouped.sort_values("total")
    vendors = ordered["vendor"].tolist()
    totals = [round(float(t), 2) for t in ordered["total"]]

    fig = go.Figure(go.Bar(
        x=totals, y=vendors, orientation="h",
        marker=dict(color=TREND_COLOR),
        text=[f"Rs. {t:,.0f}" for t in totals],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}: Rs. %{x:,.2f}<extra></extra>",
    ))
    max_total = max(totals)
    fig.update_layout(**_base_layout(
        xaxis=dict(
            showgrid=True, gridcolor=GRIDLINE_COLOR, zeroline=False,
            separatethousands=True, tickformat=",.0f", range=[0, max_total * 1.2],
        ),
        yaxis=dict(showgrid=False),
        bargap=0.35,
        margin=dict(l=8, r=60, t=8, b=8),
    ))
    return _figure_to_json_safe(fig)
