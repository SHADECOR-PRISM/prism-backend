from fastapi import Request, status
from fastapi.responses import JSONResponse
import traceback
from app.core.config import FRONTEND_URL
from app.core.supabase_retry import NETWORK_ERRORS

async def global_exception_handler(request: Request, exc: Exception):
    print(f"[Global Error Handler] Unhandled Exception: {exc}")
    traceback.print_exc()

    is_network_error = isinstance(exc, NETWORK_ERRORS)
    status_code = (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if is_network_error
        else status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    detail = (
        "認証サーバーとの通信に失敗しました。時間をおいて再試行してください。"
        if is_network_error
        else f"Internal Server Error: {str(exc)}"
    )

    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers={
            "Access-Control-Allow-Origin": FRONTEND_URL,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )