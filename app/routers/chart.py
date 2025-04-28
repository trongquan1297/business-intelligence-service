from fastapi import APIRouter, Depends, HTTPException
from app.model.chart import ChartModel
from app.model.chart_query import ChartQueryModel
from app.dependencies import get_current_user
from config import REDSHIFT_CONFIG
from app.schemas.chart import ChartCreate, ChartUpdate, ChartResponse, ChartDataResponse, ChartListResponse
from app.schemas.dashboard import ShareRequest, ShareResponse, SharedUsersResponse
from app.schemas.chart_query import ChartQueryRequest, ChartQueryResponse

router = APIRouter()
# Chart routes
@router.post("/", response_model=ChartResponse)
async def create_chart(chart: ChartCreate, current_user: str = Depends(get_current_user)):
    """
    Create a new chart with name, query, and config.
    Requires JWT authentication and chart details in the request body.
    """
    chart_id = ChartModel.create_chart(chart.dict(), current_user)
    chart_data = ChartModel.get_chart(chart_id, current_user)
    return {
        "id": chart_id,
        "name": chart.name,
        "dataset_id": chart_data["dataset_id"],
        "owner": chart_data["owner"],
        "message": "Chart created successfully"
    }

@router.put("/{chart_id}", response_model=ChartResponse)
async def update_chart(chart_id: int, chart: ChartUpdate, current_user: str = Depends(get_current_user)):
    """
    Update an existing chart by ID.
    Requires JWT authentication and updated chart details in the request body.
    """
    success = ChartModel.update_chart(chart_id, chart.dict(exclude_unset=True), current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Chart not found")
    chart_data = ChartModel.get_chart(chart_id)
    return {
        "id": chart_id,
        "name": chart_data["name"],
        "dataset_id": chart_data["dataset_id"],
        "owner": current_user,
        "message": "Chart updated successfully"
    }

@router.delete("/delete/{chart_id}", response_model=ChartResponse)
async def delete_chart(chart_id: int, current_user: str = Depends(get_current_user)):
    """
    Delete a chart by ID.
    Requires JWT authentication.
    """
    chart_data = ChartModel.get_chart(chart_id, current_user)
    if not chart_data:
        raise HTTPException(status_code=404, detail="Chart not found")
    success = ChartModel.delete_chart(chart_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Chart not found")
    return {
        "id": chart_id,
        "name": chart_data["name"],
        "dataset_id": chart_data["dataset_id"],
        "owner": chart_data["owner"],
        "message": "Chart deleted successfully"
    }

@router.get("/get", response_model=ChartListResponse)
async def get_charts(current_user: str = Depends(get_current_user)):
    """
    Retrieve a list of all charts with schema_name.
    Requires JWT authentication.
    """
    charts = ChartModel.get_all_charts(current_user)
    return {"charts": charts}


@router.get("/{chart_id}", response_model=ChartDataResponse)
async def get_chart_data(chart_id: int, current_user: str = Depends(get_current_user)):
    """
    Retrieve a chart and its data for Chart.js rendering with schema_name.
    Requires JWT authentication.
    """
    chart = ChartModel.get_chart(chart_id, current_user)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    data = ChartModel.get_chart_data(chart_id, REDSHIFT_CONFIG, current_user)
    return {
        "chart": chart,
        "data": data
    }

# Chart query route
@router.post("/query", response_model=ChartQueryResponse)
async def build_and_execute_chart_query(query: ChartQueryRequest, current_user: str = Depends(get_current_user)):
    """
    Build and execute a SQL query on Redshift for a chart.
    Returns Chart.js-compatible data with labels and values.
    Requires JWT authentication and query details in the request body.
    """
    chart_data = ChartQueryModel.build_and_execute_query(query.dict(), REDSHIFT_CONFIG)
    return chart_data

@router.post("/{chart_id}/share", response_model=ShareResponse)
async def share_chart(chart_id: int, share_data: ShareRequest, current_user: str = Depends(get_current_user)):
    """
    Share a chart with a user (view-only). Only the owner can share.
    Requires JWT authentication.
    """
    if ChartModel.share_chart(chart_id, share_data.shared_with, current_user):
        return {
            "resource_type": "chart",
            "resource_id": chart_id,
            "shared_with": share_data.shared_with,
            "shared_by": current_user,
            "message": "Chart shared successfully"
        }

@router.get("/{chart_id}/shared", response_model=SharedUsersResponse)
async def get_shared_chart_users(chart_id: int, current_user: str = Depends(get_current_user)):
    """
    Retrieve list of users a chart is shared with. Only the owner can view.
    Requires JWT authentication.
    """
    shared_users = ChartModel.get_shared_users("chart", chart_id, current_user)
    return {
        "resource_type": "chart",
        "resource_id": chart_id,
        "shared_users": shared_users
    }