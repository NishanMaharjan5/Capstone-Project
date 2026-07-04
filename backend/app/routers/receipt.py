from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from bson import ObjectId
import os
import shutil
from datetime import datetime
from app.ocr.extractor import receipt_extractor
from app.db.connection import receipts_collection
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# FIXME: same known-public fallback as app/routers/auth.py — must be set via env in production.
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123changemelater")
ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# -- Receipt schemas --
class ReceiptItem(BaseModel):
    name: str
    quantity: float = 1
    unit_price: float = 0
    price: Optional[float] = None


class SaveReceiptRequest(BaseModel):
    vendor: Optional[str] = None
    date: Optional[str] = None
    total: Optional[float] = None
    category: Optional[str] = None
    items: List[ReceiptItem] = Field(default_factory=list)
    verified: Optional[bool] = False
    raw_text: List[str] = Field(default_factory=list)

class ManualReceiptRequest(BaseModel):
    vendor: Optional[str] = None
    date: Optional[str] = None
    total: Optional[float] = None
    category: Optional[str] = None
    items: List[ReceiptItem] = Field(default_factory=list)


def normalize_items(items: List[ReceiptItem]) -> List[dict]:
    normalized = []
    for item in items or []:
        quantity = item.quantity or 1
        unit_price = item.unit_price
        if (unit_price is None or unit_price == 0) and item.price is not None:
            unit_price = item.price / quantity if quantity else item.price
        line_total = quantity * (unit_price or 0)
        normalized.append({
            "name": item.name,
            "quantity": quantity,
            "unit_price": unit_price or 0,
            "price": line_total
        })
    return normalized


def require_category(category: Optional[str]) -> str:
    if not category or not category.strip():
        raise HTTPException(status_code=400, detail="Category is required")
    return category.strip()


def require_manual_receipt(body: ManualReceiptRequest) -> None:
    if not body.vendor or not body.vendor.strip():
        raise HTTPException(status_code=400, detail="Vendor name is required")
    if not body.date:
        raise HTTPException(status_code=400, detail="Receipt date is required")
    if not body.items:
        raise HTTPException(status_code=400, detail="At least one item is required")


@router.post("/upload")
async def upload_receipt(
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{image.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    try:
        text_lines = receipt_extractor.extract_text(file_path)

        if not text_lines:
            raise HTTPException(status_code=400, detail="No text detected in image")

        extracted_data = receipt_extractor.extract_fields(text_lines)

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "success": True,
            "filename": filename,
            "raw_text": text_lines,
            "extracted_data": extracted_data,
            "message": "Receipt analyzed. Confirm to save or discard."
        }

    except HTTPException:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.post("/save")
async def save_receipt(
    body: SaveReceiptRequest,
    current_user: dict = Depends(get_current_user)
):
    receipt_doc = {
        "user_id": current_user["sub"],
        "filename": None,
        "vendor": body.vendor,
        "date": body.date,
        "total": body.total,
        "category": require_category(body.category),
        "items": normalize_items(body.items),
        "verified": body.verified,
        "raw_text": body.raw_text,
        "source": "ocr",
        "created_at": datetime.now().isoformat()
    }
    result = await receipts_collection.insert_one(receipt_doc)
    print(f"✅ Confirmed receipt saved for user {current_user['email']} | id: {result.inserted_id}")
    return {"success": True, "id": str(result.inserted_id), "message": "Receipt saved successfully"}


@router.post("/manual")
async def add_manual_receipt(
    body: ManualReceiptRequest,
    current_user: dict = Depends(get_current_user)
):
    require_manual_receipt(body)
    normalized_items = normalize_items(body.items)
    total = sum(item["price"] for item in normalized_items)

    receipt_doc = {
        "user_id": current_user["sub"],
        "filename": None,
        "vendor": body.vendor.strip(),
        "date": body.date,
        "total": total,
        "category": require_category(body.category),
        "items": normalized_items,
        "verified": True,
        "source": "manual",
        "created_at": datetime.now().isoformat()
    }
    result = await receipts_collection.insert_one(receipt_doc)
    print(f"✅ Manual receipt saved for user {current_user['email']} | id: {result.inserted_id}")
    return {"success": True, "id": str(result.inserted_id), "message": "Receipt added successfully"}


@router.get("/")
async def get_receipts(current_user: dict = Depends(get_current_user)):
    receipts = await receipts_collection.find(
        {"user_id": current_user["sub"]}
    ).sort("created_at", -1).to_list(100)
    for r in receipts:
        r["_id"] = str(r["_id"])
    return {"success": True, "receipts": receipts}


@router.delete("/{receipt_id}")
async def delete_receipt(
    receipt_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        obj_id = ObjectId(receipt_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid receipt ID")

    receipt = await receipts_collection.find_one({"_id": obj_id, "user_id": current_user["sub"]})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    await receipts_collection.delete_one({"_id": obj_id})
    return {"success": True, "message": "Receipt deleted"}
