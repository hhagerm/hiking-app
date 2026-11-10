from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from hiking_app.core.exceptions import APIException

async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    body = {"code": exc.code, "message": exc.message}
    if exc.field:
        body["field"] = exc.field
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": body},
        headers=exc.headers,
    )
    
def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(APIException, api_exception_handler)
    