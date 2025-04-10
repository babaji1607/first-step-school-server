# main.py
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from database import create_db_and_tables, get_session, SessionDep
from routers import students, teachers

app = FastAPI(
    title="Student Attendance API", 
    description="API for tracking student absences",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def root():
    """Get basic API information and available endpoints"""
    return {
        "name": "Student Attendance API",
        "version": "1.0.0",
        "description": "API for tracking student, teacher, and admin activities in an educational system",
        "endpoints": [
            "/students - Student management",
            "/teachers - Teacher dashboard and functions",
            "/docs - Interactive API documentation",
            "/redoc - Alternative documentation"
        ]
    }

@app.get("/api-info", include_in_schema=False)
async def get_api_info(request: Request):
    """Detailed API information with discovered endpoints"""
    def get_all_endpoints():
        endpoints = []
        for route in app.routes:
            if isinstance(route, APIRoute):
                endpoints.append({
                    "path": route.path,
                    "name": route.name,
                    "methods": list(route.methods)
                })
        return endpoints
    
    base_url = str(request.base_url)
    return {
        "api": "Student Attendance API",
        "version": "1.0.0",
        "description": "Comprehensive API for educational institution management",
        "documentation": f"{base_url}docs",
        "endpoints": get_all_endpoints()
    }

# Include all routers
app.include_router(students.router)
app.include_router(teachers.router)

# Add sample data for testing
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # Sample data can be added here if needed
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)