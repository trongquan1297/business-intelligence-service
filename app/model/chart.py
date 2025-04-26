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
    def create_chart(chart_data: Dict, owner: str) -> int:
        """
        Insert a new chart into the charts table.
        Validates dataset_id before insertion.
        Sets owner, who_is_access, created_at, and updated_at.
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
            INSERT INTO charts (name, dataset_id, query, config, owner, who_is_access, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            who_is_access = chart_data.get("who_is_access") or []
            who_is_access_json = json.dumps(who_is_access)
            logger.info(f"Storing who_is_access for chart: {who_is_access_json}")
            values = (
                chart_data["name"],
                chart_data["query"]["dataset_id"],
                json.dumps(chart_data["query"]),
                json.dumps(chart_data["config"]),
                owner,
                who_is_access_json
            )
            cursor.execute(query, values)
            conn.commit()

            chart_id = cursor.lastrowid
            logger.info(f"Created chart {chart_id}: {chart_data['name']} by {owner}")
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
        Updates updated_at automatically.
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

            updates = ["updated_at = NOW()"]
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
            if "who_is_access" in chart_data:
                who_is_access = chart_data["who_is_access"] or []
                updates.append("who_is_access = %s")
                values.append(json.dumps(who_is_access))
                logger.info(f"Updating who_is_access for chart {chart_id}: {who_is_access}")

            if len(updates) == 1:  # Only updated_at
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
    def get_all_charts(current_user: str) -> List[Dict]:
        """
        Retrieve all charts with dataset schema_name and metadata.
        Only returns charts where current_user is owner or in who_is_access.
        Returns a list of dictionaries with chart details.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT c.id, c.name, c.dataset_id, d.schema_name, c.query, c.config,
                   c.owner, c.who_is_access, c.created_at, c.updated_at
            FROM charts c
            JOIN datasets d ON c.dataset_id = d.id
            WHERE c.owner = %s OR JSON_CONTAINS(c.who_is_access, %s)
            """
            cursor.execute(query, (current_user, json.dumps(current_user)))
            charts = cursor.fetchall()
            for chart in charts:
                chart["query"] = json.loads(chart["query"])
                chart["config"] = json.loads(chart["config"])
                chart["who_is_access"] = json.loads(chart["who_is_access"]) if chart["who_is_access"] else []
                logger.info(f"Chart {chart['id']} who_is_access: {chart['who_is_access']}")
                # Ensure backward compatibility for value_field
                if "value_field" in chart["query"]:
                    chart["query"]["value_fields"] = [chart["query"]["value_field"]]
                    del chart["query"]["value_field"]
            return charts
        except MySQLError as e:
            logger.error(f"Failed to fetch charts: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch charts: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def get_chart(chart_id: int, current_user: str) -> Optional[Dict]:
        """
        Retrieve a chart by ID with dataset schema_name and metadata.
        Only returns chart if current_user is owner or in who_is_access.
        Returns the chart details or None if not found or unauthorized.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT c.id, c.name, c.dataset_id, d.schema_name, c.query, c.config,
                   c.owner, c.who_is_access, c.created_at, c.updated_at
            FROM charts c
            JOIN datasets d ON c.dataset_id = d.id
            WHERE c.id = %s
            """
            cursor.execute(query, (chart_id,))
            chart = cursor.fetchone()
            if chart:
                chart["query"] = json.loads(chart["query"])
                chart["config"] = json.loads(chart["config"])
                chart["who_is_access"] = json.loads(chart["who_is_access"]) if chart["who_is_access"] else []
                logger.info(f"Chart {chart_id} who_is_access: {chart['who_is_access']}")
                # Ensure backward compatibility for value_field
                if "value_field" in chart["query"]:
                    chart["query"]["value_fields"] = [chart["query"]["value_field"]]
                    del chart["query"]["value_field"]
                # Check access
                if current_user != chart["owner"] and current_user not in chart["who_is_access"]:
                    raise HTTPException(status_code=403, detail="Access denied to this chart")
            return chart
        except MySQLError as e:
            logger.error(f"Failed to fetch chart {chart_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch chart: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def get_chart_data(chart_id: int, redshift_config: Dict, current_user: str) -> Dict:
        """
        Fetch data for a chart from Redshift using stored query.
        Only returns data if current_user is owner or in who_is_access.
        Returns Chart.js-compatible data (labels, values or datasets).
        """
        chart = ChartModel.get_chart(chart_id, current_user)
        if not chart:
            raise HTTPException(status_code=404, detail="Chart not found or unauthorized")

        # Use ChartQueryModel to execute the query with config limit and sort_order
        query_data = chart["query"].copy()
        query_data["limit"] = chart["config"].get("limit", 10)
        query_data["sort_order"] = chart["config"].get("sortOrder", "desc")
        # Ensure value_fields is used
        if "value_field" in query_data:
            query_data["value_fields"] = [query_data["value_field"]]
            del query_data["value_field"]
        chart_data = ChartQueryModel.build_and_execute_query(query_data, redshift_config)

        return chart_data