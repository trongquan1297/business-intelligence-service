import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from typing import Tuple, Optional, Dict, List, Any
from app.utils import gemini, openai
from app.services.permission_service import get_role_table_groups, execute_query_with_permission

def predict_trend(df: pd.DataFrame, x_col: str, y_col: str, future_periods: int = 5) -> Tuple[Optional[pd.DataFrame], Optional[float]]:
    """
    Dự đoán xu hướng dựa trên dữ liệu thời gian và cột số.

    Args:
        df (pd.DataFrame): DataFrame chứa dữ liệu gốc.
        x_col (str): Tên cột trục X (thường là thời gian).
        y_col (str): Tên cột trục Y (giá trị số).
        future_periods (int): Số khoảng thời gian dự đoán trong tương lai.

    Returns:
        Tuple[Optional[pd.DataFrame], Optional[float]]: DataFrame kết hợp dữ liệu thực tế và dự đoán, cùng với R² score.
    """
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        return None, None

    # Chuyển đổi cột thời gian thành số (timestamp) để hồi quy
    if pd.api.types.is_datetime64_any_dtype(df[x_col]):
        df = df.copy()
        df['time_numeric'] = (pd.to_datetime(df[x_col]) - pd.to_datetime(df[x_col]).min()).dt.total_seconds() / 86400  # Chuyển thành ngày
    else:
        return None, None

    # Chuẩn bị dữ liệu cho mô hình
    X = df[['time_numeric']].values
    y = df[y_col].values

    # Huấn luyện mô hình hồi quy tuyến tính
    model = LinearRegression()
    model.fit(X, y)

    # Dự đoán cho dữ liệu hiện tại
    y_pred = model.predict(X)

    # Dự đoán cho tương lai
    last_time = X[-1][0]
    future_X = np.array([[last_time + i] for i in range(1, future_periods + 1)])
    future_y = model.predict(future_X)

    # Tạo DataFrame cho dữ liệu dự đoán
    future_dates = pd.date_range(start=df[x_col].max(), periods=future_periods + 1, freq='D')[1:]
    trend_df = pd.DataFrame({
        x_col: future_dates,
        y_col: future_y,
        'Type': 'Dự đoán'
    })

    # Thêm dữ liệu gốc với nhãn 'Thực tế'
    original_df = df[[x_col, y_col]].copy()
    original_df['Type'] = 'Thực tế'

    # Kết hợp dữ liệu thực tế và dự đoán
    combined_df = pd.concat([original_df, trend_df], ignore_index=True)

    return combined_df, model.score(X, y)

