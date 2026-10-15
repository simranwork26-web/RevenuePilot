from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.analytics import router as analytics_router
from backend.kpis import router as kpis_router

app = FastAPI(
    title="RevenuePilot API",
    description="Revenue decision intelligence for e-commerce analytics.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(kpis_router)
app.include_router(analytics_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "RevenuePilot API"}
