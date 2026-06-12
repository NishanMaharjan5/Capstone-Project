from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers.receipt import router as receipts_router
from app.routers.auth import router as auth_router
import os
from app.db.connection import db

os.makedirs("uploads", exist_ok=True)

app = FastAPI(
    title="Smart Receipt Analyzer",
    description="OCR-based expense tracking system",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    try:
        await db.command("ping")
        print("✅ Connected to MongoDB!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://127.0.0.1:5500", "null"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(receipts_router, prefix="/api/receipts", tags=["receipts"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "receipt-analyzer"}

# Mount MUST be last
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)