def create_chart(df: pd.DataFrame, chart_type: str, chart_title: str, columns_metadata: Optional[Dict[str, Dict]] = None) -> Optional[Dict]:
    """
    Tạo biểu đồ dựa trên loại, dữ liệu và metadata.

    Args:
        df (pd.DataFrame): DataFrame chứa dữ liệu để vẽ biểu đồ.
        chart_type (str): Loại biểu đồ (Line Chart, Bar Chart, Pie Chart, Scatter Plot, Box Plot).
        chart_title (str): Tiêu đề của biểu đồ.
        columns_metadata (Optional[Dict]): Metadata của các cột để đổi tên hiển thị.

    Returns:
        Optional[Dict]: Đối tượng biểu đồ Plotly dưới dạng dict, hoặc None nếu thất bại.
    """
    if df.empty:
        return None

    try:
        # Rename columns based on metadata if available
        if columns_metadata:
            df = df.copy()
            display_names = {col: meta.get('display_name', col) for col, meta in columns_metadata.items() if col in df.columns}
            df = df.rename(columns=display_names)

        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
        datetime_columns = df.select_dtypes(include=['datetime64[ns]']).columns
        categorical_columns = df.select_dtypes(include=['object']).columns

        # Layout configuration for centered title
        title_config = {'text': chart_title, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'}

        if chart_type == "Line Chart" and len(numeric_columns) > 0:
            x_col = datetime_columns[0] if len(datetime_columns) > 0 else categorical_columns[0] if len(categorical_columns) > 0 else df.columns[0]
            y_col = next((col for col in numeric_columns if col != x_col), numeric_columns[0])

            trend_df, r2_score = predict_trend(df, x_col, y_col)
            if trend_df is not None:
                fig = px.line(trend_df, x=x_col, y=y_col, color='Type', line_dash='Type', title=f"{chart_title} (R² = {r2_score:.2f})")
                fig.update_layout(title=title_config)
                return fig.to_dict()
            else:
                fig = px.line(df, x=x_col, y=y_col)
                fig.update_layout(title=title_config)
                return fig.to_dict()

        elif chart_type == "Bar Chart" and len(numeric_columns) > 0:
            if len(categorical_columns) > 0:
                x_col = categorical_columns[0]
                y_col = numeric_columns[0]
            else:
                if len(numeric_columns) < 2:
                    raise ValueError("Need at least 2 columns (one for X, one for Y) for Bar Chart")
                x_col = numeric_columns[0]
                y_col = numeric_columns[1]
            fig = px.bar(df, x=x_col, y=y_col, color=x_col if x_col in df.columns else None, color_discrete_sequence=px.colors.qualitative.Plotly)
            fig.update_traces(showlegend=False)
            fig.update_layout(title=title_config)
            return fig.to_dict()

        elif chart_type == "Pie Chart" and len(categorical_columns) > 0 and len(numeric_columns) > 0:
            fig = px.pie(df, names=categorical_columns[0], values=numeric_columns[0])
            fig.update_layout(title=title_config)
            return fig.to_dict()

        elif chart_type == "Scatter Plot" and len(numeric_columns) >= 2:
            fig = px.scatter(df, x=numeric_columns[0], y=numeric_columns[1])
            fig.update_layout(title=title_config)
            return fig.to_dict()

        elif chart_type == "Box Plot" and len(numeric_columns) > 0:
            fig = px.box(df, y=numeric_columns[0])
            fig.update_layout(title=title_config)
            return fig.to_dict()

    except Exception as e:
        raise Exception(f"Error creating chart: {str(e)}")

    return None

def handle_query(question: str, client: Any, username: str, selected_model: str = "Gemini") -> Tuple[
    Optional[pd.DataFrame], Optional[Dict], str, str, List[str], str
]:
    """
    Xử lý câu query và trả về kết quả có metadata và kiểm tra quyền.

    Args:
        question (str): Câu hỏi từ người dùng.
        client (Any): Client ClickHouse để thực thi query.
        username (str): Tên người dùng để kiểm tra quyền.
        selected_model (str): Model AI để chuyển đổi câu hỏi thành SQL (OpenAI hoặc Gemini).

    Returns:
        Tuple: (df_display, chart_fig, sql_query, explanation, recommendation, chart_title)
    """
    try:
        # Chọn model AI
        convert_func = openai.convert_to_sql if selected_model == "OpenAI" else gemini.convert_to_sql

        # Chuyển đổi câu hỏi thành SQL với kiểm tra quyền
        sql_query, explanation, chart_title, suggested_chart_type, recommendation, columns_metadata = convert_func(
            question, username
        )

        # Nếu không có SQL, trả về ngay
        if not sql_query:
            return None, None, sql_query, explanation, recommendation, chart_title

        # Thực thi query với kiểm tra quyền
        result = execute_query_with_permission(client, sql_query, username)

        if result:
            # Tạo DataFrame từ kết quả
            df = pd.DataFrame(result[0], columns=[col[0] for col in result[1]])

            # Tạo biểu đồ với loại biểu đồ được đề xuất
            chart_fig = create_chart(df, suggested_chart_type, chart_title, columns_metadata)

            # Format tên hiển thị cho DataFrame
            df_display = df.copy()
            display_names = {col: meta['display_name'] for col, meta in columns_metadata.items() if col in df.columns}
            df_display = df_display.rename(columns=display_names)

            return df_display, chart_fig, sql_query, explanation, recommendation, chart_title

        return None, None, sql_query, explanation, recommendation, chart_title

    except Exception as e:
        raise Exception(f"Error handling query: {str(e)}")