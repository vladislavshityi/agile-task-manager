from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 500
    default_code = "internal_error"

    def __init__(self, detail: str, code: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code or self.default_code


class NotFound(AppError):
    status_code = 404
    default_code = "not_found"


class Forbidden(AppError):
    status_code = 403
    default_code = "forbidden"


class Conflict(AppError):
    status_code = 409
    default_code = "conflict"


class Unauthorized(AppError):
    status_code = 401
    default_code = "unauthorized"


class ValidationError(AppError):
    status_code = 422
    default_code = "validation_error"


class BadGateway(AppError):
    status_code = 502
    default_code = "bad_gateway"


class ServiceUnavailable(AppError):
    status_code = 503
    default_code = "service_unavailable"


class GatewayTimeout(AppError):
    status_code = 504
    default_code = "gateway_timeout"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, Unauthorized) else None
        return JSONResponse(
            {"detail": exc.detail, "code": exc.code},
            status_code=exc.status_code,
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        parts = [
            f"{'.'.join(str(p) for p in err['loc'][1:])}: {err['msg']}".strip(": ")
            for err in exc.errors()
        ]
        return JSONResponse(
            {"detail": "; ".join(parts), "code": "validation_error"}, status_code=422
        )
