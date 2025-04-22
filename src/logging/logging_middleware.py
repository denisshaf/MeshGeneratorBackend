import logging
from typing import Callable, Awaitable, cast
import json

from fastapi import BackgroundTasks, Request, Response
from fastapi.responses import StreamingResponse
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.applications import Starlette

from .logging_config import setup_logging

setup_logging()
http_logger = logging.getLogger('http')
debug_logger = logging.getLogger('debug')


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Starlette, excluded_paths: list[str] | None = None) -> None:
        super().__init__(app)
        self.excluded_paths = excluded_paths or []

    async def _log_request(self, request: Request, request_body: bytes) -> None:
        try:
            body_json = json.loads(request_body)
            formatted_body = json.dumps(body_json, indent=2)
        except:
            formatted_body = request_body.decode('utf-8', errors='replace')

        http_logger.debug(
            f"\n{'=' * 50}\n"
            f"REQUEST:\n"
            f"Method: {request.method}\n"
            f"URL: {request.url}\n"
            f"Headers: {dict(request.headers)}\n"
            f"Body: \n{formatted_body}\n"
            f"{'=' * 50}"
        )

    def _log_response(self, response: StreamingResponse, response_body: bytes | None = None) -> None:
        if response_body:
            try:
                body_json = json.loads(response_body)
                formatted_body = json.dumps(body_json, indent=2)
            except:
                formatted_body = response_body.decode('utf-8', errors='replace')
        
        http_logger.debug(
            f"\n{'=' * 50}\n"
            f"RESPONSE:\n"
            f"Status Code: {response.status_code}\n"
            f"Headers: {dict(response.headers)}\n"
            f"Body: \n{formatted_body}\n" if response_body else ''
            f"{'=' * 50}"
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> StreamingResponse:
        request_body = await request.body()
        response = cast(StreamingResponse, await call_next(request))
        path = request.url.path

        if any(excluded_path in path for excluded_path in self.excluded_paths):
            response_body = None
        else:
            response_body_list = [cast(bytes, chunk) async for chunk in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body_list))
            response_body = b''.join(response_body_list)

        tasks = BackgroundTasks()
        tasks.add_task(self._log_request, request, request_body)
        tasks.add_task(self._log_response, response, response_body)
        response.background = tasks
        return response
