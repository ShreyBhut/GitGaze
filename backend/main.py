from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(
        title="GitGaze API",
        description="Repository Analysis & Visualization System",
        version="0.1.0",
    )

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "GitGaze Backend"}

    return app

app = create_app()