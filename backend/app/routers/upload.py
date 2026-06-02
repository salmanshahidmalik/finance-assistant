from fastapi import APIRouter, UploadFile, File, Header, HTTPException
import tempfile, os
from app.services.importer import import_csv

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/csv")
async def upload_csv(
    file: UploadFile = File(...),
    x_user_id: str = Header(...)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Only CSV files accepted")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        result = import_csv(tmp_path, x_user_id)
    finally:
        os.unlink(tmp_path)
    
    return result