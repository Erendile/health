from fastapi import FastAPI

app = FastAPI(
    title="Health Check API",
    description="This API only checks whether the system is up and running.",
    openapi_url="/api/v1/openapi.json",
    redoc_url=None
)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}