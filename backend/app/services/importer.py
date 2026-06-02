import pandas as pd
import re
from datetime import datetime
from app.services.db import get_supabase

def clean_amount(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    val = re.sub(r'[\$,\(\)\s]', '', val)
    try:
        return float(val)
    except:
        return None

def clean_date(val):
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(val, infer_datetime_format=True).strftime('%Y-%m-%d')
    except:
        return None

def deduplicate(df):
    df = df.drop_duplicates(subset=['date', 'amount', 'merchant'])
    return df

def import_csv(file_path: str, user_id: str):
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip')
    except Exception as e:
        return {"error": f"Could not read file: {str(e)}"}

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

    # Try to find required columns
    col_map = {}
    for col in df.columns:
        if 'amount' in col or 'price' in col or 'sum' in col:
            col_map['amount'] = col
        elif 'date' in col or 'time' in col:
            col_map['date'] = col
        elif 'merchant' in col or 'vendor' in col or 'name' in col or 'description' in col:
            col_map['merchant'] = col
        elif 'category' in col or 'type' in col:
            col_map['category'] = col

    if 'amount' not in col_map or 'date' not in col_map:
        return {"error": "Could not find amount or date columns"}

    # Clean data
    df['amount'] = df[col_map['amount']].apply(clean_amount)
    df['date'] = df[col_map['date']].apply(clean_date)
    df['merchant'] = df[col_map.get('merchant', 'merchant')].astype(str) if 'merchant' in col_map else 'Unknown'
    df['category'] = df[col_map.get('category', 'category')].astype(str) if 'category' in col_map else 'Uncategorized'

    # Drop bad rows
    df = df.dropna(subset=['amount', 'date'])
    df = deduplicate(df)

    # Insert into Supabase
    supabase = get_supabase()
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "user_id": user_id,
            "date": row['date'],
            "amount": row['amount'],
            "merchant": str(row['merchant']),
            "category": str(row['category']),
            "source": "csv"
        })

    if rows:
        supabase.table("transactions").insert(rows).execute()

    # Update monthly stats
    update_monthly_stats(user_id)

    return {"imported": len(rows)}

def update_monthly_stats(user_id: str):
    supabase = get_supabase()
    
    # Get all transactions for user
    result = supabase.table("transactions")\
        .select("date, amount, category")\
        .eq("user_id", user_id)\
        .execute()
    
    if not result.data:
        return

    df = pd.DataFrame(result.data)
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.strftime('%Y-%m')
    df['amount'] = pd.to_numeric(df['amount'])

    stats = df.groupby(['year_month', 'category']).agg(
        total=('amount', 'sum'),
        tx_count=('amount', 'count')
    ).reset_index()

    # Delete old stats and reinsert
    supabase.table("monthly_stats").delete().eq("user_id", user_id).execute()
    
    rows = []
    for _, row in stats.iterrows():
        rows.append({
            "user_id": user_id,
            "year_month": row['year_month'],
            "category": row['category'],
            "total": float(row['total']),
            "tx_count": int(row['tx_count'])
        })
    
    if rows:
        supabase.table("monthly_stats").insert(rows).execute()