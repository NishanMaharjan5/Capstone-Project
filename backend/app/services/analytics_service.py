import calendar
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go

from app.constants import CATEGORY_COLORS, DEFAULT_CATEGORY_COLOR
from app.services import budget_service

TREND_COLOR = "#2d6ef5"  # app's --accent
CONTEXT_COLOR = "#c3c2b7"  # dataviz skill's neutral gray, for "last month"/reference lines

CHART_FONT = dict(family="Inter, ui-sans-serif, system-ui, -apple-system, sans-serif", color="#4d5565", size=12)
GRIDLINE_COLOR = "#dfe3ec"
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


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
    # fig.to_dict() can leave numpy scalars embedded; round-tripping through
    # Plotly's own JSON encoder guarantees everything is plain-JSON-safe.
    return json.loads(fig.to_json())


def _empty_analytics() -> Dict[str, Any]:
    return {
        "summary": {
            "total_spent": 0.0,
            "receipt_count": 0,
            "average_receipt": 0.0,
            "top_category": None,
            "current_month_total": 0.0,
            "current_month_top_category": None,
        },
        "by_category": [],
        "by_category_comparison": [],
        "by_month": [],
        "by_day_of_week": [],
        "top_vendors": [],
        "insights": [],
        "figures": {
            "category": None,
            "monthly_trend": None,
            "category_comparison": None,
            "pace_projection": None,
            "day_of_week": None,
            "budget_vs_actual": None,
        },
    }


def build_analytics(receipts: List[dict], budgets: Optional[List[dict]] = None) -> Dict[str, Any]:
    if not receipts:
        return _empty_analytics()

    df = pd.DataFrame(receipts)
    df["total"] = pd.to_numeric(df.get("total"), errors="coerce").fillna(0.0)
    df["category"] = df.get("category").fillna("Other") if "category" in df else "Other"
    df["vendor"] = df.get("vendor").fillna("Unknown vendor") if "vendor" in df else "Unknown vendor"

    date_parsed = pd.to_datetime(df.get("date"), format="%Y-%m-%d", errors="coerce")
    # Legacy rows saved before dates were normalized to YYYY-MM-DD (or any
    # other unparseable date) fall back to their upload timestamp.
    fallback_dates = pd.to_datetime(df.get("created_at"), errors="coerce")
    df["date_parsed"] = date_parsed.fillna(fallback_dates)
    df["month"] = df["date_parsed"].dt.strftime("%Y-%m")

    now = datetime.now()
    current_month = now.strftime("%Y-%m")
    last_month = (now.replace(day=1) - pd.Timedelta(days=1)).strftime("%Y-%m")
    current_df = df[df["month"] == current_month]
    last_df = df[df["month"] == last_month]

    by_category = _build_by_category(df)
    by_month = _build_by_month(df)
    by_category_comparison = _build_category_comparison(current_df, last_df)
    by_day_of_week = _build_day_of_week(df)
    pace_series = _build_pace_series(current_df, now)
    budget_figure = budget_service.build_budget_overview(receipts, budgets)["figure"] if budgets else None

    return {
        "summary": _build_summary(df, current_month),
        "by_category": by_category,
        "by_category_comparison": by_category_comparison,
        "top_vendors": _build_top_vendors(df),
        "by_month": by_month,
        "by_day_of_week": by_day_of_week,
        "insights": _build_insights(df, current_df, last_df, by_day_of_week, now, budgets),
        "figures": {
            "category": _category_figure(by_category),
            "monthly_trend": _monthly_trend_figure(by_month),
            "category_comparison": _category_comparison_figure(by_category_comparison),
            "pace_projection": _pace_projection_figure(pace_series),
            "day_of_week": _day_of_week_figure(by_day_of_week),
            "budget_vs_actual": budget_figure,
        },
    }


