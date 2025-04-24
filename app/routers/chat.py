from fastapi import APIRouter, Depends, HTTPException
from app.models import QueryRequest, QueryResponse
from app.dependencies import get_current_user
from app.services.query_service import handle_query

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, username: str = Depends(get_current_user)):
    try:
        result = handle_query(request.question, username)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")