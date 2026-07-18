from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.routers.receipt import router as receipts_router
from app.routers.auth import router as auth_router
from app.routers.budget import router as budget_router
from app.routers.trip import router as trip_router
import os
from app.db.connection import db


class SPAStaticFiles(StaticFiles):
    """Serves the built React app, falling back to index.html for
    client-side routes (e.g. /history, /login) on a hard refresh."""

    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            raise ex

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
    allow_origins=[
        "*",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "null"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(receipts_router, prefix="/api/receipts", tags=["receipts"])
app.include_router(budget_router, prefix="/api/budgets", tags=["budgets"])
app.include_router(trip_router, prefix="/api/trips", tags=["trips"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "receipt-analyzer"}

# Mount MUST be last. Only present after `npm run build` — skip it during
# local dev where the frontend runs separately via `npm run dev` on :5173.
frontend_dist = "../frontend/dist"
if os.path.isdir(frontend_dist):
    app.mount("/", SPAStaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    print(f"⚠️  {frontend_dist} not found — skipping frontend mount (fine for local dev, run `npm run build` before deploying)")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)