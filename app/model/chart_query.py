from fastapi import HTTPException
from app.utils.database import get_mysql_connection
from mysql.connector import Error as MySQLError
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List
import re
import logging

logger = logging.getLogger(__name__)

class ChartQueryModel:
    @staticmethod
    def get_dataset_details(dataset_id: int) -> Dict:
        """
        Fetch dataset details from MySQL.
        Returns a dictionary with database, table_name, and schema_name.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT `database`, table_name, schema_name
            FROM datasets
            WHERE id = %s
            """
            cursor.execute(query, (dataset_id,))
            dataset = cursor.fetchone()
            if not dataset:
                raise HTTPException(status_code=404, detail=f"Dataset ID {dataset_id} not found")
            return dataset
        except MySQLError as e:
            logger.error(f"Failed to fetch dataset {dataset_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch dataset: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def build_and_execute_query(query_data: Dict, redshift_config: Dict) -> Dict:
        """
        Build and execute a SQL query on Redshift for a chart.
        Returns Chart.js-compatible data with labels and values.
        """
        # Fetch dataset details
        dataset = ChartQueryModel.get_dataset_details(query_data["dataset_id"])

        # Extract request data
        label_fields = query_data["label_fields"]
        value_field = query_data["value_field"]
        filters = query_data.get("filters", {})
        limit = query_data.get("limit")
        sort_order = query_data.get("sort_order")

        # Build SELECT clause
        select_clause = ", ".join(label_fields) + f", {value_field} AS value"

        # Build FROM clause
        from_clause = f"FROM {dataset['schema_name']}.{dataset['table_name']}"

        # Build WHERE clause
        where_conditions = []
        params = []
        for column_name, filter_data in query_data.get("filters", {}).items():
                if not re.match(r'^[a-zA-Z0-9_]+$', column_name):
                    raise HTTPException(status_code=400, detail=f"Invalid column name in filter: {column_name}")
                operator = filter_data.get("operator")
                value = filter_data.get("value")
                if not operator or value is None:
                    raise HTTPException(status_code=400, detail=f"Invalid filter for column: {column_name}")
                if operator not in ["=", "!=", ">", "<", ">=", "<=", "LIKE"]:
                    raise HTTPException(status_code=400, detail=f"Invalid operator in filter: {operator}")
                where_conditions.append(f"{column_name} {operator} %s")
                params.append(value)
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Build GROUP BY clause
        group_by_clause = f"GROUP BY {', '.join(label_fields)}"

        # Build LIMIT
        limit_clause = ""
        if limit is not None:
                if not isinstance(limit, int) or limit <= 0:
                    raise HTTPException(status_code=400, detail="Limit must be a positive integer")
                limit_clause = f"LIMIT {limit}"

        # Construct ORDER BY clause
        order_by_clause = ""
        if sort_order:
            sort_order = sort_order.upper()
            if sort_order not in ["ASC", "DESC"]:
                raise HTTPException(status_code=400, detail="Sort order must be 'asc' or 'desc'")
            order_by_clause = f"ORDER BY value {sort_order}"

        # Construct final query
        sql_query = f"SELECT {select_clause} {from_clause} {where_clause} {group_by_clause} {order_by_clause} {limit_clause}".strip()
        logger.info(f"Generated SQL query for dataset_id {query_data['dataset_id']}: {sql_query}")

        # Execute query on Redshift
        conn = None
        try:
            conn = psycopg2.connect(**redshift_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(sql_query, params)
            results = cursor.fetchall()

            # Format results for Chart.js
            labels = ["_".join(str(row[field]) for field in label_fields) for row in results]
            values = [float(row["value"]) for row in results]

            return {"labels": labels, "values": values}
        except psycopg2.Error as e:
            logger.error(f"Failed to execute Redshift query: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to query Redshift: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()