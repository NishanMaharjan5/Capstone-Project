from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.constants import CATEGORIES
from app.db.connection import budgets_collection, monthly_budgets_collection, receipts_collection
from app.routers.receipt import get_current_user
from app.services.budget_service import build_budget_overview, current_month_total, split_trip_receipts
from app.services.decision_engine_service import build_suggestions

router = APIRouter()


class SetBudgetRequest(BaseModel):
    category: str
    monthly_limit: float


class ClearBudgetRequest(BaseModel):
    category: str


class SetMonthlyBudgetRequest(BaseModel):
    amount: float


def require_known_category(category: str) -> str:
    if category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}")
    return category


async def _get_monthly_budget_amount(user_id: str):
    doc = await monthly_budgets_collection.find_one({"user_id": user_id})
    return doc["amount"] if doc else None


async def _total_allocated(user_id: str, exclude_category: str = None) -> float:
    budgets = await budgets_collection.find({"user_id": user_id}).to_list(100)
    return sum(
        b.get("monthly_limit", 0) for b in budgets if b["category"] != exclude_category
    )


@router.get("/")
async def get_budget_overview(current_user: dict = Depends(get_current_user)):
    budgets = await budgets_collection.find({"user_id": current_user["sub"]}).to_list(100)
    receipts = await receipts_collection.find({"user_id": current_user["sub"]}).to_list(1000)
    non_trip_receipts, trip_receipts = split_trip_receipts(receipts)
    total_monthly_budget = await _get_monthly_budget_amount(current_user["sub"])

    overview = build_budget_overview(non_trip_receipts, budgets, total_monthly_budget)
    overview["summary"]["trip_spent_this_month"] = current_month_total(trip_receipts)
    return {"success": True, "budget_overview": overview}


@router.get("/monthly")
async def get_monthly_budget(current_user: dict = Depends(get_current_user)):
    amount = await _get_monthly_budget_amount(current_user["sub"])
    return {"success": True, "amount": amount}


@router.put("/monthly")
async def set_monthly_budget(body: SetMonthlyBudgetRequest, current_user: dict = Depends(get_current_user)):
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Monthly budget must be greater than zero")

    allocated = await _total_allocated(current_user["sub"])
    if body.amount < allocated:
        raise HTTPException(
            status_code=400,
            detail=(
                f"You've already allocated Rs. {allocated:,.2f} across categories — reduce those first if you "
                f"want a lower monthly budget."
            ),
        )

    await monthly_budgets_collection.update_one(
        {"user_id": current_user["sub"]},
        {"$set": {"amount": body.amount, "updated_at": datetime.now().isoformat()}},
        upsert=True,
    )
    return {"success": True, "message": "Monthly budget saved"}


@router.get("/suggestions")
async def get_budget_suggestions(current_user: dict = Depends(get_current_user)):
    budgets = await budgets_collection.find({"user_id": current_user["sub"]}).to_list(100)
    receipts = await receipts_collection.find({"user_id": current_user["sub"]}).to_list(1000)
    non_trip_receipts, _ = split_trip_receipts(receipts)
    return {"success": True, "decision_support": build_suggestions(non_trip_receipts, budgets)}


@router.put("/")
async def set_budget(body: SetBudgetRequest, current_user: dict = Depends(get_current_user)):
    require_known_category(body.category)
    if body.monthly_limit <= 0:
        raise HTTPException(status_code=400, detail="Monthly limit must be greater than zero")

    total_monthly_budget = await _get_monthly_budget_amount(current_user["sub"])
    if not total_monthly_budget:
        raise HTTPException(
            status_code=400,
            detail="Set your monthly budget first, then divide it across categories.",
        )

    already_allocated = await _total_allocated(current_user["sub"], exclude_category=body.category)
    remaining = total_monthly_budget - already_allocated
    if body.monthly_limit > remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Only Rs. {remaining:,.2f} left to allocate — lower this amount or free up room in another category.",
        )

    await budgets_collection.update_one(
        {"user_id": current_user["sub"], "category": body.category},
        {"$set": {"monthly_limit": body.monthly_limit, "updated_at": datetime.now().isoformat()}},
        upsert=True,
    )
    return {"success": True, "message": "Budget saved"}


@router.delete("/")
async def clear_budget(body: ClearBudgetRequest, current_user: dict = Depends(get_current_user)):
    require_known_category(body.category)
    await budgets_collection.delete_one({"user_id": current_user["sub"], "category": body.category})
    return {"success": True, "message": "Budget cleared"}
