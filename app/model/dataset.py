from mysql.connector import Error
from fastapi import HTTPException
from app.utils.database import get_mysql_connection
from typing import List, Dict

class DatasetModel:
    @staticmethod
    def create_dataset(database: str, table_name: str, schema_name: str) -> int:
        """
        Insert a new dataset into the datasets table.
        Returns the ID of the created dataset.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            query = """
            INSERT INTO datasets (`database`, table_name, schema_name)
            VALUES (%s, %s, %s)
            """
            values = (database, table_name, schema_name)
            cursor.execute(query, values)
            conn.commit()

            dataset_id = cursor.lastrowid
            return dataset_id
        except Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to create dataset: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def get_all_datasets() -> List[Dict]:
        """
        Retrieve all datasets from the datasets table.
        Returns a list of dictionaries with id, database, table_name, and schema_name.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor(dictionary=True)

            query = """
            SELECT id, `database`, table_name, schema_name
            FROM datasets
            """
            cursor.execute(query)
            datasets = cursor.fetchall()
            return datasets
        except Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch datasets: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @staticmethod
    def delete_dataset(dataset_id: int) -> bool:
        """
        Delete a dataset from the datasets table by ID.
        Returns True if deleted, False if dataset not found.
        """
        conn = None
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()

            query = """
            DELETE FROM datasets
            WHERE id = %s
            """
            cursor.execute(query, (dataset_id,))
            conn.commit()

            if cursor.rowcount == 0:
                return False
            return True
        except Error as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete dataset: {str(e)}")
        finally:
            if conn:
                cursor.close()
                conn.close()