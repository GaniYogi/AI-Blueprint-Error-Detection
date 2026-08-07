from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


# --- Compliance Rule Schemas ---
class ComplianceRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    default_value: float
    current_value: float
    unit: str
    severity: str

class ComplianceRuleUpdate(BaseModel):
    current_value: float

class ComplianceRuleResponse(ComplianceRuleBase):
    id: int
    rule_key: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Report Schemas ---
class ReportResponse(BaseModel):
    id: int
    blueprint_id: int
    filename: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Analysis Result Schemas ---
class AnalysisResultResponse(BaseModel):
    id: int
    blueprint_id: int
    compliance_score: float
    total_errors: int
    total_violations: int
    raw_json: str  # JSON-stringified detailed dictionary
    created_at: datetime

    class Config:
        from_attributes = True


# --- Blueprint Schemas ---
class BlueprintBase(BaseModel):
    filename: str
    original_name: str
    file_size: int
    content_type: str
    status: str

class BlueprintResponse(BlueprintBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BlueprintDetailResponse(BlueprintResponse):
    analysis_results: Optional[AnalysisResultResponse] = None
    reports: List[ReportResponse] = []

    class Config:
        from_attributes = True


class BlueprintUploadResponse(BaseModel):
    success: bool
    filename: str
    id: int
    message: str

# --- Dashboard Analytics ---
class SeverityCounts(BaseModel):
    Low: int = 0
    Medium: int = 0
    High: int = 0
    Critical: int = 0

class DashboardAnalytics(BaseModel):
    total_blueprints: int
    total_errors: int
    total_violations: int
    average_compliance_score: float
    severity_breakdown: SeverityCounts
    recent_blueprints: List[BlueprintResponse]
    compliance_history: List[Dict[str, Any]]
    
    # CamelCase compatibility
    totalBlueprints: Optional[int] = 0
    completedAnalysis: Optional[int] = 0
    pendingAnalysis: Optional[int] = 0
    complianceScore: Optional[float] = 0.0
