from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import configs
from app.core.logger import setup_logger
from app.exceptions.register import register_exception_handlers
from app.api.routes import auth, health, user, goal, subject, topic, subtopic, question, mistake, account, ai, issue, revision

setup_logger()

app = FastAPI(
    title=configs.APP_NAME,
    version="0.1.0",
)

cors_origins = [o.strip() for o in configs.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.ngrok-free\.app" if configs.DEBUG else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(goal.router, prefix="/api/v1")
app.include_router(subject.router, prefix="/api/v1")
app.include_router(topic.router, prefix="/api/v1")
app.include_router(subtopic.router, prefix="/api/v1")
app.include_router(question.router, prefix="/api/v1")
app.include_router(mistake.subtopic_router, prefix="/api/v1")
app.include_router(mistake.goal_router, prefix="/api/v1")
app.include_router(account.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(issue.router, prefix="/api/v1")
app.include_router(revision.router, prefix="/api/v1")
