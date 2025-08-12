import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        reload_excludes=["*.log", "logs/*", "app/logs/*"],
    )
