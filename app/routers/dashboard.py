from fastapi import APIRouter, Depends, HTTPException
from app.model.dashboard import DashboardModel
from app.dependencies import get_current_user
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardListResponse,
    Dashboard
)

router = APIRouter()

@router.post("/", response_model=DashboardResponse)
async def create_dashboard(dashboard: DashboardCreate, current_user: str = Depends(get_current_user)):
    """
    Create a new dashboard with title, description, and layout.
    Requires JWT authentication and dashboard details in the request body.
    """
    dashboard_id = DashboardModel.create_dashboard(dashboard.dict())
    return {
        "id": dashboard_id,
        "title": dashboard.title,
        "message": "Dashboard created successfully"
    }

@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(dashboard_id: int, dashboard: DashboardUpdate, current_user: str = Depends(get_current_user)):
    """
    Update an existing dashboard by ID.
    Requires JWT authentication and updated dashboard details in the request body.
    """
    success = DashboardModel.update_dashboard(dashboard_id, dashboard.dict(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    dashboard_data = DashboardModel.get_dashboard(dashboard_id)
    return {
        "id": dashboard_id,
        "title": dashboard_data["title"],
        "message": "Dashboard updated successfully"
    }

@router.delete("/delete/{dashboard_id}", response_model=DashboardResponse)
async def delete_dashboard(dashboard_id: int, current_user: str = Depends(get_current_user)):
    """
    Delete a dashboard by ID.
    Requires JWT authentication.
    """
    dashboard_data = DashboardModel.get_dashboard(dashboard_id)
    if not dashboard_data:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    success = DashboardModel.delete_dashboard(dashboard_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {
        "id": dashboard_id,
        "title": dashboard_data["title"],
        "message": "Dashboard deleted successfully"
    }

@router.get("/get", response_model=DashboardListResponse)
async def get_dashboards(current_user: str = Depends(get_current_user)):
    """
    Retrieve a list of all dashboards.
    Requires JWT authentication.
    """
    dashboards = DashboardModel.get_all_dashboards()
    return {"dashboards": dashboards}

@router.get("/{dashboard_id}", response_model=Dashboard)
async def get_dashboard(dashboard_id: int, current_user: str = Depends(get_current_user)):
    """
    Retrieve a dashboard by ID.
    Requires JWT authentication.
    """
    dashboard = DashboardModel.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard
