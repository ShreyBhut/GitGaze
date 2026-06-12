import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from analysis.orchestrator import AnalyzerOrchestrator

# UPDATE 1: Change 'repo_path' to 'path' to match the frontend JSON
class AnalyzeRequest(BaseModel):
    path: str

def create_app() -> FastAPI:
    app = FastAPI(
        title="GitGaze API",
        description="Repository Analysis & Visualization System",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
        # UPDATE 2: Change request.repo_path to request.path
        if not os.path.exists(request.path):
            raise HTTPException(status_code=400, detail="Repository path does not exist on the server.")
        
        try:
            # UPDATE 3: Change request.repo_path to request.path
            orchestrator = AnalyzerOrchestrator(request.path)
            results = orchestrator.analyze_repo()
            return {"status": "success", "data": results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return app

app = create_app()