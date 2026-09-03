from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.routes import router
from app.models.execution import ErrorCategory, ExecutionError
from app.models.responses import AgentRunResponseFailure
from app.utils.logger import get_logger, setup_logging
from app.utils.metrics import get_metrics_response, prometheus_metrics_middleware

setup_logging()
logger = get_logger()

app = FastAPI(
    title="Multi-Agent AI Execution Platform",
    description="Core execution engine for Phase 1 multi-agent AI task planning, execution, evaluation, and recovery.",
    version="1.0.0",
)

# Register Prometheus HTTP Middleware
app.middleware("http")(prometheus_metrics_middleware)

app.include_router(router)


@app.get("/metrics", tags=["Observability"])
async def metrics_endpoint():
    """Prometheus metrics scraping endpoint."""
    return get_metrics_response()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler ensuring stack traces are never exposed raw."""
    logger.error(f"Unhandled exception caught at API boundary: {str(exc)}", exc_info=True)
    error_response = AgentRunResponseFailure(
        execution_id="exec_error",
        status="failed",
        error=ExecutionError(
            code=ErrorCategory.INTERNAL_ERROR,
            message="An unexpected internal server error occurred.",
            details={"path": str(request.url)},
        ),
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
