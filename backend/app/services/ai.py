import os
import re
import json
from groq import Groq

def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

async def classify_intent(query: str, has_image: bool = False) -> dict:
    client = get_client()
    prompt = (
        "Classify this finance query into exactly one category:\n"
        "- simple_lookup: specific amounts, counts, dates\n"
        "- time_comparison: comparing periods, trends, more than usual\n"
        "- pattern_detection: subscriptions, recurring charges, anomalies\n"
        "- receipt_vision: user uploaded a receipt image\n"
        "- merchant_lookup: user does not recognize a charge\n"
        "- budget_query: about budgets or spending limits\n"
        "- memory_update: user is telling assistant something to remember\n"
        "- general_summary: broad overview of finances\n\n"
        f"Query: {query}\n"
        f"Has image: {has_image}\n\n"
        "Respond with JSON only, no markdown:\n"
        '{"intent": "...", "confidence": 0.0, "entities": {}}'
    )
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    text = re.sub(r'```json|```', '', response.choices[0].message.content).strip()
    try:
        return json.loads(text)
    except Exception:
        return {"intent": "general_summary", "confidence": 0.5, "entities": {}}

async def simple_chat(prompt: str) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


async def complex_chat(prompt: str) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content