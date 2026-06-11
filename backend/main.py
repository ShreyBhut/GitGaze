import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from analysis.orchestrator import AnalyzerOrchestrator

# Pydantic model to automatically validate incoming JSON requests
class AnalyzeRequest(BaseModel):
    repo_path: str

def create_app() -> FastAPI:
    app = FastAPI(
        title="GitGaze API",
        description="Repository Analysis & Visualization System",
        version="0.1.0",
    )

    # Configure CORS to allow our frontend to communicate with the backend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Note: For production, we will lock this down to the frontend URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "GitGaze Backend"}

    @app.post("/api/analyze")
    async def analyze_repository(request: AnalyzeRequest):
        """
        Takes a local repository path, runs the core analysis engine, 
        and returns the structured repository data.
        """
        if not os.path.exists(request.repo_path):
            raise HTTPException(status_code=400, detail="Repository path does not exist on the server.")
        
        try:
            orchestrator = AnalyzerOrchestrator(request.repo_path)
            results = orchestrator.analyze_repo()
            return {"status": "success", "data": results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return app

app = create_app()