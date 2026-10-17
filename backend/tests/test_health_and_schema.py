"""Автотесты базовой конфигурации REST API, Swagger/OpenAPI и ORM-схемы БД."""

from fastapi.testclient import TestClient

from app.main import app
from app.models import Base

client = TestClient(app)

EXPECTED_TABLES = {
    "groups",
    "subgroups",
    "users",
    "auth_sessions",
    "subjects",
    "tasks",
    "subgroup_task_deadlines",
    "student_tasks",
    "task_error_reports",
    "announcements",
    "announcement_reads",
    "files",
    "notifications",
    "audit_log",
}


def test_healthcheck_and_orm_tables() -> None:
    """Проверка /api/v1/health и регистрации всех 14 таблиц БД в метаданных SQLAlchemy."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["orm_tables_registered"] == 14
    assert set(payload["tables"]) == EXPECTED_TABLES
    assert set(Base.metadata.tables.keys()) == EXPECTED_TABLES


def test_openapi_swagger_schema() -> None:
    """Проверка генерации спецификации OpenAPI (/openapi.json) и Swagger UI (/docs)."""
    openapi_res = client.get("/openapi.json")
    assert openapi_res.status_code == 200
    schema = openapi_res.json()
    assert "/api/v1/health" in schema["paths"]

    docs_res = client.get("/docs")
    assert docs_res.status_code == 200
