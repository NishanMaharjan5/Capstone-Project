from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from bson import ObjectId
import os
import shutil
from datetime import datetime
from app.ocr.extractor import receipt_extractor
from app.db.connection import receipts_collection
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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


# ── Manual entry schema ──
class ReceiptItem(BaseModel):
    name: str
    price: float

class ManualReceiptRequest(BaseModel):
    vendor: Optional[str] = None
    date: Optional[str] = None
    total: Optional[float] = None
    items: Optional[List[ReceiptItem]] = []
    confidence: Optional[int] = None


@router.post("/upload")
async def upload_receipt(
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not image.content_type.startswith('image/'):
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

        receipt_doc = {
            "user_id": current_user["sub"],
            "filename": filename,
            "vendor": extracted_data.get("vendor"),
            "date": extracted_data.get("date"),
            "total": extracted_data.get("total"),
            "items": extracted_data.get("items"),
            "verified": extracted_data.get("verified"),
            "confidence": extracted_data.get("confidence"),
            "source": "ocr",
            "created_at": datetime.now().isoformat()
        }
        result = await receipts_collection.insert_one(receipt_doc)
        print(f"✅ Receipt saved for user {current_user['email']} | id: {result.inserted_id}")

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "success": True,
            "filename": filename,
            "raw_text": text_lines,
            "extracted_data": extracted_data,
            "message": "Receipt processed successfully"
        }

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.post("/manual")
async def add_manual_receipt(
    body: ManualReceiptRequest,
    current_user: dict = Depends(get_current_user)
):
    receipt_doc = {
        "user_id": current_user["sub"],
        "filename": None,
        "vendor": body.vendor,
        "date": body.date,
        "total": body.total,
        "items": [item.dict() for item in body.items] if body.items else [],
        "verified": True,
        "confidence": body.confidence,
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