def _build_summary(df: pd.DataFrame, current_month: str) -> Dict[str, Any]:
    top_category = None
    if not df.empty:
        cat_sums = df.groupby("category")["total"].sum()
        if not cat_sums.empty:
            top_category = cat_sums.idxmax()

    month_df = df[df["month"] == current_month]
    month_top_category = None
    if not month_df.empty:
        month_cat_sums = month_df.groupby("category")["total"].sum()
        if not month_cat_sums.empty:
            month_top_category = month_cat_sums.idxmax()

    return {
        "total_spent": round(float(df["total"].sum()), 2),
        "receipt_count": int(len(df)),
        "average_receipt": round(float(df["total"].mean()), 2) if len(df) else 0.0,
        "top_category": top_category,
        "current_month_total": round(float(month_df["total"].sum()), 2),
        "current_month_top_category": month_top_category,
    }


def _build_by_category(df: pd.DataFrame) -> List[dict]:
    if df.empty:
        return []
    grouped = df.groupby("category")["total"].agg(["sum", "count"]).reset_index()
    grouped = grouped.sort_values("sum", ascending=False)
    return [
        {"category": row["category"], "total": round(float(row["sum"]), 2), "count": int(row["count"])}
        for _, row in grouped.iterrows()
    ]


def _build_by_month(df: pd.DataFrame) -> List[dict]:
    valid = df.dropna(subset=["month"])
    if valid.empty:
        return []
    grouped = valid.groupby("month")["total"].sum().reset_index().sort_values("month").tail(12)
    return [{"month": row["month"], "total": round(float(row["total"]), 2)} for _, row in grouped.iterrows()]


def _build_top_vendors(df: pd.DataFrame, limit: int = 8) -> List[dict]:
    if df.empty:
        return []
    grouped = df.groupby("vendor")["total"].agg(["sum", "count"]).reset_index()
    grouped = grouped.sort_values("sum", ascending=False).head(limit)
    return [
        {"vendor": row["vendor"], "total": round(float(row["sum"]), 2), "count": int(row["count"])}
        for _, row in grouped.iterrows()
    ]


def _build_category_comparison(current_df: pd.DataFrame, last_df: pd.DataFrame) -> List[dict]:
    if current_df.empty and last_df.empty:
        return []

    current_cat = current_df.groupby("category")["total"].sum() if not current_df.empty else pd.Series(dtype=float)
    last_cat = last_df.groupby("category")["total"].sum() if not last_df.empty else pd.Series(dtype=float)
    categories = set(current_cat.index) | set(last_cat.index)
    ordered = sorted(categories, key=lambda c: -(current_cat.get(c, 0) + last_cat.get(c, 0)))

    return [
        {
            "category": c,
            "current": round(float(current_cat.get(c, 0)), 2),
            "previous": round(float(last_cat.get(c, 0)), 2),
        }
        for c in ordered
    ]


def _build_day_of_week(df: pd.DataFrame) -> List[dict]:
    if df.empty:
        return []
    grouped = df.groupby(df["date_parsed"].dt.day_name())["total"].sum()
    grouped = grouped.reindex(DAY_ORDER, fill_value=0.0)
    return [{"day": day, "total": round(float(grouped[day]), 2)} for day in DAY_ORDER]


def _build_pace_series(current_df: pd.DataFrame, now: datetime) -> Optional[dict]:
    if current_df.empty:
        return None

    days_in_month = calendar.monthrange(now.year, now.month)[1]
    days_elapsed = now.day

    daily = current_df.groupby(current_df["date_parsed"].dt.day)["total"].sum()
    daily = daily.reindex(range(1, days_in_month + 1), fill_value=0.0)
    cumulative = daily.cumsum()

    spent_so_far = float(cumulative.loc[days_elapsed]) if days_elapsed in cumulative.index else float(cumulative.iloc[-1])
    daily_rate = spent_so_far / days_elapsed if days_elapsed > 0 else 0.0

    days = list(range(1, days_in_month + 1))
    actual = [round(float(cumulative.loc[d]), 2) if d <= days_elapsed else None for d in days]
    pace = [round(daily_rate * d, 2) for d in days]

    return {"days": days, "actual": actual, "pace": pace, "days_elapsed": days_elapsed}


