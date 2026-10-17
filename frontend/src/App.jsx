import { NavLink, Route, Routes, useParams } from 'react-router-dom';

function DashboardPage() {
  return (
    <section className="card">
      <h2>Главный экран (Дашборд)</h2>
      <p>
        Точка отсчёта для правила навигации <strong>2–3 клика</strong> (п. 4.3.1, 4.6.1 ТЗ).
        Содержит сводку «Ближайшие дедлайны на 7 дней», «Горящие дедлайны» (&lt; 24 ч),
        круговой индикатор прогресса и закреплённые объявления старосты.
      </p>
      <div className="grid">
        <div className="stat-box urgent">Горящие дедлайны (&lt; 24 ч): 1</div>
        <div className="stat-box warning">Ближайшие 7 дней: 3</div>
        <div className="stat-box success">Зачтено старостой: 12 / 16</div>
      </div>
    </section>
  );
}

function SectionPage({ title, clause, description }) {
  const params = useParams();
  return (
    <section className="card">
      <h2>{title}</h2>
      <p className="badge">Пункт ТЗ: {clause}</p>
      <p>{description}</p>
      {params.id && <p>Выбранный идентификатор: <code>{params.id}</code></p>}
      {params.inviteCode && <p>Инвайт-код учебной группы: <code>{params.inviteCode}</code></p>}
    </section>
  );
}

export default function App() {
  return (
    <div className="app-layout">
      <header className="top-header">
        <div className="brand">
          <span className="logo-dot" />
          <strong>ДедлайнТрекер</strong>
          <span className="subtitle">Учебная группа</span>
        </div>
        <nav className="main-nav" aria-label="Основная навигация (1 клик от Дашборда)">
          <NavLink to="/" end>Дашборд</NavLink>
          <NavLink to="/calendar">Календарь N(d)</NavLink>
          <NavLink to="/subjects">Предметы</NavLink>
          <NavLink to="/tasks">Все задания</NavLink>
          <NavLink to="/announcements">Объявления</NavLink>
          <NavLink to="/analytics">Старостат / Аналитика</NavLink>
          <NavLink to="/profile">Профиль</NavLink>
        </nav>
        <div className="header-actions">
          <span className="bell" title="Центр внутрисистемных уведомлений (п. 4.10.1 ТЗ)">
            🔔 <small>3</small>
          </span>
        </div>
      </header>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route
            path="/calendar"
            element={
              <SectionPage
                title="Календарь дедлайнов и расчёт нагрузки N(d)"
                clause="п. 4.6.2, 4.8.1–4.8.3"
                description="Интерактивный календарь («Месяц», «Неделя», «Список»), маркировка дней высокой нагрузки (N(d) >= 3) и экспорт в .ics."
              />
            }
          />
          <Route
            path="/subjects"
            element={
              <SectionPage
                title="Раздел «Предметы (Дисциплины)»"
                clause="п. 4.6.3"
                description="Каталог учебных дисциплин семестра с контактами преподавателей, шкалой прогресса и методическими материалами."
              />
            }
          />
          <Route
            path="/tasks"
            element={
              <SectionPage
                title="Раздел «Все задания» (Таблица и Канбан-доска)"
                clause="п. 4.6.4, 4.9.1"
                description="Перечень всех работ семестра с каскадным приоритетом дедлайнов (Персональный > Подгруппа > Общий) и фильтрацией."
              />
            }
          />
          <Route
            path="/tasks/:id"
            element={
              <SectionPage
                title="Карточка учебного задания"
                clause="п. 4.6.5, 4.2.5.2"
                description="Детальный просмотр задания, закреплённых вариантов («Студент — вариант»), загрузка отчёта и кнопка «Сообщить об ошибке»."
              />
            }
          />
          <Route
            path="/announcements"
            element={
              <SectionPage
                title="Раздел «Объявления старосты» (Announcement)"
                clause="п. 4.5.8, 4.6.8"
                description="Лента организационных и предметных объявлений старосты с закреплением, отметкой «Прочитано» и архивом."
              />
            }
          />
          <Route
            path="/analytics"
            element={
              <SectionPage
                title="Раздел «Старостат / Аналитика группы»"
                clause="п. 4.5.6–4.5.9, 4.6.7, 4.13"
                description="Матрица успеваемости группы, подтверждение статуса «Зачтено» старостой и выгрузка отчётов в XLSX/PDF."
              />
            }
          />
          <Route
            path="/profile"
            element={
              <SectionPage
                title="Личный кабинет студента"
                clause="п. 4.6.6, 4.10.3"
                description="Персональная статистика, текущие задолженности, настройки уведомлений и управление согласием на обработку ПДн (Закон РБ № 99-З)."
              />
            }
          />
          <Route
            path="/login"
            element={
              <SectionPage
                title="Вход в систему"
                clause="п. 4.2.1, 4.2.2"
                description="Авторизация по логину и паролю (JWT) со ступенчатой защитой от перебора (5 ошибок -> CAPTCHA, 10 ошибок -> блокировка на 15 минут)."
              />
            }
          />
          <Route
            path="/register/:inviteCode"
            element={
              <SectionPage
                title="Регистрация студента по инвайт-коду группы"
                clause="п. 4.2.1.1, 4.15.5"
                description="Самостоятельная регистрация студента по приглашению старосты с обязательным согласием на обработку персональных данных (Закон РБ № 99-З)."
              />
            }
          />
        </Routes>
      </main>
    </div>
  );
}
