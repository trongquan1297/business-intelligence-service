from fastapi import FastAPI
from app.routers import auth, chat, database_metadata, chart, dataset, dashboard
from app.dependencies import init_clients

app = FastAPI(title="AI Chat API", description="API for AI-powered chat and analytics")

@app.on_event("startup")
async def startup_event():
    init_clients()


app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(dataset.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(chart.router, prefix="/api/charts", tags=["charts"])
app.include_router(database_metadata.router, prefix="/api/database", tags=["charts"])
app.include_router(dashboard.router, prefix="/api/dashboards", tags=["dashboards"])

# app.include_router(history.router, prefix="/history", tags=["History"])
# app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/")
async def root():
    return {"message": "Welcome to AI Chat API"}