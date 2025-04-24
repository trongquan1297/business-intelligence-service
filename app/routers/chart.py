from fastapi import APIRouter, Depends, HTTPException
from app.model.chart import ChartModel
from app.model.chart_query import ChartQueryModel
from app.dependencies import get_current_user
from config import REDSHIFT_CONFIG
from app.schemas.chart import ChartCreate, ChartUpdate, ChartResponse, ChartDataResponse, ChartListResponse
from app.schemas.chart_query import ChartQueryRequest, ChartQueryResponse

router = APIRouter()
# Chart routes
@router.post("/", response_model=ChartResponse)
async def create_chart(chart: ChartCreate, current_user: str = Depends(get_current_user)):
    """
    Create a new chart with name, query, and config.
    Requires JWT authentication and chart details in the request body.
    """
    chart_id = ChartModel.create_chart(chart.dict())
    chart_data = ChartModel.get_chart(chart_id)
    return {
        "id": chart_id,
        "name": chart.name,
        "schema_name": chart_data["schema_name"],
        "message": "Chart created successfully"
    }

@router.put("/{chart_id}", response_model=ChartResponse)
async def update_chart(chart_id: int, chart: ChartUpdate, current_user: str = Depends(get_current_user)):
    """
    Update an existing chart by ID.
    Requires JWT authentication and updated chart details in the request body.
    """
    success = ChartModel.update_chart(chart_id, chart.dict(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=404, detail="Chart not found")
    chart_data = ChartModel.get_chart(chart_id)
    return {
        "id": chart_id,
        "name": chart_data["name"],
        "schema_name": chart_data["schema_name"],
        "message": "Chart updated successfully"
    }

@router.delete("/delete/{chart_id}", response_model=ChartResponse)
async def delete_chart(chart_id: int, current_user: str = Depends(get_current_user)):
    """
    Delete a chart by ID.
    Requires JWT authentication.
    """
    chart_data = ChartModel.get_chart(chart_id)
    if not chart_data:
        raise HTTPException(status_code=404, detail="Chart not found")
    success = ChartModel.delete_chart(chart_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chart not found")
    return {
        "id": chart_id,
        "name": chart_data["name"],
        "schema_name": chart_data["schema_name"],
        "message": "Chart deleted successfully"
    }

@router.get("/get", response_model=ChartListResponse)
async def get_charts(current_user: str = Depends(get_current_user)):
    """
    Retrieve a list of all charts with schema_name.
    Requires JWT authentication.
    """
    charts = ChartModel.get_all_charts()
    return {"charts": charts}


@router.get("/{chart_id}", response_model=ChartDataResponse)
async def get_chart_data(chart_id: int, current_user: str = Depends(get_current_user)):
    """
    Retrieve a chart and its data for Chart.js rendering with schema_name.
    Requires JWT authentication.
    """
    chart = ChartModel.get_chart(chart_id)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    data = ChartModel.get_chart_data(chart_id, REDSHIFT_CONFIG)
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