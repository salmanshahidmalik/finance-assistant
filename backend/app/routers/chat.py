from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.ai import classify_intent
from app.services.handlers import (
    handle_simple_lookup,
    handle_time_comparison,
    handle_pattern_detection,
    handle_budget_query,
    handle_general_summary,
    handle_memory_update,
    handle_merchant_lookup,
    handle_receipt_vision,
)

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    image_data: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    x_user_id: str = Header(...)
):
    if not request.message.strip():
        raise HTTPException(400, "Message cannot be empty")

    has_image = request.image_data is not None
    intent_data = await classify_intent(request.message, has_image)
    intent = intent_data.get("intent", "general_summary")

    handlers = {
        "simple_lookup": handle_simple_lookup,
        "time_comparison": handle_time_comparison,
        "pattern_detection": handle_pattern_detection,
        "budget_query": handle_budget_query,
        "general_summary": handle_general_summary,
        "memory_update": handle_memory_update,
        "merchant_lookup": handle_merchant_lookup,
    }

    if has_image or intent == "receipt_vision":
        response = await handle_receipt_vision(
            request.message, x_user_id, request.image_data
        )
    elif intent in handlers:
        response = await handlers[intent](request.message, x_user_id)
    else:
        response = await handle_general_summary(request.message, x_user_id)

    # Save to chat history
    from app.services.db import get_supabase
    supabase = get_supabase()
    supabase.table("chat_history").insert([
        {"user_id": x_user_id, "role": "user", "content": request.message},
        {"user_id": x_user_id, "role": "assistant", "content": response}
    ]).execute()

    return ChatResponse(response=response, intent=intent)

@router.get("/history")
async def get_history(x_user_id: str = Header(...)):
    from app.services.db import get_supabase
    supabase = get_supabase()
    result = supabase.table("chat_history")\
        .select("role, content, created_at")\
        .eq("user_id", x_user_id)\
        .order("created_at")\
        .limit(50)\
        .execute()
    return result.data or []