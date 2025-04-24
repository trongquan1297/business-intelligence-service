# from fastapi import APIRouter, Depends
# from app.models import HistoryItem
# from app.dependencies import get_current_user
# from app.services.history_service import save_query_history, load_query_history, delete_query_from_history

# router = APIRouter()

# @router.post("/save", response_model=dict)
# async def save_history(query: QueryResponse, username: str = Depends(get_current_user)):
#     query_id = save_query_history(
#         username, query.question, query.explanation, query.sql_query,
#         query.data, query.suggested_chart_type, query.chart, query.chart_title
#     )
#     return {"query_id": query_id}

# @router.get("/list", response_model=List[HistoryItem])
# async def get_history(username: str = Depends(get_current_user)):
#     return load_query_history(username)

# @router.delete("/{history_id}")
# async def delete_history(history_id: str, username: str = Depends(get_current_user)):
#     delete_query_from_history(history_id)
#     return {"message": "Query deleted successfully"}