-- =============================================================================
-- DDL-скрипт базы данных: Веб-сервис для учёта заданий и дедлайнов учебной группы
-- Целевая СУБД: PostgreSQL 15+
-- Соответствует модели Enterprise Architect: Схемы_БД/database_model.qea
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1. Учебные группы (Groups) — п. 4.2.1.1, 4.5.1 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE groups (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(50) NOT NULL,
    faculty             VARCHAR(150),
    course              SMALLINT NOT NULL DEFAULT 1 CHECK (course BETWEEN 1 AND 6),
    academic_year       VARCHAR(20) NOT NULL,
    current_semester    SMALLINT NOT NULL DEFAULT 1 CHECK (current_semester BETWEEN 1 AND 12),
    invite_code         VARCHAR(64) NOT NULL UNIQUE,
    invite_expires_at   TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_groups_name_year UNIQUE (name, academic_year)
);

COMMENT ON TABLE groups IS 'Учебные группы с инвайт-кодом для самостоятельной регистрации студентов (п. 4.2.1.1 ТЗ)';

-- -----------------------------------------------------------------------------
-- 2. Подгруппы учебной группы (Subgroups) — п. 4.2.5, 4.5.1 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE subgroups (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id            UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    subgroup_number     SMALLINT NOT NULL DEFAULT 1 CHECK (subgroup_number BETWEEN 1 AND 4),
    name                VARCHAR(50) NOT NULL,
    CONSTRAINT uq_subgroups_group_num UNIQUE (group_id, subgroup_number)
);

COMMENT ON TABLE subgroups IS 'Подгруппы учебной группы для дифференциации дедлайнов лабораторных/практических работ';

-- -----------------------------------------------------------------------------
-- 3. Пользователи (Users: Student, Starosta, задел Teacher) — п. 4.1.3, 4.2.2, 4.15.5 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id                    UUID REFERENCES groups(id) ON DELETE SET NULL,
    subgroup_id                 UUID REFERENCES subgroups(id) ON DELETE SET NULL,
    email                       VARCHAR(255) NOT NULL UNIQUE,
    password_hash               VARCHAR(255) NOT NULL,
    full_name                   VARCHAR(150) NOT NULL,
    role                        VARCHAR(20) NOT NULL DEFAULT 'STUDENT'
                                CHECK (role IN ('STUDENT', 'STAROSTA', 'TEACHER')),
    roster_number               SMALLINT CHECK (roster_number > 0),
    membership_status           VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                                CHECK (membership_status IN ('PENDING', 'ACTIVE', 'ARCHIVED')),
    pdn_consent_given           BOOLEAN NOT NULL DEFAULT false,
    pdn_consent_at              TIMESTAMPTZ,
    failed_login_attempts       SMALLINT NOT NULL DEFAULT 0,
    last_failed_login_at        TIMESTAMPTZ,
    locked_until                TIMESTAMPTZ,
    email_notifications_enabled BOOLEAN NOT NULL DEFAULT true,
    theme_preference            VARCHAR(10) NOT NULL DEFAULT 'SYSTEM'
                                CHECK (theme_preference IN ('LIGHT', 'DARK', 'SYSTEM')),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_users_group_roster ON users(group_id, roster_number);
COMMENT ON TABLE users IS 'Учётные записи студентов и старосты с согласием на обработку ПДн (Закон РБ № 99-З) и защитой от перебора паролей';

-- -----------------------------------------------------------------------------
-- 4. Сессии авторизации и токены восстановления пароля (AuthSessions) — п. 4.2.1 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE auth_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      VARCHAR(255) NOT NULL UNIQUE,
    token_type      VARCHAR(20) NOT NULL DEFAULT 'REFRESH'
                    CHECK (token_type IN ('REFRESH', 'PASSWORD_RESET', 'STAROSTA_INVITE')),
    ip_address      INET,
    user_agent      VARCHAR(500),
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_auth_sessions_user ON auth_sessions(user_id);

-- -----------------------------------------------------------------------------
-- 5. Учебные дисциплины (Subjects) — п. 4.5.2, 4.6.3 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE subjects (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id                    UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    name                        VARCHAR(200) NOT NULL,
    short_name                  VARCHAR(40) NOT NULL,
    semester                    SMALLINT NOT NULL DEFAULT 1,
    teacher_full_name           VARCHAR(150),
    teacher_email               VARCHAR(150),
    teacher_consultation_info   VARCHAR(255),
    external_course_url         VARCHAR(500),
    assessment_type             VARCHAR(20) NOT NULL DEFAULT 'EXAM'
                                CHECK (assessment_type IN ('EXAM', 'CREDIT', 'DIFF_CREDIT')),
    is_archived                 BOOLEAN NOT NULL DEFAULT false,
    created_by                  UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_subjects_group_name_sem UNIQUE (group_id, name, semester)
);

