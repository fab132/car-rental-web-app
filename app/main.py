"""Application entry point.

Run locally or in Codespaces with:
    uvicorn app.main:app --reload
Interactive docs: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.errors import ConflictError, NotFoundError
from app.routers import cars, customers, rentals
from app.routers import views
from app.settings import STATIC_DIR

app = FastAPI(
    title="CityCar Rental API",
    version="0.1.0",
    description="Admin CRUD for cars, customers and rentals (Milestone 2).",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.exception_handler(NotFoundError)
def not_found(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(ConflictError)
def conflict(_: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})


app.include_router(views.router)
app.include_router(cars.router)
app.include_router(customers.router)
app.include_router(rentals.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
