from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from datetime import datetime
from app.ocr.extractor import receipt_extractor

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_receipt(image: UploadFile = File(...)):
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
async def get_receipts():
    return {"message": "This will return all receipts from Google Sheets"}