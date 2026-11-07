"""Application errors mapped to friendly API responses."""

from __future__ import annotations


class AppError(Exception):
    """An error that can be shown safely to the user."""

    status_code = 400

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ValidationError(AppError):
    status_code = 400


class SelectionError(ValidationError):
    pass


class PathNotAllowedError(AppError):
    status_code = 403


class PathNotFoundError(AppError):
    status_code = 404


class PathExistsError(AppError):
    status_code = 409


class ToolUnavailableError(AppError):
    status_code = 503


class YtDlpError(AppError):
    status_code = 422


class CommandTimeoutError(AppError):
    status_code = 504
