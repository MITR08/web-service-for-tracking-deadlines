"""Точка входа серверного приложения FastAPI со встроенной документацией Swagger / OpenAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings

OPENAPI_TAGS = [
    {
        "name": "Система и Мониторинг",
        "description": "Проверка доступности сервиса, состояния БД и метаданных схемы.",
    },
    {
        "name": "Авторизация и Группы (RBAC)",
        "description": "Вход (JWT), ступенчатая защита от брутфорса (CAPTCHA / блокировка) и инвайт-коды групп.",
    },
    {
        "name": "Дисциплины и Задания",
        "description": "Управление предметами, заданиями, приоритетом дедлайнов и распределением вариантов.",
    },
    {
        "name": "Объявления и Уведомления",
        "description": "Сущность «Объявления старосты» (Announcement) и внутрисистемный центр уведомлений.",
    },
    {
        "name": "Файлы и Аналитика",
        "description": "Загрузка материалов с антивирусной инспекцией архивов, календарь нагрузки N(d) и отчёты.",
    },
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "REST API сервер для учёта учебных заданий, каскадного контроля дедлайнов "
        "(Персональный > Подгруппа > Общий), распределения вариантов и верификации сдачи работ старостой."
    ),
    version="1.0.0",
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Система и Мониторинг"], summary="Корневой маршрут API")
def root() -> dict:
    """Перенаправление/информация о документации Swagger UI и OpenAPI."""
    return {
        "project": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "health_url": f"{settings.API_V1_PREFIX}/health",
    }
