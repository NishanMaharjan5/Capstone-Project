from datetime import datetime
from typing import Dict, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.constants import TRIP_CATEGORIES
from app.db.connection import receipts_collection, trips_collection, users_collection
from app.routers.auth import verify_password
from app.routers.receipt import get_current_user
from app.services.trip_service import build_trip_summary, build_trip_totals, validate_trip_budgets

router = APIRouter()


class CreateTripRequest(BaseModel):
    name: str
    destination: Optional[str] = None
    start_date: str
    planned_end_date: Optional[str] = None
    total_budget: Optional[float] = None
    budgets: Dict[str, float] = Field(default_factory=dict)


class DeleteTripRequest(BaseModel):
    password: str


def require_known_trip_category(category: str) -> str:
    if category not in TRIP_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}")
    return category


def serialize_trip(trip: dict) -> dict:
    trip = dict(trip)
    trip["_id"] = str(trip["_id"])
    return trip


async def _get_owned_trip(trip_id: str, current_user: dict) -> dict:
    try:
        obj_id = ObjectId(trip_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid trip ID")

    trip = await trips_collection.find_one({"_id": obj_id, "user_id": current_user["sub"]})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/")
async def create_trip(body: CreateTripRequest, current_user: dict = Depends(get_current_user)):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Trip name is required")

    existing_active = await trips_collection.find_one({"user_id": current_user["sub"], "status": "active"})
    if existing_active:
        raise HTTPException(
            status_code=400,
            detail=f"You already have an active trip: {existing_active['name']}. End it before starting a new one.",
        )

    for category in body.budgets:
        require_known_trip_category(category)

    filtered_budgets = {c: amt for c, amt in body.budgets.items() if amt and amt > 0}
    try:
        validate_trip_budgets(body.total_budget, filtered_budgets)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    trip_doc = {
        "user_id": current_user["sub"],
        "name": body.name.strip(),
        "destination": (body.destination or "").strip() or None,
        "start_date": body.start_date,
        "planned_end_date": body.planned_end_date,
        "total_budget": body.total_budget if body.total_budget and body.total_budget > 0 else None,
        "budgets": filtered_budgets,
        "status": "active",
        "ended_at": None,
        "created_at": datetime.now().isoformat(),
    }
    result = await trips_collection.insert_one(trip_doc)
    return {"success": True, "id": str(result.inserted_id)}


@router.get("/active")
async def get_active_trip(current_user: dict = Depends(get_current_user)):
    trip = await trips_collection.find_one({"user_id": current_user["sub"], "status": "active"})
    return {"success": True, "trip": serialize_trip(trip) if trip else None}


@router.get("/")
async def list_trips(current_user: dict = Depends(get_current_user)):
    trips = await trips_collection.find({"user_id": current_user["sub"]}).sort("created_at", -1).to_list(200)

    results = []
    for trip in trips:
        trip_receipts = await receipts_collection.find(
            {"user_id": current_user["sub"], "trip_id": str(trip["_id"])}
        ).to_list(1000)
        serialized = serialize_trip(trip)
        serialized.update(build_trip_totals(trip_receipts))
        results.append(serialized)

    return {"success": True, "trips": results}


@router.get("/{trip_id}")
async def get_trip_detail(trip_id: str, current_user: dict = Depends(get_current_user)):
    trip = await _get_owned_trip(trip_id, current_user)
    receipts = await receipts_collection.find(
        {"user_id": current_user["sub"], "trip_id": trip_id}
    ).to_list(1000)
    for r in receipts:
        r["_id"] = str(r["_id"])

    return {
        "success": True,
        "trip": serialize_trip(trip),
        "summary": build_trip_summary(trip, receipts),
    }


@router.post("/{trip_id}/end")
async def end_trip(trip_id: str, current_user: dict = Depends(get_current_user)):
    trip = await _get_owned_trip(trip_id, current_user)
    if trip["status"] == "ended":
        raise HTTPException(status_code=400, detail="Trip has already ended")

    await trips_collection.update_one(
        {"_id": trip["_id"]},
        {"$set": {"status": "ended", "ended_at": datetime.now().isoformat()}},
    )
    return {"success": True, "message": "Trip ended"}


@router.delete("/{trip_id}")
async def delete_trip(
    trip_id: str,
    body: DeleteTripRequest,
    current_user: dict = Depends(get_current_user),
):
    trip = await _get_owned_trip(trip_id, current_user)
    if trip["status"] != "ended":
        raise HTTPException(status_code=400, detail="End this trip before deleting it")

    user = await users_collection.find_one({"_id": ObjectId(current_user["sub"])})
    if not user or not user.get("password"):
        raise HTTPException(
            status_code=400,
            detail="Password confirmation isn't available for accounts signed in with Google",
        )
    if not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    await trips_collection.delete_one({"_id": trip["_id"]})
    # Deleting a trip removes the trip's own tracking wrapper, not the underlying
    # spending — tagged receipts revert to normal, untagged history entries.
    await receipts_collection.update_many(
        {"user_id": current_user["sub"], "trip_id": trip_id},
        {"$set": {"trip_id": None}},
    )
    return {"success": True, "message": "Trip deleted"}
