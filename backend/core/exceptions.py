"""
Exception handlers for Prometrix backend
"""

import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("prometrix.exceptions")


class PrometrixException(Exception):
    """Base exception for Prometrix application"""
    
    def __init__(self, message: str, code: str = "PROMETRIX_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(PrometrixException):
    """Validation error"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class NotFoundError(PrometrixException):
    """Resource not found error"""
    
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, "NOT_FOUND")


class LLMProviderError(PrometrixException):
    """LLM provider error"""
    
    def __init__(self, provider: str, message: str, details: Dict[str, Any] = None):
        super().__init__(f"LLM Provider ({provider}) error: {message}", "LLM_ERROR", details)
        self.provider = provider


class StorageError(PrometrixException):
    """Storage operation error"""
    
    def __init__(self, operation: str, message: str, details: Dict[str, Any] = None):
        super().__init__(f"Storage {operation} error: {message}", "STORAGE_ERROR", details)


async def prometrix_exception_handler(request: Request, exc: PrometrixException):
    """Handle custom Prometrix exceptions"""
    logger.error(f"Prometrix exception: {exc.code} - {exc.message}", extra={
        "code": exc.code,
        "details": exc.details,
        "path": request.url.path
    })
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()}", extra={
        "path": request.url.path,
        "errors": exc.errors()
    })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "errors": exc.errors()
                }
            }
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}", extra={
        "status_code": exc.status_code,
        "path": request.url.path
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", extra={
        "path": request.url.path,
        "exception_type": type(exc).__name__
    }, exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    )


def setup_exception_handlers(app: FastAPI):
    """Setup exception handlers for the FastAPI app"""
    app.add_exception_handler(PrometrixException, prometrix_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)