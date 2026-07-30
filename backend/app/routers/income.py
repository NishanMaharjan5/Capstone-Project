from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db.connection import income_collection
from app.routers.receipt import get_current_user

router = APIRouter()


class AddIncomeRequest(BaseModel):
    amount: float
    source: str
    date: Optional[str] = None


def serialize_income(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.get("/")
async def list_income(current_user: dict = Depends(get_current_user)):
    entries = await income_collection.find(
        {"user_id": current_user["sub"]}
    ).sort("date", -1).to_list(1000)

    items = [serialize_income(e) for e in entries]
    total = sum(item.get("amount", 0) for item in items)
    return {"success": True, "items": items, "total": total}


@router.post("/")
async def add_income(body: AddIncomeRequest, current_user: dict = Depends(get_current_user)):
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")
    if not body.source or not body.source.strip():
        raise HTTPException(status_code=400, detail="Source is required")

    income_doc = {
        "user_id": current_user["sub"],
        "amount": body.amount,
        "source": body.source.strip(),
        "date": body.date or datetime.now().strftime("%Y-%m-%d"),
        "created_at": datetime.now().isoformat(),
    }
    result = await income_collection.insert_one(income_doc)
    return {"success": True, "id": str(result.inserted_id), "message": "Income added"}


@router.delete("/{income_id}")
async def delete_income(income_id: str, current_user: dict = Depends(get_current_user)):
    try:
        obj_id = ObjectId(income_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid income ID")

    entry = await income_collection.find_one({"_id": obj_id, "user_id": current_user["sub"]})
    if not entry:
        raise HTTPException(status_code=404, detail="Income entry not found")

    await income_collection.delete_one({"_id": obj_id})
    return {"success": True, "message": "Income entry deleted"}
