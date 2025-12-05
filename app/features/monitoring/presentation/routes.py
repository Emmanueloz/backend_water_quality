from fastapi import APIRouter, Response
from prometheus_client import Counter, generate_latest

monitoring_router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


REQUESTS = Counter("requests_total", "Número total de solicitudes")

@monitoring_router.get("/")
async def home():
    REQUESTS.inc()
    return {"message": "Monitoring Home"}

@monitoring_router.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type="text/plain")

