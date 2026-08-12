from fastapi import Request, status
from fastapi.responses import JSONResponse
import traceback
from app.core.config import FRONTEND_URL

async def global_exception_handler(request: Request, exc: Exception):
    print(f"[Global Error Handler] Unhandled Exception: {exc}")
    traceback.print_exc()
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": FRONTEND_URL,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )