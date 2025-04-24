import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def create_chart(df, chart_type, chart_title, columns_metadata=None):
    # Tái sử dụng logic từ utils.py trong mã Streamlit
    # Chỉnh sửa để trả về dict thay vì đối tượng plotly trực tiếp
    if df.empty:
        return None
    
    # Áp dụng logic tương tự như trong create_chart của Streamlit
    # Ví dụ cho Line Chart:
    if chart_type == "Line Chart":
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
        datetime_columns = df.select_dtypes(include=['datetime64[ns]']).columns
        if len(numeric_columns) > 0 and len(datetime_columns) > 0:
            x_col = datetime_columns[0]
            y_col = numeric_columns[0]
            fig = px.line(df, x=x_col, y=y_col)
            fig.update_layout(title={'text': chart_title, 'x': 0.5, 'xanchor': 'center'})
            return fig
    # Thêm các loại biểu đồ khác tương tự
    return None