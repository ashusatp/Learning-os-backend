from fastapi import FastAPI

from app.exceptions.custom_exceptions import AppException
from app.exceptions.handlers import app_exception_handler, global_exception_handler


def register_exception_handlers(app: FastAPI):

    app.add_exception_handler(
        AppException,
        app_exception_handler,
    )

    app.add_exception_handler(
        Exception,
        global_exception_handler,
    )
