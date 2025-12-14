from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    message: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="LinkedIn Insights Microservice is running"
    )


@router.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="ok",
        message="Welcome to LinkedIn Insights Microservice API. Visit /docs for documentation."
    )
