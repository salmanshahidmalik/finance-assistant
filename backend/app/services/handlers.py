import os
import json
import re
from app.services.db import get_supabase
from app.services.ai import simple_chat, complex_chat


def get_user_context(user_id: str) -> str:
    supabase = get_supabase()
    result = supabase.table("user_context").select("key, value").eq("user_id", user_id).execute()
    if not result.data:
        return "No saved preferences."
    return "\n".join([f"- {r['key']}: {r['value']}" for r in result.data])


def get_recent_transactions(user_id: str, limit: int = 50) -> list:
    supabase = get_supabase()
    result = supabase.table("transactions")\
        .select("date, amount, merchant, category")\
        .eq("user_id", user_id)\
        .order("date", desc=True)\
        .limit(limit)\
        .execute()
    return result.data or []


def get_monthly_stats(user_id: str) -> list:
    supabase = get_supabase()
    result = supabase.table("monthly_stats")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("year_month", desc=True)\
        .execute()
    return result.data or []


async def handle_simple_lookup(query: str, user_id: str) -> str:
    transactions = get_recent_transactions(user_id, 100)
    context = get_user_context(user_id)
    prompt = (
        "You are a personal finance assistant. Answer this question using the transaction data below.\n"
        "Be specific with numbers. If you cannot answer from the data, say so clearly.\n\n"
        f"User preferences:\n{context}\n\n"
        f"Recent transactions (JSON):\n{json.dumps(transactions, indent=2)}\n\n"
        f"User question: {query}\n\n"
        "Give a clear, concise answer with specific numbers."
    )
    return await simple_chat(prompt)


async def handle_time_comparison(query: str, user_id: str) -> str:
    stats = get_monthly_stats(user_id)
    context = get_user_context(user_id)
    prompt = (
        "You are a personal finance assistant. Answer this spending comparison question.\n"
        "Use the monthly stats data below. Be specific with numbers and percentages.\n\n"
        f"User preferences:\n{context}\n\n"
        f"Monthly spending stats (JSON):\n{json.dumps(stats, indent=2)}\n\n"
        f"User question: {query}\n\n"
        "Compare the relevant periods clearly. Mention specific numbers."
    )
    return await complex_chat(prompt)


async def handle_pattern_detection(query: str, user_id: str) -> str:
    supabase = get_supabase()
    result = supabase.table("transactions")\
        .select("date, amount, merchant, category")\
        .eq("user_id", user_id)\
        .order("date", desc=True)\
        .limit(200)\
        .execute()
    transactions = result.data or []
    context = get_user_context(user_id)
    prompt = (
        "You are a personal finance assistant. Analyze these transactions and identify:\n"
        "1. Recurring subscriptions (same merchant, similar amount, regular interval)\n"
        "2. Any unusual or suspicious charges\n"
        "3. Patterns the user should know about\n\n"
        f"User preferences:\n{context}\n\n"
        f"Transactions (JSON):\n{json.dumps(transactions, indent=2)}\n\n"
        f"User question: {query}\n\n"
        "List findings clearly with merchant names and amounts."
    )
    return await complex_chat(prompt)


async def handle_budget_query(query: str, user_id: str) -> str:
    supabase = get_supabase()
    budgets = supabase.table("budgets").select("*").eq("user_id", user_id).execute()
    stats = get_monthly_stats(user_id)
    context = get_user_context(user_id)
    prompt = (
        "You are a personal finance assistant helping with budget tracking.\n\n"
        f"User preferences:\n{context}\n\n"
        f"User budgets:\n{json.dumps(budgets.data, indent=2)}\n\n"
        f"Monthly spending stats:\n{json.dumps(stats[:20], indent=2)}\n\n"
        f"User question: {query}\n\n"
        "If they want to set a budget, tell them to use the budget panel on the right.\n"
        "If checking budget status, compare their spending to their limits clearly."
    )
    return await simple_chat(prompt)


async def handle_general_summary(query: str, user_id: str) -> str:
    stats = get_monthly_stats(user_id)
    transactions = get_recent_transactions(user_id, 50)
    context = get_user_context(user_id)
    prompt = (
        "You are a personal finance assistant. Give a clear, friendly summary of this user's finances.\n\n"
        f"User preferences:\n{context}\n\n"
        f"Monthly stats:\n{json.dumps(stats[:24], indent=2)}\n\n"
        f"Recent transactions:\n{json.dumps(transactions[:20], indent=2)}\n\n"
        f"User question: {query}\n\n"
        "Give a warm, helpful summary. Use bullet points. Include:\n"
        "- Top spending categories\n"
        "- Any concerning patterns\n"
        "- One positive observation\n"
        "- One actionable suggestion"
    )
    return await complex_chat(prompt)


async def handle_memory_update(query: str, user_id: str) -> str:
    prompt = (
        "Extract a key-value memory from this user statement.\n"
        "Examples:\n"
        "- 'I get paid on the 1st' -> key: 'payday', value: '1st of each month'\n"
        "- 'Don't count rent in food budget' -> key: 'exclude_from_food', value: 'rent'\n"
        "- 'My monthly income is $3000' -> key: 'monthly_income', value: '3000'\n\n"
        f"User statement: {query}\n\n"
        "Respond with JSON only, no markdown:\n"
        '{"key": "...", "value": "..."}'
    )
    response = await simple_chat(prompt)
    try:
        text = re.sub(r'```json|```', '', response).strip()
        data = json.loads(text)
        supabase = get_supabase()
        supabase.table("user_context").upsert({
            "user_id": user_id,
            "key": data["key"],
            "value": data["value"]
        }).execute()
        return f"Got it! I'll remember that {data['value']}."
    except Exception:
        return "I understood your preference. I'll keep that in mind."


async def handle_merchant_lookup(query: str, user_id: str) -> str:
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        search_prompt = (
            f"Extract the merchant or charge name from this query to search for: {query}\n"
            "Respond with just the search query, nothing else."
        )
        search_term = await simple_chat(search_prompt)
        results = client.search(search_term.strip(), max_results=3)
        context = "\n".join([r.get("content", "") for r in results.get("results", [])])
        prompt = (
            f"The user does not recognize this charge: {query}\n\n"
            f"Web search results:\n{context}\n\n"
            "Explain what this merchant or charge likely is in 2-3 sentences."
        )
        return await simple_chat(prompt)
    except Exception:
        return await simple_chat(
            f"Based on the name, explain what this charge might be: {query}"
        )


async def handle_receipt_vision(query: str, user_id: str, image_data: str = None) -> str:
    if not image_data:
        return "Please upload a receipt image and I'll extract the details for you."
    return (
        "Receipt scanning requires a vision-capable model. "
        "Please type the receipt details manually and I'll record them for you. "
        "For example: 'Add expense: $45.50 at Walmart for Groceries on 2024-03-15'"
    )