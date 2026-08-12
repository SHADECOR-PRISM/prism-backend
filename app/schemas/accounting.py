from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from uuid import UUID
from datetime import date

# ==========================================
# 既存の表示用（Read用）スキーマ（変更禁止エリア）
# ==========================================
class Container(BaseModel):
    id: str
    user_id: str
    project_name: str
    category: str
    applied_at: str
    status: Literal["pending", "approved", "rejected"]
    total_amount: int

# ==========================================
# 1. 交通費明細 (Base / Read / Write)
# ==========================================
class TransportDetailBase(BaseModel):
    usage_date: date
    category: Literal['train', 'bus', 'taxi', 'air', 'other']
    departure: Optional[str] = Field(None, max_length=100)
    arrival: Optional[str] = Field(None, max_length=100)
    is_round_trip: bool = True
    amount: int = Field(gt=0, description="金額は1円以上")

# 登録用（Write）
class TransportDetailCreate(TransportDetailBase):
    id: Optional[UUID] = None

# 表示用（Read）★ 追加！
class TransportDetailResponse(TransportDetailBase):
    id: UUID
    status: Literal["pending", "approved", "rejected"]

    class Config:
        from_attributes = True


# ==========================================
# 2. 一般経費明細 (Base / Read / Write)
# ==========================================
class ExpenseDetailBase(BaseModel):
    usage_date: date
    category: Literal[
        'system_admin', 'supplies', 'software_license', 
        'rental', 'travel_expenses', 'food_beverage', 
        'service_fee', 'others'
    ]
    remark: Optional[str] = Field(None, max_length=100)
    amount: int = Field(gt=0, description="金額は1円以上")

# 登録用（Write）
class ExpenseDetailCreate(ExpenseDetailBase):
    id: Optional[UUID] = None

# 表示用（Read）★ 追加！
class ExpenseDetailResponse(ExpenseDetailBase):
    id: UUID
    status: Literal["pending", "approved", "rejected"]

    class Config:
        from_attributes = True


# 3. 申請ヘッダー (application_headers) 用
class ApplicationHeaderCreate(BaseModel):
    project_id: UUID
    type: Literal['expense', 'income'] = 'expense'  # ENUM: application_type
    category: str = Field(..., max_length=100)      # 例: "交通費", "経費"


# 4. API一括受取用リクエストボディ
class ApplicationCreateRequest(BaseModel):
    header: ApplicationHeaderCreate
    transport_details: Optional[List[TransportDetailCreate]] = None
    expense_details: Optional[List[ExpenseDetailCreate]] = None


# 5. 保存完了レスポンス用
class ApplicationCreateResponse(BaseModel):
    header_id: UUID
    message: str
    total_amount: int


# ==========================================
# 6. コンテナ詳細表示用 (Read用) スキーマ
# ==========================================
class ContainerDetailResponse(BaseModel):
    id: str
    user_id: str
    project_name: str
    category: str
    applied_at: str
    status: Literal["pending", "approved", "rejected"]
    total_amount: int
    transportation_details: List[TransportDetailResponse] = []
    expense_details: List[ExpenseDetailResponse] = []

    class Config:
        from_attributes = True