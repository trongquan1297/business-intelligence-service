from fastapi import APIRouter, Depends, HTTPException
from app.model.dataset import DatasetModel
from app.dependencies import get_current_user
from app.schemas.dataset import DatasetCreate, DatasetResponse, DatasetListResponse, DatasetDeleteResponse

router = APIRouter()

@router.post("/", response_model=DatasetResponse)
async def create_dataset(dataset: DatasetCreate, current_user: str = Depends(get_current_user)):
    """
    Create a new dataset with schema_name.
    Requires JWT authentication and table_name, database, schema_name in the request body.
    """
    dataset_id = DatasetModel.create_dataset(
        database=dataset.database,
        table_name=dataset.table_name,
        schema_name=dataset.schema_name
    )
    return {
        "id": dataset_id,
        "table_name": dataset.table_name,
        "schema_name": dataset.schema_name,
        "message": "Dataset created successfully"
    }

@router.get("/get", response_model=DatasetListResponse)
async def get_datasets(current_user: str = Depends(get_current_user)):
    """
    Retrieve a list of all datasets with schema_name.
    Requires JWT authentication.
    """
    datasets = DatasetModel.get_all_datasets()
    return {"datasets": datasets}

@router.delete("/delete/{dataset_id}", response_model=DatasetDeleteResponse)
async def delete_dataset(dataset_id: int, current_user: str = Depends(get_current_user)):
    """
    Delete a dataset from the datasets table by ID.
    Requires JWT authentication.
    Returns the ID of the deleted dataset and a confirmation message.
    """
    success = DatasetModel.delete_dataset(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {
        "id": dataset_id,
        "message": "Dataset deleted successfully"
    }

