import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class OperationRequest(BaseModel):
    user_role: Literal["FAN", "ORGANIZER", "VOLUNTEER", "STAFF"] = Field(
        ...,
        description="The operational role of the requester, determining tailored recommendations and access constraints. Must be one of the permitted stadium roles: FAN, ORGANIZER, VOLUNTEER, or STAFF."
    )
    telemetry_stream: str = Field(
        ...,
        max_length=5000,
        description="A stream of live telemetry data containing stadium operational metrics, crowd dynamics, incident details, or general queries. Used as input for security and threat analysis."
    )

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
    alert_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        ...,
        description="Calculated operational threat level and threat classification representing the urgency of the detected stadium incident. Must be one of: LOW, MEDIUM, HIGH, or CRITICAL."
    )
    recommendation: str = Field(
        ...,
        description="Tailored operational instruction and coordination directives customized for the user's role and telemetry input to mitigate threats and guide response."
    )
    accessibility_routing: str = Field(
        ...,
        description="Barrier-free, ADA-compliant routing path details and navigation instructions for fans requiring special assistance, wheelchair access, or elevators."
    )
