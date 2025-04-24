import json
import uuid
from datetime import datetime, date
import numpy as np
import pandas as pd
from app.utils.database import get_mysql_connection

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Series):
            return obj.tolist()
        return super().default(obj)
    
def convert_numpy_types(data):
    """Chuyển đổi các kiểu dữ liệu NumPy trong dict thành Python native types"""
    if isinstance(data, dict):
        return {key: convert_numpy_types(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_numpy_types(item) for item in data]
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, pd.Series):
        return data.tolist()
    return data

def deserialize_dataframe(data_json):
    """Chuyển đổi JSON thành DataFrame với xử lý datetime"""
    if not data_json:
        return None
    
    try:
        df_dict = json.loads(data_json)
        df = pd.DataFrame.from_dict(df_dict)
        
        # Cố gắng chuyển đổi các cột có dạng datetime string về datetime
        for column in df.columns:
            try:
                if isinstance(df[column].iloc[0], str):
                    # Thử chuyển đổi về datetime
                    df[column] = pd.to_datetime(df[column])
            except:
                continue
        
        return df
    except Exception as e:
        return None

def save_query_history(username, question, explanation, sql_query, df=None, chart_type=None, chart_fig=None, chart_title=None):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        query_id = str(uuid.uuid4())
        
        data_json = None
        if df is not None:
            df_copy = df.copy()
            for column in df_copy.columns:
                if pd.api.types.is_datetime64_any_dtype(df_copy[column]) or pd.api.types.is_period_dtype(df_copy[column]):
                    df_copy[column] = df_copy[column].astype(str)
                elif pd.api.types.is_numeric_dtype(df_copy[column]):
                    df_copy[column] = df_copy[column].astype(float)
            df_dict = df_copy.to_dict()
            df_dict = convert_numpy_types(df_dict)
            data_json = json.dumps(df_dict, cls=CustomJSONEncoder)
        
        chart_json = None
        if chart_fig is not None:
            chart_json = json.dumps(convert_numpy_types(chart_fig), cls=CustomJSONEncoder)
        else:
            chart_json = json.dumps({})
        
        sql = """
        INSERT INTO query_history (id, username, timestamp, question, explanation, sql_query, data, chart_type, chart_fig, chart_title, execution_time)
        VALUES (%s, %s, NOW(),%s, %s, %s, %s, %s, %s, %s, 0.0)
        """
        cursor.execute(sql, (query_id, username, question, explanation, sql_query, data_json, chart_type, chart_json, chart_title))
        conn.commit()
        cursor.close()
        conn.close()
        return query_id
    except Exception as e:
        return None

def load_query_history(username):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        sql = """
        SELECT id, timestamp, question,explanation, sql_query, data, chart_type, chart_fig, chart_title
        FROM query_history
        WHERE username = %s
        ORDER BY timestamp DESC
        LIMIT 5
        """
        cursor.execute(sql, (username,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "question": row[2],
                "explanation": row[3],
                "sql_query": row[4],
                "data": deserialize_dataframe(row[5]) if row[5] else None,
                "chart_type": row[6],
                "chart_fig": json.loads(row[7]) if isinstance(row[7], str) and row[7].strip() else None,
                "chart_title": row[8]
            }
            for row in result
        ]
    except Exception as e:
        return []
    
def delete_query_from_history(query_id):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        sql = "DELETE FROM query_history WHERE id = %s"
        cursor.execute(sql, (query_id,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

