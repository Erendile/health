from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, field_validator
import databases
import os

DATABASE_URL = os.environ["DATABASE_URL"]

database = databases.Database(DATABASE_URL)
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await database.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         SERIAL PRIMARY KEY,
            nickname   VARCHAR(32)  NOT NULL,
            message    VARCHAR(280) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    yield
    await database.disconnect()


app = FastAPI(
    title="Health Check API",
    description="This API only checks whether the system is up and running.",
    openapi_url="/api/v1/openapi.json",
    redoc_url=None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- Schemas ---

class MessageIn(BaseModel):
    nickname: str
    message: str

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("nickname cannot be empty")
        if len(v) > 32:
            raise ValueError("nickname max 32 characters")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty")
        if len(v) > 280:
            raise ValueError("message max 280 characters")
        return v


# --- Endpoints ---

@app.get("/health", tags=["Health"])
@limiter.limit("60/minute")
async def health_check(request: Request):
    return {"status": "healthy"}


@app.get("/test", tags=["Test"])
@limiter.limit("60/minute")
async def test(request: Request):
    return {"status": "test"}


@app.get("/db-status", tags=["Health"])
@limiter.limit("10/minute")
async def db_status(request: Request):
    try:
        await database.fetch_one("SELECT 1")
        return {"status": "connected"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})


@app.post("/messages", tags=["Messages"], status_code=201)
@limiter.limit("10/hour")
async def create_message(request: Request, body: MessageIn):
    query = """
        INSERT INTO messages (nickname, message)
        VALUES (:nickname, :message)
        RETURNING id, nickname, message, created_at
    """
    row = await database.fetch_one(query, values={"nickname": body.nickname, "message": body.message})
    return {
        "id": row["id"],
        "nickname": row["nickname"],
        "message": row["message"],
        "created_at": row["created_at"].isoformat(),
    }


@app.get("/messages", tags=["Messages"])
@limiter.limit("30/minute")
async def list_messages(request: Request):
    rows = await database.fetch_all(
        "SELECT id, nickname, message, created_at FROM messages ORDER BY created_at DESC LIMIT 50"
    )
    return [
        {
            "id": r["id"],
            "nickname": r["nickname"],
            "message": r["message"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]