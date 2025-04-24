from fastapi import HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional

class RedshiftMetadataModel:
    @staticmethod
    def get_redshift_connection(redshift_config: Dict):
        """
        Create and return a Redshift database connection.
        """
        try:
            conn = psycopg2.connect(**redshift_config)
            return conn
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to Redshift: {str(e)}")

    @staticmethod
    def get_all_schemas(redshift_config: Dict) -> List[Dict]:
        """
        Retrieve a list of all schemas in the Redshift database.
        Returns a list of dictionaries with schema_name.
        """
        conn = None
        try:
            conn = RedshiftMetadataModel.get_redshift_connection(redshift_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
            """
            cursor.execute(query)
            schemas = cursor.fetchall()
            return schemas
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch schemas: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def get_all_tables(redshift_config: Dict, schema_name: Optional[str] = None) -> List[Dict]:
        """
        Retrieve a list of tables in the Redshift database, optionally filtered by schema.
        Returns a list of dictionaries with schema_name and table_name.
        """
        conn = None
        try:
            conn = RedshiftMetadataModel.get_redshift_connection(redshift_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
            SELECT table_schema AS schema_name, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            AND table_schema NOT IN ('pg_catalog', 'information_schema')
            """
            params = []
            if schema_name:
                query += " AND table_schema = %s"
                params.append(schema_name)
            query += " ORDER BY table_schema, table_name"
            cursor.execute(query, params)
            tables = cursor.fetchall()
            return tables
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch tables: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def get_table_columns(redshift_config: Dict, table_name: str, schema_name: str) -> List[Dict]:
        """
        Retrieve a list of columns for a specific table in Redshift.
        Returns a list of dictionaries with column_name and data_type.
        """
        conn = None
        try:
            conn = RedshiftMetadataModel.get_redshift_connection(redshift_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
            AND table_schema = %s
            ORDER BY ordinal_position
            """
            cursor.execute(query, (table_name, schema_name))
            columns = cursor.fetchall()
            if not columns:
                raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found or has no columns")
            return columns
        except psycopg2.Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch columns: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()