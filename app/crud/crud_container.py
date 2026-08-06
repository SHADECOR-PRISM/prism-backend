from datetime import datetime
from app.db.session import supabase
from app.models.models import ApplicationHeader
from typing import cast, Dict, Any
import app.core.config as config

def get_user_container(user_id: str, start: datetime, end: datetime, offset: int):
    # ISOフォーマット文字列を生成（タイムゾーンが含まれていない場合はZや明示的なISO形式にする）
    start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%S")

    response = (
        supabase.table("application_header")
        .select("*")
        .eq("user_id", user_id)
        # ISO文字列比較または日付指定比較を確実に行う
        .gte("applied_at", start_str)
        .lt("applied_at", end_str)
        .order("applied_at", desc=True)
        .range(offset, offset + config.FETCH_LIMIT - 1)
        .execute()
    )
    
    return [ApplicationHeader(**cast(Dict[str, Any], item)) for item in response.data]