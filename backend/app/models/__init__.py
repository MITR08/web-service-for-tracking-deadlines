"""ORM-модели реляционной базы данных PostgreSQL 15+ (соответствуют Схемы_БД/database_model.qea)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Group(Base):
    """Учебная группа (п. 4.2.1.1, 4.5.1 ТЗ)."""

    __tablename__ = "groups"
    __table_args__ = (UniqueConstraint("name", "academic_year", name="uq_groups_name_year"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    faculty: Mapped[str | None] = mapped_column(String(150))
    course: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    current_semester: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    invite_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    invite_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Subgroup(Base):
    """Подгруппа учебной группы (п. 4.2.5, 4.5.1 ТЗ)."""

    __tablename__ = "subgroups"
    __table_args__ = (UniqueConstraint("group_id", "subgroup_number", name="uq_subgroups_group_num"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    subgroup_number: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


class User(Base):
    """Пользователь системы: Студент, Староста и задел Преподаватель (п. 4.1.3, 4.2.2, 4.15.5 ТЗ)."""

    __tablename__ = "users"
    __table_args__ = (Index("ix_users_group_roster", "group_id", "roster_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id", ondelete="SET NULL")
    )
    subgroup_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subgroups.id", ondelete="SET NULL")
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="STUDENT")
    roster_number: Mapped[int | None] = mapped_column(SmallInteger)
    membership_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    pdn_consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pdn_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_login_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    last_failed_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    theme_preference: Mapped[str] = mapped_column(String(10), nullable=False, default="SYSTEM")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class AuthSession(Base):
    """Сессии авторизации (Refresh Token) и токены сброса пароля (п. 4.2.1 ТЗ)."""

    __tablename__ = "auth_sessions"
    __table_args__ = (Index("ix_auth_sessions_user", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    token_type: Mapped[str] = mapped_column(String(20), nullable=False, default="REFRESH")
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Subject(Base):
    """Учебная дисциплина семестра (п. 4.5.2, 4.6.3 ТЗ)."""

    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("group_id", "name", "semester", name="uq_subjects_group_name_sem"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[str] = mapped_column(String(40), nullable=False)
    semester: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    teacher_full_name: Mapped[str | None] = mapped_column(String(150))
    teacher_email: Mapped[str | None] = mapped_column(String(150))
    teacher_consultation_info: Mapped[str | None] = mapped_column(String(255))
    external_course_url: Mapped[str | None] = mapped_column(String(500))
    assessment_type: Mapped[str] = mapped_column(String(20), nullable=False, default="EXAM")
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Task(Base):
    """Учебное задание с общим дедлайном и параметрами распределения вариантов (п. 4.2.4, 4.2.5 ТЗ)."""

    __tablename__ = "tasks"
    __table_args__ = (Index("ix_tasks_subject_deadline", "subject_id", "common_deadline"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    work_type: Mapped[str] = mapped_column(String(30), nullable=False, default="LAB")
    description: Mapped[str | None] = mapped_column(Text)
    grading_criteria: Mapped[str | None] = mapped_column(Text)
    external_links: Mapped[str | None] = mapped_column(Text)
    common_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    variants_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    variant_distribution_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="BY_ROSTER"
    )
    random_seed: Mapped[int | None] = mapped_column(Integer)
    max_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=Decimal("10.00"))
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SubgroupTaskDeadline(Base):
    """Дедлайн подгруппы по заданию — средний уровень приоритета (п. 4.2.5 ТЗ)."""

    __tablename__ = "subgroup_task_deadlines"
    __table_args__ = (UniqueConstraint("task_id", "subgroup_id", name="uq_subgroup_task_deadline"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    subgroup_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subgroups.id", ondelete="CASCADE"), nullable=False
    )
    subgroup_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    updated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class StudentTask(Base):
    """Индивидуальное задание студента: закреплённый вариант, персональный дедлайн, статус и подтверждение старостой."""

    __tablename__ = "student_tasks"
    __table_args__ = (
        UniqueConstraint("task_id", "student_id", name="uq_student_tasks_task_student"),
        Index("ix_student_tasks_student_status", "student_id", "status"),
        Index("ix_student_tasks_task_status", "task_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    variant_number: Mapped[int | None] = mapped_column(SmallInteger)
    variant_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    personal_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    personal_deadline_reason: Mapped[str | None] = mapped_column(String(255))
    student_reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    student_personal_note: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(25), nullable=False, default="NOT_STARTED")
    submission_url: Mapped[str | None] = mapped_column(String(500))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_comment: Mapped[str | None] = mapped_column(String(500))
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class TaskErrorReport(Base):
    """Сообщения студентов об ошибке в задании (п. 4.2.7 ТЗ)."""

    __tablename__ = "task_error_reports"
    __table_args__ = (Index("ix_task_error_reports_task", "task_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    resolution_comment: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Announcement(Base):
    """Объявления старосты (п. 4.5.8, 4.6.8 ТЗ)."""

    __tablename__ = "announcements"
    __table_args__ = (Index("ix_announcements_group_pinned", "group_id", "is_pinned", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL")
    )
    target_subgroup_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subgroups.id", ondelete="SET NULL")
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_important: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class AnnouncementRead(Base):
    """Отметки ознакомления студентов с объявлениями старосты (п. 4.5.8 ТЗ)."""

    __tablename__ = "announcement_reads"
    __table_args__ = (
        UniqueConstraint("announcement_id", "user_id", name="uq_announcement_reads_ann_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    announcement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FileRecord(Base):
    """Учебные материалы и файлы отчётов с антивирусной и архивной проверкой (п. 4.11 ТЗ)."""

    __tablename__ = "files"
    __table_args__ = (
        Index("ix_files_task", "task_id"),
        Index("ix_files_student_task", "student_task_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL")
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE")
    )
    student_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_tasks.id", ondelete="CASCADE")
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    extension: Mapped[str] = mapped_column(String(15), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    is_archive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    unpacked_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    archive_nesting_level: Mapped[int | None] = mapped_column(SmallInteger, default=0)
    antivirus_status: Mapped[str] = mapped_column(String(20), nullable=False, default="CLEAN")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Notification(Base):
    """Внутрисистемные уведомления и напоминания (п. 4.10 ТЗ)."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_recipient_unread", "recipient_id", "is_read", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    related_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE")
    )
    related_announcement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("announcements.id", ondelete="CASCADE")
    )
    notification_type: Mapped[str] = mapped_column(String(35), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_via_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AuditLog(Base):
    """Системный журнал аудита изменений дедлайнов, вариантов, статусов и событий ИБ (п. 4.1.6 ТЗ)."""

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_group_created", "group_id", "created_at"),
        Index("ix_audit_log_entity", "entity_type", "entity_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id", ondelete="SET NULL")
    )
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    old_values: Mapped[str | None] = mapped_column(Text)
    new_values: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(INET)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
