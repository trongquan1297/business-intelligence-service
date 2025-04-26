from mysql.connector import Error as MySQLError
from fastapi import HTTPException
from app.utils.database import get_mysql_connection
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

class DashboardModel:
    @staticmethod
    def create_dashboard(dashboard_data: Dict, owner: str) -> int:
        """
        Insert a new dashboard into the dashboards table.
        Sets owner, description, created_at, and updated_at.
        Returns the ID of the created dashboard.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            query = """
            INSERT INTO dashboards (name, layout, owner, description, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            """
            values = (
                dashboard_data["name"],
                json.dumps(dashboard_data["layout"]),
                owner,
                dashboard_data.get("description")
            )
            cursor.execute(query, values)
            conn.commit()

            dashboard_id = cursor.lastrowid
            logger.info(f"Created dashboard {dashboard_id}: {dashboard_data['name']} by {owner}")
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
        Updates updated_at automatically.
        Returns True if updated, False if dashboard not found.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            updates = ["updated_at = NOW()"]
            values = []
            if dashboard_data.get("name"):
                updates.append("name = %s")
                values.append(dashboard_data["name"])
            if dashboard_data.get("layout"):
                updates.append("layout = %s")
                values.append(json.dumps(dashboard_data["layout"]))
            if "description" in dashboard_data:
                updates.append("description = %s")
                values.append(dashboard_data["description"])

            if len(updates) == 1:  # Only updated_at
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
    def get_all_dashboards(current_user: str) -> List[Dict]:
        """
        Retrieve all dashboards with metadata.
        Only returns dashboards where current_user is owner.
        Returns a list of dictionaries with dashboard details.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT id, name, layout, owner, description, created_at, updated_at
            FROM dashboards
            WHERE owner = %s
            """
            cursor.execute(query, (current_user,))
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

    @staticmethod
    def get_dashboard(dashboard_id: int, current_user: str) -> Optional[Dict]:
        """
        Retrieve a dashboard by ID with metadata.
        Only returns dashboard if current_user is owner.
        Returns the dashboard details or None if not found or unauthorized.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT id, name, layout, owner, description, created_at, updated_at
            FROM dashboards
            WHERE id = %s
            """
            cursor.execute(query, (dashboard_id,))
            dashboard = cursor.fetchone()
            if dashboard:
                dashboard["layout"] = json.loads(dashboard["layout"])
                if current_user != dashboard["owner"]:
                    raise HTTPException(status_code=403, detail="Access denied to this dashboard")
            return dashboard
        except MySQLError as e:
            logger.error(f"Failed to fetch dashboard {dashboard_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()