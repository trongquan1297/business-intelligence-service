from fastapi import HTTPException
from app.utils.database import get_mysql_connection
from mysql.connector import Error as MySQLError
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class DashboardModel:
    @staticmethod
    def create_dashboard(dashboard_data: Dict) -> int:
        """
        Create a new dashboard in the dashboards table.
        Validates chart_ids in layout.
        Returns the ID of the created dashboard.
        """
        # Validate chart_ids
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            for item in dashboard_data["layout"]:
                if item["type"] == "chart":
                    chart_id = item["content"].get("chart_id")
                    cursor.execute("SELECT id FROM charts WHERE id = %s", (chart_id,))
                    if not cursor.fetchone():
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid chart_id: {chart_id} does not exist in charts table"
                        )
        except MySQLError as e:
            logger.error(f"Failed to validate chart_ids: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to validate chart_ids: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

        # Insert dashboard
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            query = """
            INSERT INTO dashboards (title, description, layout)
            VALUES (%s, %s, %s)
            """
            values = (
                dashboard_data["title"],
                dashboard_data.get("description"),
                json.dumps(dashboard_data["layout"])
            )
            cursor.execute(query, values)
            conn.commit()
            dashboard_id = cursor.lastrowid
            logger.info(f"Created dashboard {dashboard_id}: {dashboard_data['title']}")
            return dashboard_id
        except MySQLError as e:
            logger.error(f"Failed to create dashboard: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create dashboard: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def update_dashboard(dashboard_id: int, dashboard_data: Dict) -> bool:
        """
        Update an existing dashboard by ID.
        Validates chart_ids in layout if provided.
        Returns True if updated, False if dashboard not found.
        """
        if dashboard_data.get("layout"):
            conn = None
            try:
                conn = get_mysql_connection()
                cursor = conn.cursor()
                for item in dashboard_data["layout"]:
                    if item["type"] == "chart":
                        chart_id = item["content"].get("chart_id")
                        cursor.execute("SELECT id FROM charts WHERE id = %s", (chart_id,))
                        if not cursor.fetchone():
                            raise HTTPException(
                                status_code=400,
                                detail=f"Invalid chart_id: {chart_id} does not exist in charts table"
                            )
            except MySQLError as e:
                logger.error(f"Failed to validate chart_ids: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to validate chart_ids: {str(e)}")
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
            if dashboard_data.get("title"):
                updates.append("title = %s")
                values.append(dashboard_data["title"])
            if "description" in dashboard_data:
                updates.append("description = %s")
                values.append(dashboard_data["description"])
            if dashboard_data.get("layout"):
                updates.append("layout = %s")
                values.append(json.dumps(dashboard_data["layout"]))
            if not updates:
                return True
            values.append(dashboard_id)
            query = f"""
            UPDATE dashboards
            SET {', '.join(updates)}
            WHERE id = %s
            """
            cursor.execute(query, values)
            conn.commit()
            if cursor.rowcount == 0:
                return False
            logger.info(f"Updated dashboard {dashboard_id}")
            return True
        except MySQLError as e:
            logger.error(f"Failed to update dashboard {dashboard_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update dashboard: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def delete_dashboard(dashboard_id: int) -> bool:
        """
        Delete a dashboard by ID.
        Returns True if deleted, False if dashboard not found.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            query = """
            DELETE FROM dashboards
            WHERE id = %s
            """
            cursor.execute(query, (dashboard_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return False
            logger.info(f"Deleted dashboard {dashboard_id}")
            return True
        except MySQLError as e:
            logger.error(f"Failed to delete dashboard {dashboard_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete dashboard: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def get_dashboard(dashboard_id: int) -> Optional[Dict]:
        """
        Retrieve a dashboard by ID.
        Returns the dashboard details or None if not found.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT id, title, description, layout, created_at, updated_at
            FROM dashboards
            WHERE id = %s
            """
            cursor.execute(query, (dashboard_id,))
            dashboard = cursor.fetchone()
            if dashboard:
                dashboard["layout"] = json.loads(dashboard["layout"])
            return dashboard
        except MySQLError as e:
            logger.error(f"Failed to fetch dashboard {dashboard_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def get_all_dashboards() -> List[Dict]:
        """
        Retrieve all dashboards.
        Returns a list of dashboard details.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT id, title, description, layout, created_at, updated_at
            FROM dashboards
            """
            cursor.execute(query)
            dashboards = cursor.fetchall()
            for dashboard in dashboards:
                dashboard["layout"] = json.loads(dashboard["layout"])
            return dashboards
        except MySQLError as e:
            logger.error(f"Failed to fetch dashboards: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch dashboards: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()