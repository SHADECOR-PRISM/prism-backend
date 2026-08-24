from datetime import datetime
from typing import Any


def parse_iso_date_to_string(date_val: Any) -> str:
    """
    Supabase や DB から取得した様々な形式の日時データ
    ('2026-08-06 05:35:01.945563+00', '2026-08-06T05:35:01Z', datetimeオブジェクトなど)
    を安全に 'YYYY/MM/DD' 形式の文字列へ変換する共通関数
    """
    if not date_val:
        return ""

    if isinstance(date_val, datetime):
        return date_val.strftime("%Y/%m/%d")

    val_str = str(date_val).strip()
    try:
        # スペース区切りの場合、'T' に置換
        val_str = val_str.replace(" ", "T")

        # 'Z' や '+00' などのタイムゾーン表記を Python 互換（+00:00）に補正
        if val_str.endswith("Z"):
            val_str = val_str[:-1] + "+00:00"
        elif val_str.endswith("+00"):
            val_str = val_str[:-3] + "+00:00"

        return datetime.fromisoformat(val_str).strftime("%Y/%m/%d")
    except Exception:
        # パースに失敗した場合の安全なフォールバック (先頭10桁 YYYY-MM-DD をハイフンからスラッシュへ)
        return val_str[:10].replace("-", "/")