def _build_insights(
    df: pd.DataFrame,
    current_df: pd.DataFrame,
    last_df: pd.DataFrame,
    by_day_of_week: List[dict],
    now: datetime,
    budgets: Optional[List[dict]] = None,
) -> List[dict]:
    insights: List[dict] = []
    if df.empty:
        return insights

    # Budget alerts are prepended, not appended, so they outrank the rules below
    # in DecisionSupportWidget's top-3 slice — going over budget is more
    # actionable than a day-of-week habit or vendor-frequency nudge.
    if budgets:
        current_cat_totals = (
            current_df.groupby("category")["total"].sum().to_dict() if not current_df.empty else {}
        )
        budget_insights = budget_service.build_budget_insights(current_cat_totals, budgets)
        insights = budget_insights + insights

    if not current_df.empty and not last_df.empty:
        current_cat = current_df.groupby("category")["total"].sum()
        last_cat = last_df.groupby("category")["total"].sum()
        for category, current_total in current_cat.items():
            previous_total = last_cat.get(category, 0)
            if previous_total > 0:
                pct_change = (current_total - previous_total) / previous_total * 100
                if pct_change >= 20:
                    insights.append({
                        "type": "category_increase",
                        "message": f"{category} spending is up {pct_change:.0f}% vs last month.",
                        "detail": (
                            f"You spent Rs. {current_total:,.2f} on {category} this month compared to "
                            f"Rs. {previous_total:,.2f} last month — a {pct_change:.0f}% increase."
                        ),
                        "chart": "category_comparison",
                    })
                elif pct_change <= -20:
                    insights.append({
                        "type": "category_decrease",
                        "message": f"{category} spending is down {abs(pct_change):.0f}% vs last month.",
                        "detail": (
                            f"You spent Rs. {current_total:,.2f} on {category} this month compared to "
                            f"Rs. {previous_total:,.2f} last month — a {abs(pct_change):.0f}% decrease."
                        ),
                        "chart": "category_comparison",
                    })

    if not current_df.empty:
        current_cat_sums = current_df.groupby("category")["total"].sum()
        month_total = float(current_cat_sums.sum())
        if month_total > 0:
            top_cat = current_cat_sums.idxmax()
            share = float(current_cat_sums.max()) / month_total * 100
            insights.append({
                "type": "top_category",
                "message": f"{top_cat} is your biggest expense this month at {share:.0f}% of total spend.",
                "detail": (
                    f"{top_cat} accounts for Rs. {float(current_cat_sums.max()):,.2f} of your "
                    f"Rs. {month_total:,.2f} total spend this month ({share:.0f}%), more than any other category."
                ),
                "chart": "category",
            })

    days_elapsed = now.day
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    spent_so_far = float(current_df["total"].sum())
    if days_elapsed > 0 and spent_so_far > 0:
        projected = budget_service.project_month_end(spent_so_far, days_elapsed, days_in_month)
        last_month_total = float(last_df["total"].sum())
        message = f"At your current pace, you're on track to spend ~Rs. {projected:,.0f} this month."
        if last_month_total > 0 and projected > last_month_total * 1.1:
            delta_pct = (projected - last_month_total) / last_month_total * 100
            message += f" That's {delta_pct:.0f}% more than last month."
        daily_rate = spent_so_far / days_elapsed
        detail = (
            f"You've spent Rs. {spent_so_far:,.2f} over the first {days_elapsed} days of the month, "
            f"a daily average of Rs. {daily_rate:,.2f}. At that rate, you'd spend about Rs. {projected:,.0f} "
            f"by the end of the month."
        )
        insights.append({"type": "pace_projection", "message": message, "detail": detail, "chart": "pace_projection"})

    if not current_df.empty:
        avg_receipt = float(df["total"].mean())
        if avg_receipt > 0:
            largest = current_df.loc[current_df["total"].idxmax()]
            if float(largest["total"]) >= avg_receipt * 2:
                insights.append({
                    "type": "largest_receipt",
                    "message": f"Your largest expense this month was Rs. {float(largest['total']):,.2f} at {largest['vendor']}.",
                    "detail": (
                        f"Your largest single receipt this month was Rs. {float(largest['total']):,.2f} at "
                        f"{largest['vendor']}, more than double your average receipt of Rs. {avg_receipt:,.2f}."
                    ),
                    "chart": None,
                })

    if by_day_of_week:
        top_day = max(by_day_of_week, key=lambda r: r["total"])
        if top_day["total"] > 0:
            insights.append({
                "type": "day_of_week_habit",
                "message": f"{top_day['day']} is your biggest spending day of the week, totaling Rs. {top_day['total']:,.2f}.",
                "detail": (
                    f"Across all your receipts, {top_day['day']} totals Rs. {top_day['total']:,.2f} in spending — "
                    f"more than any other day of the week."
                ),
                "chart": "day_of_week",
            })

    if not current_df.empty:
        vendor_stats = current_df.groupby("vendor").agg(total=("total", "sum"), count=("total", "count"))
        frequent = vendor_stats[vendor_stats["count"] >= 3].sort_values("count", ascending=False)
        if not frequent.empty:
            vendor = frequent.index[0]
            row = frequent.iloc[0]
            insights.append({
                "type": "vendor_frequency",
                "message": (
                    f"You've been to {vendor} {int(row['count'])} times this month, "
                    f"totaling Rs. {float(row['total']):,.2f} — worth checking if that's intentional."
                ),
                "detail": (
                    f"You've visited {vendor} {int(row['count'])} times this month, totaling "
                    f"Rs. {float(row['total']):,.2f} (about Rs. {float(row['total']) / row['count']:,.2f} per visit)."
                ),
                "chart": None,
            })

    if not df.empty:
        last_date = df["date_parsed"].max()
        if pd.notna(last_date):
            days_since = (pd.Timestamp(now) - last_date).days
            if days_since > 7:
                insights.append({
                    "type": "no_recent_activity",
                    "message": f"No receipts logged in the last {days_since} days — add any recent purchases to keep this dashboard accurate.",
                    "detail": (
                        f"Your most recent logged receipt was {days_since} days ago. Add any recent purchases so "
                        f"your analytics and budgets stay accurate."
                    ),
                    "chart": None,
                })

    return insights


