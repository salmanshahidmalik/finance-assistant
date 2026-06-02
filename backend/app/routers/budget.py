from fastapi import APIRouter, Header
from pydantic import BaseModel
from app.services.db import get_supabase

router = APIRouter(prefix="/budget", tags=["budget"])

class BudgetCreate(BaseModel):
    category: str
    amount: float
    period: str = "monthly"

@router.post("/")
async def create_budget(budget: BudgetCreate, x_user_id: str = Header(...)):
    supabase = get_supabase()
    result = supabase.table("budgets").upsert({
        "user_id": x_user_id,
        "category": budget.category,
        "amount": budget.amount,
        "period": budget.period
    }).execute()
    return {"status": "saved"}

@router.get("/")
async def get_budgets(x_user_id: str = Header(...)):
    supabase = get_supabase()
    budgets = supabase.table("budgets").select("*").eq("user_id", x_user_id).execute()
    stats = supabase.table("monthly_stats")\
        .select("*")\
        .eq("user_id", x_user_id)\
        .order("year_month", desc=True)\
        .limit(50)\
        .execute()

    from datetime import datetime
    current_month = datetime.now().strftime('%Y-%m')
    current_stats = [s for s in (stats.data or []) if s['year_month'] == current_month]
    spending_by_category = {s['category']: s['total'] for s in current_stats}

    result = []
    for b in (budgets.data or []):
        spent = spending_by_category.get(b['category'], 0)
        result.append({
            **b,
            "spent": spent,
            "remaining": b['amount'] - spent,
            "percentage": round((spent / b['amount']) * 100, 1) if b['amount'] > 0 else 0
        })

    return result