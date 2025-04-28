from fastapi import APIRouter, Depends, HTTPException
from app.schemas.comment import CommentCreate, CommentResponse
from app.model.comment import CommentModel
from app.utils.database import get_mysql_connection
from app.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=CommentResponse)
async def create_comment(comment_data: CommentCreate, current_user: str = Depends(get_current_user)):
    """
    Create a new comment for a resource. Requires view access to the resource.
    Requires JWT authentication.
    """
    comment_id = CommentModel.create_comment(comment_data.dict(), current_user)
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, resource_type, resource_id, username, content, created_at
            FROM comments
            WHERE id = %s
        """, (comment_id,))
        comment = cursor.fetchone()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        return {
            "id": comment["id"],
            "resource_type": comment["resource_type"],
            "resource_id": comment["resource_id"],
            "username": comment["username"],
            "content": comment["content"],
            "created_at": comment["created_at"],
            "message": "Comment created successfully"
        }
    finally:
        cursor.close()
        conn.close()

@router.delete("/{comment_id}", response_model=CommentResponse)
async def delete_comment(comment_id: int, current_user: str = Depends(get_current_user)):
    """
    Delete a comment by ID. Only the comment author can delete.
    Requires JWT authentication.
    """
    conn = get_mysql_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, resource_type, resource_id, username, content, created_at
            FROM comments
            WHERE id = %s
        """, (comment_id,))
        comment = cursor.fetchone()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        if not CommentModel.delete_comment(comment_id, current_user):
            raise HTTPException(status_code=404, detail="Comment not found")
        return {
            "id": comment["id"],
            "resource_type": comment["resource_type"],
            "resource_id": comment["resource_id"],
            "username": comment["username"],
            "content": comment["content"],
            "created_at": comment["created_at"],
            "message": "Comment deleted successfully"
        }
    finally:
        cursor.close()
        conn.close()