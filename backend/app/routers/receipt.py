from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
import shutil
from datetime import datetime
from app.ocr.extractor import receipt_extractor
from app.db.connection import receipts_collection

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


@router.get("/")
async def get_receipts(current_user: dict = Depends(get_current_user)):
    receipts = await receipts_collection.find(
        {"user_id": current_user["sub"]}
    ).to_list(100)
    for r in receipts:
        r["_id"] = str(r["_id"])
    return {"success": True, "receipts": receipts}