def _category_figure(by_category: List[dict]) -> Optional[dict]:
    if not by_category:
        return None

    # Ascending so Plotly (which draws bottom-to-top) puts the biggest category on top.
    ordered = sorted(by_category, key=lambda r: r["total"])
    categories = [r["category"] for r in ordered]
    totals = [r["total"] for r in ordered]
    colors = [CATEGORY_COLORS.get(c, DEFAULT_CATEGORY_COLOR) for c in categories]

    fig = go.Figure(go.Bar(
        x=totals,
        y=categories,
        orientation="h",
        marker=dict(color=colors),
        text=[f"Rs. {t:,.0f}" for t in totals],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}: Rs. %{x:,.2f}<extra></extra>",
    ))
    # Pad the axis range so the outside label on the longest bar has room to
    # render instead of being clipped at the plot edge.
    max_total = max(totals) if totals else 0
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


def _monthly_trend_figure(by_month: List[dict]) -> Optional[dict]:
    if not by_month:
        return None

    months = [r["month"] for r in by_month]
    totals = [r["total"] for r in by_month]

    fig = go.Figure(go.Bar(
        x=months,
        y=totals,
        marker=dict(color=TREND_COLOR),
        text=[f"Rs. {t:,.0f}" for t in totals],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{x}: Rs. %{y:,.2f}<extra></extra>",
    ))
    max_total = max(totals) if totals else 0
    fig.update_layout(**_base_layout(
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True, gridcolor=GRIDLINE_COLOR, zeroline=False,
            separatethousands=True, tickformat=",.0f", range=[0, max_total * 1.2],
        ),
        bargap=0.35,
    ))
    return _figure_to_json_safe(fig)


