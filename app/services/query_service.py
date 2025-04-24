from app.utils.utils import handle_query
from app.utils.database import get_clickhouse_client

def handle_query(question: str, username: str) -> dict:
    client = get_clickhouse_client()
    df_display, chart_fig, sql_query, explanation, recommendation, chart_title = handle_query(
        question, client, username, selected_model="Gemini"
    )
    return {
        "sql_query": sql_query,
        "explanation": explanation,
        "chart_title": chart_title,
        "suggested_chart_type": "Bar Chart" if not df_display else chart_fig.get("layout", {}).get("template", "Bar Chart"),
        "recommendation": recommendation,
        "data": df_display.to_dict(orient="records") if df_display is not None else None,
        "chart": chart_fig if chart_fig else None
    }