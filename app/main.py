"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Secure Code Review Bot",
    description="GenAI-Powered Hybrid Security Analysis System",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.webhooks import router as webhook_router
app.include_router(webhook_router)


class HealthResponse(BaseModel):
    status: str
    version: str
    service: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        service="secure-code-review-bot"
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Secure Code Review Bot API",
        "docs": "/docs",
        "health": "/health",
        "webhook": "/webhook/github"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
