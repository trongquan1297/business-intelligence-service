from fastapi import APIRouter, Depends, Query
from app.model.database_metadata import RedshiftMetadataModel
from app.dependencies import get_current_user
from config import REDSHIFT_CONFIG
from app.schemas.database_metadata import TableListResponse, ColumnListResponse, SchemaListResponse

router = APIRouter()
# Redshift metadata routes
@router.get("/schemas", response_model=SchemaListResponse)
async def get_redshift_schemas(current_user: str = Depends(get_current_user)):
    """
    Retrieve a list of all schemas in the Redshift database.
    Requires JWT authentication.
    """
    schemas = RedshiftMetadataModel.get_all_schemas(REDSHIFT_CONFIG)
    return {"schemas": schemas}

@router.get("/tables", response_model=TableListResponse)
async def get_redshift_tables(
    schema_name: str = Query(..., description="Schema name of the table"),
    current_user: str = Depends(get_current_user)):
    """
    Retrieve a list of all tables in the Redshift database.
    Requires JWT authentication.
    """
    tables = RedshiftMetadataModel.get_all_tables(REDSHIFT_CONFIG, schema_name)
    return {"tables": tables}

@router.get("/columns", response_model=ColumnListResponse)
async def get_redshift_columns(
    table_name: str = Query(..., description="Name of the table to fetch columns for"),
    schema_name: str = Query(..., description="Schema name of the table"),
    current_user: str = Depends(get_current_user)
):
    """
    Retrieve a list of columns for a specific table in Redshift.
    Requires JWT authentication, table_name, and schema_name as query parameters.
    """
    columns = RedshiftMetadataModel.get_table_columns(REDSHIFT_CONFIG, table_name, schema_name)
    return {"table_name": table_name, "schema_name": schema_name, "columns": columns}