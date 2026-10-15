"""Application entry point.

Run locally or in Codespaces with:
    uvicorn app.main:app --reload
Interactive docs: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

app = FastAPI(
    title="CityCar Rental API",
    version="0.1.0",
    description="Admin CRUD for cars, customers and rentals (Milestone 2).",
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
