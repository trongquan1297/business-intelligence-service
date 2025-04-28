from mysql.connector import Error as MySQLError
from fastapi import HTTPException
from app.utils.database import get_mysql_connection
from typing import List, Dict, Optional
from app.model.comment import CommentModel
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
    def update_dashboard(dashboard_id: int, dashboard_data: Dict, current_user: str) -> bool:
        """
        Update an existing dashboard by ID.
        Updates updated_at automatically.
        Returns True if updated, False if dashboard not found.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            # Check if dashboard exists and user is owner
            cursor.execute("SELECT owner FROM dashboards WHERE id = %s", (dashboard_id,))
            dashboard = cursor.fetchone()
            if not dashboard:
                raise HTTPException(status_code=404, detail="Dashboard not found")
            if dashboard[0] != current_user:
                raise HTTPException(status_code=403, detail="Only the owner can update the dashboard")

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
            print(values)
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
    def delete_dashboard(dashboard_id: int, current_user: str) -> bool:
        """
        Delete a dashboard by ID.
        Returns True if deleted, False if dashboard not found.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            # Check if dashboard exists and user is owner
            cursor.execute("SELECT owner FROM dashboards WHERE id = %s", (dashboard_id,))
            dashboard = cursor.fetchone()
            if not dashboard:
                raise HTTPException(status_code=404, detail="Dashboard not found")
            if dashboard[0] != current_user:
                raise HTTPException(status_code=403, detail="Only the owner can delete the dashboard")
        
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
        Retrieve all dashboards accessible to the current user (owner or shared).
        Returns a list of dictionaries with dashboard details and shared_users.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT d.id, d.name, d.layout, d.owner, d.description, d.created_at, d.updated_at
            FROM dashboards d
            WHERE d.owner = %s
            OR EXISTS (
                SELECT 1 FROM shared s
                WHERE s.resource_type = 'dashboard'
                AND s.resource_id = d.id
                AND s.shared_with = %s
            )
            """
            cursor.execute(query, (current_user, current_user))
            dashboards = cursor.fetchall()

            for dashboard in dashboards:
                dashboard["layout"] = json.loads(dashboard["layout"])
                # Fetch shared users
                cursor.execute("""
                    SELECT shared_with
                    FROM shared
                    WHERE resource_type = 'dashboard' AND resource_id = %s
                """, (dashboard["id"],))
                shared_users = [row["shared_with"] for row in cursor.fetchall()]
                dashboard["shared_users"] = shared_users

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
            Retrieve a dashboard by ID if the user is the owner or shared_with.
            Returns the dashboard details with shared_users or None if not found or unauthorized.
            """
            conn = None
            try:
                conn = get_mysql_connection()
                cursor = conn.cursor(dictionary=True)

                query = """
                SELECT id, name, layout, owner, description, created_at, updated_at
                FROM dashboards
                WHERE id = %s
                AND (
                    owner = %s
                    OR EXISTS (
                        SELECT 1 FROM shared
                        WHERE resource_type = 'dashboard'
                        AND resource_id = %s
                        AND shared_with = %s
                    )
                )
                """
                cursor.execute(query, (dashboard_id, current_user, dashboard_id, current_user))
                dashboard = cursor.fetchone()
                if dashboard:
                    dashboard["layout"] = json.loads(dashboard["layout"])
                    # Fetch shared users
                    cursor.execute("""
                        SELECT shared_with
                        FROM shared
                        WHERE resource_type = 'dashboard' AND resource_id = %s
                    """, (dashboard_id,))
                    shared_users = [row["shared_with"] for row in cursor.fetchall()]
                    dashboard["shared_users"] = shared_users

                    dashboard["comments"] = CommentModel.get_comments("dashboard", dashboard_id)
                return dashboard
            except MySQLError as e:
                logger.error(f"Failed to fetch dashboard {dashboard_id}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard: {str(e)}")
            finally:
                if conn:
                    cursor.close()
                    conn.close()
    
    @staticmethod
    def share_dashboard(dashboard_id: int, shared_with: str, shared_by: str) -> bool:
        """
        Share a dashboard with a user. Only the owner can share.
        Returns True if shared, raises exceptions for invalid cases.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            # Check if dashboard exists and user is owner
            cursor.execute("SELECT owner FROM dashboards WHERE id = %s", (dashboard_id,))
            dashboard = cursor.fetchone()
            if not dashboard:
                raise HTTPException(status_code=404, detail="Dashboard not found")
            if dashboard[0] != shared_by:
                raise HTTPException(status_code=403, detail="Only the owner can share the dashboard")

            # Check if shared_with user exists
            cursor.execute("SELECT username FROM users WHERE username = %s", (shared_with,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Shared_with user does not exist")

            # Check if already shared
            cursor.execute("""
                SELECT 1 FROM shared
                WHERE resource_type = 'dashboard' AND resource_id = %s AND shared_with = %s
            """, (dashboard_id, shared_with))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Dashboard already shared with this user")

            # Prevent sharing with self
            if shared_with == shared_by:
                raise HTTPException(status_code=400, detail="Cannot share with self")

            # Insert sharing record
            query = """
            INSERT INTO shared (resource_type, resource_id, shared_with, shared_by)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, ('dashboard', dashboard_id, shared_with, shared_by))
            conn.commit()

            logger.info(f"Shared dashboard {dashboard_id} with {shared_with} by {shared_by}")
            return True
        except MySQLError as e:
            logger.error(f"Failed to share dashboard {dashboard_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to share dashboard: {str(e)}")
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
    