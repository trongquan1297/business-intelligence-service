from mysql.connector import Error as MySQLError
from fastapi import HTTPException
from app.utils.database import get_mysql_connection
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from app.model.chart_query import ChartQueryModel

logger = logging.getLogger(__name__)

class ChartModel:
    @staticmethod
    def create_chart(chart_data: Dict) -> int:
        """
        Insert a new chart into the charts table.
        Validates dataset_id before insertion.
        Returns the ID of the created chart.
        """
        # Validate dataset_id
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            query = "SELECT id FROM datasets WHERE id = %s"
            cursor.execute(query, (chart_data["query"]["dataset_id"],))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid dataset_id: {chart_data['query']['dataset_id']} does not exist in datasets table"
                )
        except MySQLError as e:
            logger.error(f"Failed to validate dataset_id: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to validate dataset_id: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

        # Insert chart
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            query = """
            INSERT INTO charts (name, dataset_id, query, config)
            VALUES (%s, %s, %s, %s)
            """
            values = (
                chart_data["name"],
                chart_data["query"]["dataset_id"],
                json.dumps(chart_data["query"]),
                json.dumps(chart_data["config"])
            )
            cursor.execute(query, values)
            conn.commit()

            chart_id = cursor.lastrowid
            logger.info(f"Created chart {chart_id}: {chart_data['name']}")
            return chart_id
        except MySQLError as e:
            logger.error(f"Failed to create chart: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create chart: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def update_chart(chart_id: int, chart_data: Dict) -> bool:
        """
        Update an existing chart by ID.
        Validates dataset_id if provided.
        Returns True if updated, False if chart not found.
        """
        if chart_data.get("query") and chart_data["query"].get("dataset_id"):
            conn = None
            try:
                conn = get_mysql_connection()
                cursor = conn.cursor()
                query = "SELECT id FROM datasets WHERE id = %s"
                cursor.execute(query, (chart_data["query"]["dataset_id"],))
                if not cursor.fetchone():
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid dataset_id: {chart_data['query']['dataset_id']} does not exist in datasets table"
                    )
            except MySQLError as e:
                logger.error(f"Failed to validate dataset_id: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to validate dataset_id: {str(e)}")
            finally:
                if conn:
                    cursor.close()
                    conn.close()

        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            updates = []
            values = []
            if chart_data.get("name"):
                updates.append("name = %s")
                values.append(chart_data["name"])
            if chart_data.get("query"):
                updates.append("dataset_id = %s")
                values.append(chart_data["query"]["dataset_id"])
                updates.append("query = %s")
                values.append(json.dumps(chart_data["query"]))
            if chart_data.get("config"):
                updates.append("config = %s")
                values.append(json.dumps(chart_data["config"]))

            if not updates:
                return True

            values.append(chart_id)
            query = f"""
            UPDATE charts
            SET {', '.join(updates)}
            WHERE id = %s
            """
            cursor.execute(query, values)
            conn.commit()

            if cursor.rowcount == 0:
                return False
            logger.info(f"Updated chart {chart_id}")
            return True
        except MySQLError as e:
            logger.error(f"Failed to update chart {chart_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update chart: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def delete_chart(chart_id: int) -> bool:
        """
        Delete a chart by ID.
        Returns True if deleted, False if chart not found.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            query = """
            DELETE FROM charts
            WHERE id = %s
            """
            cursor.execute(query, (chart_id,))
            conn.commit()

            if cursor.rowcount == 0:
                return False
            logger.info(f"Deleted chart {chart_id}")
            return True
        except MySQLError as e:
            logger.error(f"Failed to delete chart {chart_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete chart: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def get_all_charts() -> List[Dict]:
        """
        Retrieve all charts with dataset schema_name.
        Returns a list of dictionaries with chart details.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT c.id, c.name, c.dataset_id, d.schema_name, c.query, c.config
            FROM charts c
            JOIN datasets d ON c.dataset_id = d.id
            """
            cursor.execute(query)
            charts = cursor.fetchall()
            for chart in charts:
                chart["query"] = json.loads(chart["query"])
                chart["config"] = json.loads(chart["config"])
            return charts
        except MySQLError as e:
            logger.error(f"Failed to fetch charts: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch charts: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def get_chart(chart_id: int) -> Optional[Dict]:
        """
        Retrieve a chart by ID with dataset schema_name.
        Returns the chart details or None if not found.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT c.id, c.name, c.dataset_id, d.schema_name, c.query, c.config
            FROM charts c
            JOIN datasets d ON c.dataset_id = d.id
            WHERE c.id = %s
            """
            cursor.execute(query, (chart_id,))
            chart = cursor.fetchone()
            if chart:
                chart["query"] = json.loads(chart["query"])
                chart["config"] = json.loads(chart["config"])
            return chart
        except MySQLError as e:
            logger.error(f"Failed to fetch chart {chart_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch chart: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def get_chart_data(chart_id: int, redshift_config: Dict) -> Dict:
        """
        Fetch data for a chart from Redshift using stored query.
        Returns Chart.js-compatible data (labels, values).
        """
        chart = ChartModel.get_chart(chart_id)
        if not chart:
            raise HTTPException(status_code=404, detail="Chart not found")

        # Use ChartQueryModel to execute the query
        query_data = chart["query"]
        chart_data = ChartQueryModel.build_and_execute_query(query_data, redshift_config)

        # Apply limit and sortOrder from config
        limit = chart["config"].get("limit", 10)
        sort_order = chart["config"].get("sortOrder", "desc").upper()

        # Sort and limit data
        combined = list(zip(chart_data["labels"], chart_data["values"]))
        combined.sort(key=lambda x: x[1], reverse=(sort_order == "DESC"))
        combined = combined[:limit]
        chart_data["labels"], chart_data["values"] = zip(*combined) if combined else ([], [])

        return {
            "labels": list(chart_data["labels"]),
            "values": list(chart_data["values"])
        }