def _category_comparison_figure(comparison: List[dict]) -> Optional[dict]:
    if not comparison:
        return None

    # Ascending so the biggest category (by current-month spend) sits on top.
    ordered = sorted(comparison, key=lambda r: r["current"])
    categories = [r["category"] for r in ordered]
    previous = [r["previous"] for r in ordered]
    current = [r["current"] for r in ordered]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=categories, x=previous, orientation="h", name="Last month",
        marker=dict(color=CONTEXT_COLOR),
        hovertemplate="%{y} (last month): Rs. %{x:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=categories, x=current, orientation="h", name="This month",
        marker=dict(color=TREND_COLOR),
        hovertemplate="%{y} (this month): Rs. %{x:,.2f}<extra></extra>",
    ))

    max_total = max(previous + current) if (previous or current) else 0
    fig.update_layout(**_base_layout(
        barmode="group",
        showlegend=True,
        legend=dict(orientation="h", y=1.15, x=0),
        xaxis=dict(
            showgrid=True, gridcolor=GRIDLINE_COLOR, zeroline=False,
            separatethousands=True, tickformat=",.0f", range=[0, max_total * 1.2],
        ),
        yaxis=dict(showgrid=False),
        bargap=0.3,
        bargroupgap=0.1,
        margin=dict(l=8, r=24, t=40, b=8),
    ))
    return _figure_to_json_safe(fig)


def _pace_projection_figure(pace_series: Optional[dict]) -> Optional[dict]:
    if not pace_series:
        return None

    days = pace_series["days"]
    actual = pace_series["actual"]
    pace = pace_series["pace"]

    fig = go.Figure()
    # Reference line drawn first so the real (accent) line sits visually on top of it.
    fig.add_trace(go.Scatter(
        x=days, y=pace, mode="lines", name="Projected pace",
        line=dict(color=CONTEXT_COLOR, width=2, dash="dash"),
        hovertemplate="Day %{x}: projected Rs. %{y:,.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=days, y=actual, mode="lines+markers", name="Actual spend",
        line=dict(color=TREND_COLOR, width=2),
        marker=dict(size=6, color=TREND_COLOR),
        hovertemplate="Day %{x}: Rs. %{y:,.2f}<extra></extra>",
    ))

    fig.update_layout(**_base_layout(
        showlegend=True,
        legend=dict(orientation="h", y=1.15, x=0),
        xaxis=dict(showgrid=False, title=dict(text="Day of month")),
        yaxis=dict(
            showgrid=True, gridcolor=GRIDLINE_COLOR, zeroline=False,
            separatethousands=True, tickformat=",.0f",
        ),
        margin=dict(l=8, r=24, t=40, b=32),
    ))
    return _figure_to_json_safe(fig)


def _day_of_week_figure(by_day_of_week: List[dict]) -> Optional[dict]:
    if not by_day_of_week or not any(r["total"] > 0 for r in by_day_of_week):
        return None

    days = [r["day"][:3] for r in by_day_of_week]
    totals = [r["total"] for r in by_day_of_week]

    fig = go.Figure(go.Bar(
        x=days, y=totals,
        marker=dict(color=TREND_COLOR),
        text=[f"Rs. {t:,.0f}" for t in totals],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{x}: Rs. %{y:,.2f}<extra></extra>",
    ))
    max_total = max(totals) if totals else 0
    fig.update_layout(**_base_layout(
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True, gridcolor=GRIDLINE_COLOR, zeroline=False,
            separatethousands=True, tickformat=",.0f", range=[0, max_total * 1.2],
        ),
        bargap=0.35,
    ))
    return _figure_to_json_safe(fig)
