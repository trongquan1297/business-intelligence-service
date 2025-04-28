from fastapi import APIRouter, Depends, HTTPException
from app.schemas.dashboard import DashboardCreate, DashboardUpdate, DashboardResponse,DashboardDataResponse, DashboardListResponse, ShareResponse, ShareRequest, SharedUsersResponse
from app.model.dashboard import DashboardModel
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
    Retrieve a list of all dashboards accessible to the user (owned or shared).
    Requires JWT authentication.
    """
    dashboards = DashboardModel.get_all_dashboards(current_user)
    return {"dashboards": dashboards}

@router.get("/{dashboard_id}", response_model=DashboardDataResponse)
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
        "comments": dashboard["comments"],
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
    if not DashboardModel.update_dashboard(dashboard_id, dashboard_data.dict(exclude_unset=True), current_user):
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
    if not DashboardModel.delete_dashboard(dashboard_id, current_user):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {
        "id": dashboard["id"],
        "name": dashboard["name"],
        "owner": dashboard["owner"],
        "layout": dashboard["layout"],
        "description": dashboard["description"],
        "message": "Dashboard deleted successfully"
    }

@router.post("/{dashboard_id}/share", response_model=ShareResponse)
async def share_dashboard(dashboard_id: int, share_data: ShareRequest, current_user: str = Depends(get_current_user)):
    """
    Share a dashboard with a user (view-only). Only the owner can share.
    Requires JWT authentication.
    """
    if DashboardModel.share_dashboard(dashboard_id, share_data.shared_with, current_user):
        return {
            "resource_type": "dashboard",
            "resource_id": dashboard_id,
            "shared_with": share_data.shared_with,
            "shared_by": current_user,
            "message": "Dashboard shared successfully"
        }

@router.get("/{dashboard_id}/shared", response_model=SharedUsersResponse)
async def get_shared_dashboard_users(dashboard_id: int, current_user: str = Depends(get_current_user)):
    """
    Retrieve list of users a dashboard is shared with. Only the owner can view.
    Requires JWT authentication.
    """
    shared_users = DashboardModel.get_shared_users("dashboard", dashboard_id, current_user)
    return {
        "resource_type": "dashboard",
        "resource_id": dashboard_id,
        "shared_users": shared_users
    }