-- -----------------------------------------------------------------------------
-- 6. Учебные задания (Tasks) — п. 4.2.4, 4.2.5, 4.2.5.2 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE tasks (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id                  UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    title                       VARCHAR(255) NOT NULL,
    work_type                   VARCHAR(30) NOT NULL DEFAULT 'LAB'
                                CHECK (work_type IN ('LAB', 'PRACTICE', 'HOMEWORK', 'COURSEWORK', 'TEST', 'ESSAY')),
    description                 TEXT,
    grading_criteria            TEXT,
    external_links              TEXT,
    common_deadline             TIMESTAMPTZ NOT NULL,
    variants_count              SMALLINT NOT NULL DEFAULT 1 CHECK (variants_count >= 1),
    variant_distribution_mode   VARCHAR(20) NOT NULL DEFAULT 'BY_ROSTER'
                                CHECK (variant_distribution_mode IN ('NONE', 'BY_ROSTER', 'CYCLIC', 'RANDOM_SEED', 'MANUAL')),
    random_seed                 INTEGER,
    max_score                   NUMERIC(5,2) DEFAULT 10.00,
    is_archived                 BOOLEAN NOT NULL DEFAULT false,
    created_by                  UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_tasks_subject_deadline ON tasks(subject_id, common_deadline);

-- -----------------------------------------------------------------------------
-- 7. Дедлайны подгрупп (SubgroupTaskDeadlines) — средний приоритет (п. 4.2.5 ТЗ)
-- -----------------------------------------------------------------------------
CREATE TABLE subgroup_task_deadlines (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id             UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    subgroup_id         UUID NOT NULL REFERENCES subgroups(id) ON DELETE CASCADE,
    subgroup_deadline   TIMESTAMPTZ NOT NULL,
    reason              VARCHAR(255),
    updated_by          UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_subgroup_task_deadline UNIQUE (task_id, subgroup_id)
);

-- -----------------------------------------------------------------------------
-- 8. Индивидуальные задания студентов (StudentTasks) — п. 4.2.5, 4.9.1, 4.9.4 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE student_tasks (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id                     UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    student_id                  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    variant_number              SMALLINT CHECK (variant_number >= 1),
    variant_locked              BOOLEAN NOT NULL DEFAULT true,
    personal_deadline           TIMESTAMPTZ,
    personal_deadline_reason    VARCHAR(255),
    student_reminder_at         TIMESTAMPTZ,
    student_personal_note       VARCHAR(500),
    status                      VARCHAR(25) NOT NULL DEFAULT 'NOT_STARTED'
                                CHECK (status IN ('NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED', 'PASSED', 'NEEDS_REVISION')),
    submission_url              VARCHAR(500),
    submitted_at                TIMESTAMPTZ,
    verified_by                 UUID REFERENCES users(id) ON DELETE SET NULL,
    verified_at                 TIMESTAMPTZ,
    verification_comment        VARCHAR(500),
    score                       NUMERIC(5,2),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_student_tasks_task_student UNIQUE (task_id, student_id)
);

CREATE INDEX ix_student_tasks_student_status ON student_tasks(student_id, status);
CREATE INDEX ix_student_tasks_task_status ON student_tasks(task_id, status);

-- -----------------------------------------------------------------------------
-- 9. Сообщения об ошибке в задании (TaskErrorReports) — п. 4.2.7 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE task_error_reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id             UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    reporter_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message             TEXT NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'OPEN'
                        CHECK (status IN ('OPEN', 'RESOLVED', 'REJECTED')),
    resolved_by         UUID REFERENCES users(id) ON DELETE SET NULL,
    resolution_comment  VARCHAR(500),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at         TIMESTAMPTZ
);

CREATE INDEX ix_task_error_reports_task ON task_error_reports(task_id, status);

