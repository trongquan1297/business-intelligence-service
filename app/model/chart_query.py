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
        Returns Chart.js-compatible data with labels and values or datasets.
        """
        # Fetch dataset details
        dataset = ChartQueryModel.get_dataset_details(query_data["dataset_id"])

        # Extract request data
        label_fields = query_data["label_fields"]
        value_fields = query_data["value_fields"]
        filters = query_data.get("filters", {})
        limit = query_data.get("limit")
        sort_order = query_data.get("sort_order")
        dimension_field = query_data.get("dimension_field")

        # Validate inputs
        if not label_fields:
            raise HTTPException(status_code=400, detail="At least one label field is required")
        for field in label_fields:
            if not re.match(r'^[a-zA-Z0-9_]+$', field):
                raise HTTPException(status_code=400, detail=f"Invalid label field: {field}")
        if not value_fields:
            raise HTTPException(status_code=400, detail="At least one value field is required")
        for value_field in value_fields:
            if not re.match(r'^(SUM|COUNT|AVG|MIN|MAX)\([a-zA-Z0-9_]+\)$', value_field, re.IGNORECASE):
                raise HTTPException(status_code=400, detail=f"Invalid value field format: {value_field}")
        if dimension_field and not re.match(r'^[a-zA-Z0-9_]+$', dimension_field):
            raise HTTPException(status_code=400, detail=f"Invalid dimension field: {dimension_field}")

        # Build SELECT clause
        select_fields = label_fields[:]
        if dimension_field:
            select_fields.append(dimension_field)
        # Create aliases for value fields (e.g., SUM(amount) AS value_0, COUNT(transaction_id) AS value_1)
        value_aliases = [f"{value_field} AS value_{i}" for i, value_field in enumerate(value_fields)]
        select_clause = ", ".join(select_fields + value_aliases)

        # Build FROM clause
        from_clause = f"FROM {dataset['schema_name']}.{dataset['table_name']}"

        # Build WHERE clause
        where_conditions = []
        params = []
        for column_name, filter_data in filters.items():
            if not re.match(r'^[a-zA-Z0-9_]+$', column_name):
                raise HTTPException(status_code=400, detail=f"Invalid column name in filter: {column_name}")
            operator = filter_data.get("operator").lower()
            value = filter_data.get("value")
            if not operator or value is None:
                raise HTTPException(status_code=400, detail=f"Invalid filter for column: {column_name}")
            valid_operators = ["=", "!=", ">", "<", ">=", "<=", "like", "between"]
            if operator not in valid_operators:
                raise HTTPException(status_code=400, detail=f"Invalid operator in filter: {operator}")
            
            if operator == "between":
                if not isinstance(value, list) or len(value) != 2:
                    raise HTTPException(status_code=400, detail=f"Value for 'between' must be a list of two timestamps")
                where_conditions.append(f"{column_name} BETWEEN %s AND %s")
                params.extend(value)
            else:
                where_conditions.append(f"{column_name} {operator} %s")
                params.append(value)
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Build GROUP BY clause
        group_by_fields = label_fields[:]
        if dimension_field:
            group_by_fields.append(dimension_field)
        group_by_clause = f"GROUP BY {', '.join(group_by_fields)}"

        # Build ORDER BY clause
        order_by_clause = ""
        if sort_order:
            sort_order = sort_order.upper()
            if sort_order not in ["ASC", "DESC"]:
                raise HTTPException(status_code=400, detail="Sort order must be 'asc' or 'desc'")
            # Order by the first value field for consistency
            order_by_clause = f"ORDER BY value_0 {sort_order}"

        # Build LIMIT clause
        limit_clause = ""
        if limit is not None:
            if not isinstance(limit, int) or limit <= 0:
                raise HTTPException(status_code=400, detail="Limit must be a positive integer")
            limit_clause = f"LIMIT {limit}"

        # Construct final query
        sql_query = f"""
        SELECT {select_clause}
        {from_clause}
        {where_clause}
        {group_by_clause}
        {order_by_clause}
        {limit_clause}
        """.strip()
        logger.info(f"Generated SQL query for dataset_id {query_data['dataset_id']}: {sql_query}")
        print(sql_query)

        # Execute query on Redshift
        conn = None
        try:
            conn = psycopg2.connect(**redshift_config, cursor_factory=RealDictCursor)
            cursor = conn.cursor()
            cursor.execute(sql_query, params)
            results = cursor.fetchall()

            # Format results for Chart.js
            if dimension_field or len(value_fields) > 1:
                # Use datasets format
                labels = []
                if dimension_field:
                    # Group by dimension_field
                    datasets = {}
                    for row in results:
                        label = "_".join(str(row[field]) for field in label_fields)
                        dimension_value = str(row[dimension_field])
                        values = [float(row[f"value_{i}"]) for i in range(len(value_fields))]

                        if label not in labels:
                            labels.append(label)

                        if dimension_value not in datasets:
                            datasets[dimension_value] = {
                                "label": dimension_value,
                                "data": [[0.0] * len(value_fields) for _ in labels]
                            }
                        # Adjust data length
                        while len(datasets[dimension_value]["data"]) < len(labels):
                            datasets[dimension_value]["data"].append([0.0] * len(value_fields))
                        datasets[dimension_value]["data"][labels.index(label)] = values

                    # Flatten datasets for each value_field
                    final_datasets = []
                    for value_idx, value_field in enumerate(value_fields):
                        for dim_value, dataset in datasets.items():
                            final_datasets.append({
                                "label": dim_value,  # Use only dimension value
                                "data": [row[value_idx] for row in dataset["data"]]
                            })
                    return {
                        "labels": labels,
                        "datasets": final_datasets
                    }
                else:
                    # Multiple value_fields without dimension_field
                    labels = ["_".join(str(row[field]) for field in label_fields) for row in results]
                    datasets = [
                        {
                            "label": value_field,
                            "data": [float(row[f"value_{i}"]) for row in results]
                        }
                        for i, value_field in enumerate(value_fields)
                    ]
                    return {
                        "labels": labels,
                        "datasets": datasets
                    }
            else:
                # Single value_field without dimension_field
                labels = ["_".join(str(row[field]) for field in label_fields) for row in results]
                values = [float(row["value_0"]) for row in results]
                return {
                    "labels": labels,
                    "values": values
                }
        except psycopg2.Error as e:
            logger.error(f"Failed to execute Redshift query: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to query Redshift: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()