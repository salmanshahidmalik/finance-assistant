from app.services.ai import classify_intent

async def route_query(query: str, user_id: str, has_image: bool = False):
    intent = await classify_intent(query, has_image)
    return intent