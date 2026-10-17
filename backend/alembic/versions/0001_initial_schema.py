"""Initial database schema (14 tables + 3 analytical views).

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-10-17 12:40:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.models import Base

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создание всех 14 реляционных таблиц и 3 аналитических представлений PostgreSQL."""
    bind = op.get_bind()
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto";'))
    Base.metadata.create_all(bind=bind)

    op.execute(
        sa.text(
            """
            CREATE OR REPLACE VIEW vw_effective_student_deadlines AS
            SELECT
                st.id AS student_task_id,
                st.student_id,
                u.full_name,
                u.group_id,
                u.subgroup_id,
                st.task_id,
                t.subject_id,
                t.title AS task_title,
                st.variant_number,
                st.status,
                t.common_deadline,
                std.subgroup_deadline,
                st.personal_deadline,
                COALESCE(st.personal_deadline, std.subgroup_deadline, t.common_deadline) AS effective_deadline,
                CASE
                    WHEN st.personal_deadline IS NOT NULL THEN 'PERSONAL'
                    WHEN std.subgroup_deadline IS NOT NULL THEN 'SUBGROUP'
                    ELSE 'COMMON'
                END AS deadline_source,
                (st.status <> 'PASSED' AND now() > COALESCE(st.personal_deadline, std.subgroup_deadline, t.common_deadline)) AS is_overdue
            FROM student_tasks st
            JOIN users u ON u.id = st.student_id
            JOIN tasks t ON t.id = st.task_id
            LEFT JOIN subgroup_task_deadlines std
                ON std.task_id = t.id AND std.subgroup_id = u.subgroup_id;
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE OR REPLACE VIEW vw_daily_workload_calendar AS
            SELECT
                student_id,
                group_id,
                DATE(effective_deadline) AS deadline_date,
                COUNT(*) FILTER (WHERE status <> 'PASSED') AS active_deadlines_count,
                CASE
                    WHEN COUNT(*) FILTER (WHERE status <> 'PASSED') >= 3 THEN 'HIGH'
                    WHEN COUNT(*) FILTER (WHERE status <> 'PASSED') = 2 THEN 'MEDIUM'
                    ELSE 'NORMAL'
                END AS workload_level
            FROM vw_effective_student_deadlines
            GROUP BY student_id, group_id, DATE(effective_deadline);
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE OR REPLACE VIEW vw_group_academic_arrears AS
            SELECT
                u.group_id,
                s.id AS subject_id,
                s.name AS subject_name,
                u.id AS student_id,
                u.full_name AS student_name,
                COUNT(t.id) AS total_tasks,
                COUNT(*) FILTER (WHERE st.status = 'PASSED') AS passed_verified_count,
                COUNT(*) FILTER (WHERE st.status = 'SUBMITTED') AS awaiting_verification_count,
                COUNT(*) FILTER (
                    WHERE st.status <> 'PASSED'
                      AND now() > COALESCE(st.personal_deadline, std.subgroup_deadline, t.common_deadline)
                ) AS arrears_overdue_count
            FROM users u
            JOIN subjects s ON s.group_id = u.group_id
            JOIN tasks t ON t.subject_id = s.id
            JOIN student_tasks st ON st.task_id = t.id AND st.student_id = u.id
            LEFT JOIN subgroup_task_deadlines std
                ON std.task_id = t.id AND std.subgroup_id = u.subgroup_id
            WHERE u.role IN ('STUDENT', 'STAROSTA')
            GROUP BY u.group_id, s.id, s.name, u.id, u.full_name;
            """
        )
    )


def downgrade() -> None:
    """Откат представлений и таблиц."""
    bind = op.get_bind()
    op.execute(sa.text("DROP VIEW IF EXISTS vw_group_academic_arrears;"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_daily_workload_calendar;"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_effective_student_deadlines;"))
    Base.metadata.drop_all(bind=bind)
