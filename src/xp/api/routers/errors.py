from starlette import status
from starlette.responses import JSONResponse

from xp.api.models.discover import DiscoverErrorResponse


def handle_service_error(
    error: str, default_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """
    Handle service errors by creating a standardized JSON error response.

    Args:
        error: Service response object with success and error attributes
        default_status_code: HTTP status code to use (defaults to 500)

    Returns:
        JSONResponse with error details
    """
    error_msg = error or "Unknown service error"

    # Map specific error patterns to appropriate HTTP status codes
    if "Not connected to server" in error_msg:
        status_code = status.HTTP_400_BAD_REQUEST
    elif "Failed to generate telegram" in error_msg:
        status_code = status.HTTP_400_BAD_REQUEST
    elif "Response timeout" in error_msg:
        status_code = status.HTTP_408_REQUEST_TIMEOUT
    elif "Failed to send telegram" in error_msg:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        status_code = default_status_code

    return JSONResponse(
        status_code=status_code,
        content=DiscoverErrorResponse(error=error_msg).model_dump(),
    )
