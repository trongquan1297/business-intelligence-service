from mysql.connector import Error as MySQLError
from fastapi import HTTPException
from app.utils.database import get_mysql_connection
from app.schemas.comment import ResourceType
import logging

logger = logging.getLogger(__name__)

class CommentModel:
    @staticmethod
    def create_comment(comment_data: dict, current_user: str) -> int:
        """
        Create a new comment for a resource. Only users with view access can comment.
        Returns the ID of the created comment.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            resource_type = comment_data["resource_type"]
            resource_id = comment_data["resource_id"]

            # Validate resource_type
            if resource_type not in [ResourceType.dashboard]:
                raise HTTPException(status_code=400, detail="Invalid resource type. Only 'dashboard' is supported currently.")

            # Check if resource exists and user has view access
            if resource_type == ResourceType.dashboard:
                query = """
                SELECT id FROM dashboards
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
                cursor.execute(query, (resource_id, current_user, resource_id, current_user))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Dashboard not found or unauthorized")
            # Add elif for 'note' when implemented

            # Insert comment
            query = """
            INSERT INTO comments (resource_type, resource_id, username, content, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """
            values = (
                resource_type,
                resource_id,
                current_user,
                comment_data["content"]
            )
            cursor.execute(query, values)
            conn.commit()

            comment_id = cursor.lastrowid
            logger.info(f"Created comment {comment_id} for {resource_type} {resource_id} by {current_user}")
            return comment_id
        except MySQLError as e:
            logger.error(f"Failed to create comment: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create comment: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def delete_comment(comment_id: int, current_user: str) -> bool:
        """
        Delete a comment by ID. Only the comment author can delete.
        Returns True if deleted, False if comment not found.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            # Check if comment exists and user is author
            cursor.execute("SELECT username FROM comments WHERE id = %s", (comment_id,))
            comment = cursor.fetchone()
            if not comment:
                raise HTTPException(status_code=404, detail="Comment not found")
            if comment[0] != current_user:
                raise HTTPException(status_code=403, detail="Only the comment author can delete the comment")

            query = """
            DELETE FROM comments
            WHERE id = %s
            """
            cursor.execute(query, (comment_id,))
            conn.commit()

            if cursor.rowcount == 0:
                return False
            logger.info(f"Deleted comment {comment_id} by {current_user}")
            return True
        except MySQLError as e:
            logger.error(f"Failed to delete comment {comment_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete comment: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def get_comments(resource_type: str, resource_id: int) -> list:
        """
        Retrieve all comments for a resource, ordered by created_at DESC.
        Returns a list of comment dictionaries.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT id, resource_type, resource_id, username, content, created_at
            FROM comments
            WHERE resource_type = %s AND resource_id = %s
            ORDER BY created_at DESC
            """
            cursor.execute(query, (resource_type, resource_id))
            comments = cursor.fetchall()
            return comments
        except MySQLError as e:
            logger.error(f"Failed to fetch comments for {resource_type} {resource_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch comments: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()