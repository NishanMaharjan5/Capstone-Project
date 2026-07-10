from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.constants import CATEGORIES
from app.db.connection import budgets_collection, receipts_collection
from app.routers.receipt import get_current_user
from app.services.budget_service import build_budget_overview
from app.services.decision_engine_service import build_suggestions

router = APIRouter()


class SetBudgetRequest(BaseModel):
    category: str
    monthly_limit: float


class ClearBudgetRequest(BaseModel):
    category: str


def require_known_category(category: str) -> str:
    if category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}")
    return category


@router.get("/")
async def get_budget_overview(current_user: dict = Depends(get_current_user)):
    budgets = await budgets_collection.find({"user_id": current_user["sub"]}).to_list(100)
    receipts = await receipts_collection.find({"user_id": current_user["sub"]}).to_list(1000)
    return {"success": True, "budget_overview": build_budget_overview(receipts, budgets)}


@router.get("/suggestions")
async def get_budget_suggestions(current_user: dict = Depends(get_current_user)):
    budgets = await budgets_collection.find({"user_id": current_user["sub"]}).to_list(100)
    receipts = await receipts_collection.find({"user_id": current_user["sub"]}).to_list(1000)
    return {"success": True, "decision_support": build_suggestions(receipts, budgets)}


@router.put("/")
async def set_budget(body: SetBudgetRequest, current_user: dict = Depends(get_current_user)):
    require_known_category(body.category)
    if body.monthly_limit <= 0:
        raise HTTPException(status_code=400, detail="Monthly limit must be greater than zero")

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
