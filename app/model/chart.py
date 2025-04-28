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
        Sets owner, created_at, and updated_at.
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
            INSERT INTO charts (name, dataset_id, query, config, owner, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """
            values = (
                chart_data["name"],
                chart_data["query"]["dataset_id"],
                json.dumps(chart_data["query"]),
                json.dumps(chart_data["config"]),
                owner
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
    def update_chart(chart_id: int, chart_data: Dict, current_user: str) -> bool:
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
                
                # Check if chart exists and user is owner
                cursor.execute("SELECT owner FROM charts WHERE id = %s", (chart_id,))
                chart = cursor.fetchone()
                if not chart:
                    raise HTTPException(status_code=404, detail="Chart not found")
                if chart[0] != current_user:
                    raise HTTPException(status_code=403, detail="Only the owner can update the chart")

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
    def delete_chart(chart_id: int, current_user: str) -> bool:
        """
        Delete a chart by ID.
        Returns True if deleted, False if chart not found.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            # Check if chart exists and user is owner
            cursor.execute("SELECT owner FROM charts WHERE id = %s", (chart_id,))
            chart = cursor.fetchone()
            if not chart:
                raise HTTPException(status_code=404, detail="Chart not found")
            if chart[0] != current_user:
                raise HTTPException(status_code=403, detail="Only the owner can delete the chart")

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
        Retrieve all charts accessible to the current user (owner or shared).
        Returns a list of dictionaries with chart details and shared_users.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT c.id, c.name, c.dataset_id, c.query, c.config,
                   c.owner, c.created_at, c.updated_at
            FROM charts c
            WHERE c.owner = %s
            OR EXISTS (
                SELECT 1 FROM shared s
                WHERE s.resource_type = 'chart'
                AND s.resource_id = c.id
                AND s.shared_with = %s
            )
            """
            cursor.execute(query, (current_user, current_user))
            charts = cursor.fetchall()

            for chart in charts:
                chart["query"] = json.loads(chart["query"])
                chart["config"] = json.loads(chart["config"])
                if "value_field" in chart["query"]:
                    chart["query"]["value_fields"] = [chart["query"]["value_field"]]
                    del chart["query"]["value_field"]
                # Fetch shared users
                cursor.execute("""
                    SELECT shared_with
                    FROM shared
                    WHERE resource_type = 'chart' AND resource_id = %s
                """, (chart["id"],))
                shared_users = [row["shared_with"] for row in cursor.fetchall()]
                chart["shared_users"] = shared_users

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
        Retrieve a chart by ID if the user is the owner or shared_with.
        Returns the chart details with shared_users or None if not found or unauthorized.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT id, name, dataset_id, query, config,
                   owner, created_at, updated_at
            FROM charts
            WHERE id = %s
            AND (
                owner = %s
                OR EXISTS (
                    SELECT 1 FROM shared
                    WHERE resource_type = 'chart'
                    AND resource_id = %s
                    AND shared_with = %s
                )
            )
            """
            cursor.execute(query, (chart_id, current_user, chart_id, current_user))
            chart = cursor.fetchone()
            if chart:
                chart["query"] = json.loads(chart["query"])
                chart["config"] = json.loads(chart["config"])
                if "value_field" in chart["query"]:
                    chart["query"]["value_fields"] = [chart["query"]["value_field"]]
                    del chart["query"]["value_field"]
                # Fetch shared users
                cursor.execute("""
                    SELECT shared_with
                    FROM shared
                    WHERE resource_type = 'chart' AND resource_id = %s
                """, (chart_id,))
                shared_users = [row["shared_with"] for row in cursor.fetchall()]
                chart["shared_users"] = shared_users
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
        Only returns data if current_user is owner.
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
    
    @staticmethod
    def share_chart(chart_id: int, shared_with: str, shared_by: str) -> bool:
        """
        Share a chart with a user. Only the owner can share.
        Returns True if shared, raises exceptions for invalid cases.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            # Check if chart exists and user is owner
            cursor.execute("SELECT owner FROM charts WHERE id = %s", (chart_id,))
            chart = cursor.fetchone()
            if not chart:
                raise HTTPException(status_code=404, detail="Chart not found")
            if chart[0] != shared_by:
                raise HTTPException(status_code=403, detail="Only the owner can share the chart")

            # Check if shared_with user exists
            cursor.execute("SELECT username FROM users WHERE username = %s", (shared_with,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Shared_with user does not exist")

            # Check if already shared
            cursor.execute("""
                SELECT 1 FROM shared
                WHERE resource_type = 'chart' AND resource_id = %s AND shared_with = %s
            """, (chart_id, shared_with))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Chart already shared with this user")

            # Prevent sharing with self
            if shared_with == shared_by:
                raise HTTPException(status_code=400, detail="Cannot share with self")

            # Insert sharing record
            query = """
            INSERT INTO shared (resource_type, resource_id, shared_with, shared_by)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, ('chart', chart_id, shared_with, shared_by))
            conn.commit()

            logger.info(f"Shared chart {chart_id} with {shared_with} by {shared_by}")
            return True
        except MySQLError as e:
            logger.error(f"Failed to share chart {chart_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to share chart: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()
    
    @staticmethod
    def get_shared_users(resource_type: str, resource_id: int, current_user: str) -> List[str]:
        """
        Retrieve list of users a resource is shared with. Only the owner can view.
        Returns list of shared_with usernames.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            # Check if user is owner
            table = 'dashboards' if resource_type == 'dashboard' else 'charts'
            cursor.execute(f"SELECT owner FROM {table} WHERE id = %s", (resource_id,))
            resource = cursor.fetchone()
            if not resource:
                raise HTTPException(status_code=404, detail=f"{resource_type.capitalize()} not found")
            if resource[0] != current_user:
                raise HTTPException(status_code=403, detail="Only the owner can view shared users")

            # Fetch shared users
            cursor.execute("""
                SELECT shared_with
                FROM shared
                WHERE resource_type = %s AND resource_id = %s
            """, (resource_type, resource_id))
            shared_users = [row[0] for row in cursor.fetchall()]
            return shared_users
        except MySQLError as e:
            logger.error(f"Failed to fetch shared users for {resource_type} {resource_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch shared users: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()