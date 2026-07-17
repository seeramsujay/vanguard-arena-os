import json
import logging
import os
import re
from fastapi import FastAPI, Header, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai

from app.prompts import STADIUM_COMMAND_SYSTEM_PROMPT
from app.schemas import OperationRequest, OperationResponse

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vanguard_arena")

load_dotenv()

app = FastAPI(
    title="Vanguard Arena OS",
    description="Production-ready Python backend for FIFA World Cup 2026 stadium operations and fan experience",
    version="1.0.0"
)
@app.get("/", include_in_schema=False)
async def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")
@app.get(
    "/",
    summary="System Health Check and Welcome",
    description="Serves as the system health check and developer welcome route, providing status information and interactive API documentation references."
)
async def root() -> dict[str, str]:
    """
    Root endpoint offering a welcome message and redirect coordinates 
    to the interactive API documentation.
    """
    return {
        "status": "Vanguard Arena OS is fully operational",
        "tournament": "FIFA World Cup 2026™ Stadium Operations AI Support",
        "interactive_docs": "/docs",
        "system_engine": "Gemini 1.5 Flash (Async Mode)"
    }

# Robust CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "fallback-secret-token")

def verify_arena_token(x_arena_token: str | None = Header(None, alias="X-Arena-Token")) -> str:
    """
    Security check for incoming requests. Validates the API token from header.
    """
    if not x_arena_token or x_arena_token != INTERNAL_API_TOKEN:
        logger.warning(f"Unauthorized request attempted with token: {x_arena_token}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Invalid or missing X-Arena-Token header"
        )
    return x_arena_token

def generate_mock_response(request: OperationRequest) -> OperationResponse:
    """
    Fallback mock response generator when GEMINI_API_KEY is not configured.
    Provides robust, localized, and role-based responses for testing/dev environments.
    """
    role = request.user_role
    telemetry = request.telemetry_stream.lower()
    
    # Check for Spanish queries
    is_spanish = any(word in telemetry for word in ["ayuda", "silla", "ruedas", "rampa", "ascensor", "puerta", "lleno", "congestión", "seguridad"])
    
    alert_level = "LOW"
    
    if is_spanish:
        recommendation = "Las operaciones del estadio funcionan con normalidad. Bienvenido a la Copa Mundial de la FIFA 2026."
        accessibility_routing = "Todas las rampas y ascensores accesibles en las Puertas A, B y C están en pleno funcionamiento."
    else:
        recommendation = "Stadium operations running normally. Welcome to the FIFA World Cup 2026."
        accessibility_routing = "All accessible ramps and elevators at Gates A, B, and C are fully operational."

    # Critical/Emergency checks
    if any(word in telemetry for word in ["fire", "smoke", "emergency", "injury", "fuego", "humo", "emergencia", "lesion"]):
        alert_level = "CRITICAL"
        if role == "FAN":
            recommendation = "¡EVACUAR DE INMEDIATO! Diríjase a la salida más cercana y siga al personal de seguridad." if is_spanish else "EVACUATE IMMEDIATELY! Proceed to the nearest exit and follow security staff instructions."
        elif role in ["STAFF", "ORGANIZER"]:
            recommendation = "Activar protocolos de emergencia, notificar a despacho y evacuar la zona afectada." if is_spanish else "Trigger emergency protocol, notify dispatch, and clear the affected zone."
        else: # VOLUNTEER
            recommendation = "Ayude a dirigir a los fans a las salidas y repórtese con su supervisor inmediatamente." if is_spanish else "Guide fans toward exits immediately and report to supervisor."
        accessibility_routing = "El elevador de emergencia está reservado para personal de rescate. Use rampas de evacuación lateral." if is_spanish else "Emergency elevators are reserved for response teams. Use lateral evacuation ramps."
        
    # Crowding checks
    elif any(word in telemetry for word in ["crowd", "gate a", "congestion", "blocked", "jam", "puerta a", "bloqueado", "embotellamiento"]):
        alert_level = "HIGH"
        if role == "FAN":
            recommendation = "La Puerta A está muy congestionada. Vaya a la Puerta G (espera < 5 mins)." if is_spanish else "Gate A is highly congested. Please proceed to Gate G (under 5 min wait)."
        elif role in ["STAFF", "VOLUNTEER"]:
            recommendation = "Redirigir flujo peatonal de Puerta A a Puerta G y colocar barreras." if is_spanish else "Redirect incoming flow from Gate A to Gate G and place queue barriers."
        else: # ORGANIZER
            recommendation = "Monitorear la saturación de Puerta A y desplegar más personal a Puerta G." if is_spanish else "Monitor Gate A saturation and dispatch additional ticket scanning staff to Gate G."
        accessibility_routing = "La Puerta G cuenta con carriles ADA dedicados y rampas niveladas." if is_spanish else "Gate G has dedicated, step-free ADA lanes and level access ramps."

    # Accessibility/ADA checks
    elif any(word in telemetry for word in ["wheelchair", "ada", "elevator", "ramp", "silla", "ruedas", "ascensor", "rampa"]):
        alert_level = "MEDIUM"
        if role == "FAN":
            recommendation = "Para asistencia, diríjase al mostrador de servicios de accesibilidad cerca de la entrada principal." if is_spanish else "For assistance, proceed to the accessibility guest services desk near the main entrance."
        elif role in ["STAFF", "VOLUNTEER"]:
            recommendation = "Asistir al fan en silla de ruedas hacia el ascensor del ala norte." if is_spanish else "Assist the wheelchair-bound fan to the North wing elevator."
        else: # ORGANIZER
            recommendation = "Verificar que todos los accesos ADA del sector este estén despejados." if is_spanish else "Verify all ADA access points on the east concourse remain clear."
        
        accessibility_routing = "Use el ascensor en la Sección 104 para subir al Nivel 2. Los asientos accesibles están en la Sección 202." if is_spanish else "Use the elevator at Section 104 to reach Level 2. Accessible seating is in Section 202."

    return OperationResponse(
        alert_level=alert_level,
        recommendation=recommendation,
        accessibility_routing=accessibility_routing
    )

_cached_model = None

@app.post(
    "/api/v1/operations/analyze",
    response_model=OperationResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_arena_token)],
    summary="Analyze Live Stadium Telemetry",
    description="Processes real-time stadium operational streams to categorize threats, generate coordination instructions, and extract barrier-free routing path parameters.",
    response_description="A structured JSON response containing the calculated operational threat level, immediate action directives, and ADA-compliant pathways."
)
async def analyze_operation(request: OperationRequest) -> OperationResponse:
    """
    Analyzes stadium operations telemetry or user queries using Gemini 1.5 Flash asynchronously.
    Falls back to a structured mock response if the Gemini API Key is missing or invalid.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.info("GEMINI_API_KEY env is missing. Gracefully falling back to mock response.")
        return generate_mock_response(request)

    try:
        global _cached_model
        if _cached_model is None:
            genai.configure(api_key=api_key)
            _cached_model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=STADIUM_COMMAND_SYSTEM_PROMPT
            )
        model = _cached_model
        
        prompt_content = f"User Role: {request.user_role}\nTelemetry Stream: {request.telemetry_stream}"
        
        # Call the asynchronous SDK method to prevent event loop blocking
        response = await model.generate_content_async(
            prompt_content,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        # Process and clean potential markdown response wrappers
        response_text = response.text.strip()
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()
            
        data = json.loads(response_text)
        return OperationResponse(**data)
        
    except Exception as e:
        logger.error(f"Error executing Gemini async operation: {e}. Falling back to mock.")
        return generate_mock_response(request)
