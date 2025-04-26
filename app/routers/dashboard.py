from fastapi import APIRouter, Depends, HTTPException
from app.schemas.dashboard import DashboardCreate, DashboardUpdate, DashboardResponse, DashboardListResponse
from app.schemas.chart import ChartCreate, ChartUpdate, ChartResponse, ChartDataResponse, ChartListResponse
from app.model.dashboard import DashboardModel
from app.model.chart import ChartModel
from app.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=DashboardResponse)
async def create_dashboard(dashboard_data: DashboardCreate, current_user: str = Depends(get_current_user)):
    """
    Create a new dashboard with the provided data.
    Requires JWT authentication.
    """
    dashboard_id = DashboardModel.create_dashboard(dashboard_data.dict(), current_user)
    dashboard = DashboardModel.get_dashboard(dashboard_id, current_user)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {
        "id": dashboard["id"],
        "name": dashboard["name"],
        "owner": dashboard["owner"],
        "layout": dashboard["layout"],
        "description": dashboard["description"],
        "message": "Dashboard created successfully"
    }

@router.get("/get", response_model=DashboardListResponse)
async def get_dashboards(current_user: str = Depends(get_current_user)):
    """
    Retrieve a list of all dashboards.
    Requires JWT authentication.
    """
    dashboards = DashboardModel.get_all_dashboards(current_user)
    return {"dashboards": dashboards}

@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(dashboard_id: int, current_user: str = Depends(get_current_user)):
    """
    Retrieve a dashboard by ID.
    Requires JWT authentication.
    """
    dashboard = DashboardModel.get_dashboard(dashboard_id, current_user)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or unauthorized")
    return {
        "id": dashboard["id"],
        "name": dashboard["name"],
        "owner": dashboard["owner"],
        "layout": dashboard["layout"],
        "description": dashboard["description"],
        "message": "Dashboard retrieved successfully"
    }

@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(dashboard_id: int, dashboard_data: DashboardUpdate, current_user: str = Depends(get_current_user)):
    """
    Update an existing dashboard by ID.
    Requires JWT authentication.
    """
    dashboard = DashboardModel.get_dashboard(dashboard_id, current_user)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or unauthorized")
    if not DashboardModel.update_dashboard(dashboard_id, dashboard_data.dict(exclude_unset=True)):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    updated_dashboard = DashboardModel.get_dashboard(dashboard_id, current_user)
    return {
        "id": updated_dashboard["id"],
        "name": updated_dashboard["name"],
        "owner": updated_dashboard["owner"],
        "layout": updated_dashboard["layout"],
        "description": updated_dashboard["description"],
        "message": "Dashboard updated successfully"
    }

@router.delete("/{dashboard_id}", response_model=DashboardResponse)
async def delete_dashboard(dashboard_id: int, current_user: str = Depends(get_current_user)):
    """
    Delete a dashboard by ID.
    Requires JWT authentication.
    """
    dashboard = DashboardModel.get_dashboard(dashboard_id, current_user)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found or unauthorized")
    if not DashboardModel.delete_dashboard(dashboard_id):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {
        "id": dashboard["id"],
        "name": dashboard["name"],
        "owner": dashboard["owner"],
        "layout": dashboard["layout"],
        "description": dashboard["description"],
        "message": "Dashboard deleted successfully"
    }