-- -----------------------------------------------------------------------------
-- 10. Объявления старосты (Announcements) — п. 4.5.8, 4.6.8 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE announcements (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id            UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    subject_id          UUID REFERENCES subjects(id) ON DELETE SET NULL,
    target_subgroup_id  UUID REFERENCES subgroups(id) ON DELETE SET NULL,
    author_id           UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title               VARCHAR(200) NOT NULL,
    content             TEXT NOT NULL,
    is_important        BOOLEAN NOT NULL DEFAULT false,
    is_pinned           BOOLEAN NOT NULL DEFAULT false,
    expires_at          TIMESTAMPTZ,
    is_archived         BOOLEAN NOT NULL DEFAULT false,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_announcements_group_pinned ON announcements(group_id, is_pinned, created_at DESC);

-- -----------------------------------------------------------------------------
-- 11. Отметки прочтения объявлений (AnnouncementReads) — п. 4.5.8 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE announcement_reads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    announcement_id UUID NOT NULL REFERENCES announcements(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    read_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_announcement_reads_ann_user UNIQUE (announcement_id, user_id)
);

-- -----------------------------------------------------------------------------
-- 12. Учебные материалы и файлы отчётов (Files) — п. 4.11.1–4.11.5 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE files (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id              UUID REFERENCES subjects(id) ON DELETE SET NULL,
    task_id                 UUID REFERENCES tasks(id) ON DELETE CASCADE,
    student_task_id         UUID REFERENCES student_tasks(id) ON DELETE CASCADE,
    uploaded_by             UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    original_filename       VARCHAR(255) NOT NULL,
    storage_key             VARCHAR(500) NOT NULL UNIQUE,
    extension               VARCHAR(15) NOT NULL
                            CHECK (extension IN ('pdf','docx','doc','xlsx','pptx','rtf','txt','zip','rar','7z','png','jpg','jpeg')),
    mime_type               VARCHAR(100) NOT NULL,
    size_bytes              BIGINT NOT NULL CHECK (size_bytes > 0 AND size_bytes <= 52428800),
    sha256_checksum         CHAR(64) NOT NULL,
    is_archive              BOOLEAN NOT NULL DEFAULT false,
    unpacked_size_bytes     BIGINT CHECK (unpacked_size_bytes IS NULL OR unpacked_size_bytes <= 209715200),
    archive_nesting_level   SMALLINT DEFAULT 0 CHECK (archive_nesting_level <= 2),
    antivirus_status        VARCHAR(20) NOT NULL DEFAULT 'CLEAN'
                            CHECK (antivirus_status IN ('PENDING', 'CLEAN', 'REJECTED_EXECUTABLE', 'REJECTED_VIRUS', 'REJECTED_ZIPBOMB')),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_files_task ON files(task_id);
CREATE INDEX ix_files_student_task ON files(student_task_id);

-- -----------------------------------------------------------------------------
-- 13. Внутрисистемные уведомления и напоминания (Notifications) — п. 4.10 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE notifications (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    related_task_id         UUID REFERENCES tasks(id) ON DELETE CASCADE,
    related_announcement_id UUID REFERENCES announcements(id) ON DELETE CASCADE,
    notification_type       VARCHAR(35) NOT NULL
                            CHECK (notification_type IN (
                                'DEADLINE_72H', 'DEADLINE_24H', 'DEADLINE_2H',
                                'DEADLINE_CHANGED', 'VARIANT_ASSIGNED',
                                'STATUS_VERIFIED', 'ANNOUNCEMENT', 'STALE_SUBMISSION_14D'
                            )),
    title                   VARCHAR(200) NOT NULL,
    body                    TEXT NOT NULL,
    is_read                 BOOLEAN NOT NULL DEFAULT false,
    read_at                 TIMESTAMPTZ,
    sent_via_email          BOOLEAN NOT NULL DEFAULT false,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_notifications_recipient_unread ON notifications(recipient_id, is_read, created_at DESC);

-- -----------------------------------------------------------------------------
-- 14. Журнал аудита безопасности и изменений (AuditLog) — п. 4.1.6 ТЗ
-- -----------------------------------------------------------------------------
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    actor_id        UUID REFERENCES users(id) ON DELETE SET NULL,
    group_id        UUID REFERENCES groups(id) ON DELETE SET NULL,
    entity_type     VARCHAR(40) NOT NULL,
    entity_id       UUID,
    action          VARCHAR(50) NOT NULL,
    old_values      TEXT,
    new_values      TEXT,
    ip_address      INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_audit_log_group_created ON audit_log(group_id, created_at DESC);
CREATE INDEX ix_audit_log_entity ON audit_log(entity_type, entity_id);

-- =============================================================================
-- АНАЛИТИЧЕСКИЕ ПРЕДСТАВЛЕНИЯ (VIEWS)
-- =============================================================================

-- 1. Вычисление действующего дедлайна по правилу приоритета: Личный > Подгруппа > Общий (п. 4.2.5)
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

-- 2. Расчёт концентрации дедлайнов N(d) и маркировка дней высокой нагрузки N(d) >= 3 (п. 4.8.1)
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

-- 3. Ведомость академических задолженностей по верифицированным статусам (п. 4.9.4, 4.13.2)
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
