import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class OperationRequest(BaseModel):
    user_role: Literal["FAN", "ORGANIZER", "VOLUNTEER", "STAFF"]
    telemetry_stream: str = Field(..., max_length=5000)

    @field_validator("telemetry_stream")
    @classmethod
    def sanitize_and_check_injection(cls, v: str) -> str:
        # Strip simple HTML tags to sanitize the stream
        sanitized = re.sub(r"<[^>]*>", "", v)
        
        # Define known prompt injection patterns (case-insensitive checks)
        injection_patterns = [
            r"ignore\s+(?:all\s+|previous\s+|the\s+)?instructions",
            r"disregard\s+(?:all\s+|previous\s+|the\s+)?instructions",
            r"override\s+system",
            r"system\s+override",
            r"forget\s+(?:all\s+|previous\s+|the\s+)?instructions",
            r"you\s+are\s+now\s+(?:a|an)\b",
            r"new\s+role",
            r"ignore\s+above",
            r"ignore\s+below",
            r"stop\s+following\s+instructions",
            r"assistant\s+should\s+now\b"
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise ValueError("Potential prompt injection attempt detected.")
        
        return sanitized

class OperationResponse(BaseModel):
    alert_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    recommendation: str = Field(..., description="Tailored operational recommendation based on role and telemetry.")
    accessibility_routing: str = Field(..., description="ADA routing details or standard accessibility route info.")
