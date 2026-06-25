import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bot,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Dumbbell,
  Laptop,
  Plus,
  RefreshCw,
  Save,
  Target,
  Trophy,
  type LucideIcon
} from "lucide-react";
import { addSet, createGoal, createWorkout, finishWorkout, getDashboard } from "./api";
import type { CoachStatus, Dashboard, Exercise, ExerciseStat, NextAction, Recommendation, Workout } from "./types";
import "./styles.css";

type Tab = "today" | "stats" | "coach" | "goals";

function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [tab, setTab] = useState<Tab>("today");
  const [workoutId, setWorkoutId] = useState<number | null>(null);
  const [selectedWorkoutType, setSelectedWorkoutType] = useState("A");
  const [activeExercise, setActiveExercise] = useState<Exercise | null>(null);
  const [status, setStatus] = useState("Загрузка");

  useEffect(() => {
    window.Telegram?.WebApp?.ready();
    window.Telegram?.WebApp?.expand();
    refresh();
  }, []);

  async function refresh() {
    try {
      const data = await getDashboard();
      setDashboard(data);
      setWorkoutId(data.today.current_workout_id || null);
      setSelectedWorkoutType(data.today.workout_type || "A");
      setStatus("");
    } catch {
      setStatus("Открой приложение из Telegram, чтобы пройти авторизацию.");
    }
  }

  const activePlan = useMemo(() => {
    if (!dashboard) return [];
    return dashboard.plans?.[selectedWorkoutType] || dashboard.today_plan;
  }, [dashboard, selectedWorkoutType]);

  const activeIndex = useMemo(() => {
    if (!dashboard || !activeExercise) return 0;
    const index = activePlan.findIndex((item) => item.exercise_id === activeExercise.exercise_id);
    return index >= 0 ? index : 0;
  }, [dashboard, activeExercise, activePlan]);

  async function startWorkout() {
    if (!dashboard) return;
    if (dashboard.today.current_workout_id) {
      setWorkoutId(dashboard.today.current_workout_id);
    } else {
      const created = await createWorkout({ workout_type: selectedWorkoutType, energy_level: "Normal" });
      setWorkoutId(created.workout.id);
    }
    setActiveExercise(activePlan[0] || null);
    setStatus("Тренировка начата");
  }

  function nextExercise() {
    if (!dashboard) return;
    const next = activePlan[activeIndex + 1];
    setActiveExercise(next || null);
    setStatus(next ? "Следующее упражнение" : "План завершён");
  }

  async function saveSet(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!workoutId || !activeExercise) return;
    const form = new FormData(event.currentTarget);
    const response = await addSet(workoutId, {
      exercise_name: activeExercise.name,
      set_index: Number(form.get("set_index") || 1),
      reps: Number(form.get("reps") || 0),
      weight: Number(form.get("weight") || 0),
      rir: Number(form.get("rir") || 0),
      pain_level: Number(form.get("pain_level") || 0),
      technique_ok: form.get("technique_ok") === "on",
      planned_sets: activeExercise.planned_sets,
      planned_reps: activeExercise.planned_reps
    });
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred("light");
    setStatus(response.set.recommendation || response.set.progression_status);
    event.currentTarget.reset();
  }

  async function finish() {
    if (!workoutId) return;
    await finishWorkout(workoutId, "Сохранено из Mini App");
    setWorkoutId(null);
    setActiveExercise(null);
    await refresh();
    setTab("coach");
  }

  async function saveGoal(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const name = String(form.get("name") || "").trim();
    if (!name) {
      setStatus("Назови цель");
      return;
    }
    await createGoal({
      name,
      category: String(form.get("category") || "").trim(),
      target: String(form.get("target") || "").trim(),
      current_result: String(form.get("current_result") || "").trim(),
    });
    event.currentTarget.reset();
    await refresh();
    setStatus("Цель добавлена");
  }

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">Training Bot</p>
          <h1>{dashboard?.user.first_name || "Тренировка"}</h1>
        </div>
        <button className="ghost icon-button" onClick={refresh} aria-label="Обновить" title="Обновить">
          <RefreshCw aria-hidden="true" />
        </button>
      </header>

      <nav className="tabs" aria-label="Разделы">
        <button className={tab === "today" ? "active" : ""} onClick={() => setTab("today")} aria-label="Сегодня" title="Сегодня"><CalendarDays aria-hidden="true" /></button>
        <button className={tab === "stats" ? "active" : ""} onClick={() => setTab("stats")} aria-label="Статы" title="Статы"><BarChart3 aria-hidden="true" /></button>
        <button className={tab === "coach" ? "active" : ""} onClick={() => setTab("coach")} aria-label="Коуч" title="Коуч"><Bot aria-hidden="true" /></button>
        <button className={tab === "goals" ? "active" : ""} onClick={() => setTab("goals")} aria-label="Цели" title="Цели"><Target aria-hidden="true" /></button>
      </nav>

      {status && <div className="status">{status}</div>}
      {tab === "today" && dashboard && (
        <TodayPanel
          dashboard={dashboard}
          plan={activePlan}
          selectedWorkoutType={selectedWorkoutType}
          onSelectWorkoutType={(type) => {
            if (workoutId) return;
            setSelectedWorkoutType(type);
            setActiveExercise(null);
          }}
          workoutId={workoutId}
          activeExercise={activeExercise}
          activeIndex={activeIndex}
          onStart={startWorkout}
          onSaveSet={saveSet}
          onNext={nextExercise}
          onFinish={finish}
        />
      )}
      {tab === "stats" && dashboard && <StatsPanel stats={dashboard.exercise_stats} workouts={dashboard.recent_workouts} />}
      {tab === "coach" && dashboard && <CoachPanel recommendations={dashboard.recommendations} actions={dashboard.next_actions} status={dashboard.coach_status} />}
      {tab === "goals" && dashboard && <GoalsPanel goals={dashboard.goals} onSaveGoal={saveGoal} />}
    </main>
  );
}

function TodayPanel({
  dashboard,
  plan,
  selectedWorkoutType,
  onSelectWorkoutType,
  workoutId,
  activeExercise,
  activeIndex,
  onStart,
  onSaveSet,
  onNext,
  onFinish
}: {
  dashboard: Dashboard;
  plan: Exercise[];
  selectedWorkoutType: string;
  onSelectWorkoutType: (type: string) => void;
  workoutId: number | null;
  activeExercise: Exercise | null;
  activeIndex: number;
  onStart: () => void;
  onSaveSet: (event: React.FormEvent<HTMLFormElement>) => void;
  onNext: () => void;
  onFinish: () => void;
}) {
  const progress = activeExercise ? Math.round(((activeIndex + 1) / plan.length) * 100) : 0;
  return (
    <section className="pane">
      <section className="hero-panel">
        <p className="eyebrow">{dashboard.weekly_summary.range_label}</p>
        <h2>{dashboard.today.headline}</h2>
        <div className="metrics">
          <Metric icon={Dumbbell} label="Тренировки" value={dashboard.weekly_summary.completed_workouts} />
          <Metric icon={Activity} label="Подходы" value={dashboard.weekly_summary.total_sets} />
          <Metric icon={AlertTriangle} label="Боль" value={dashboard.weekly_summary.pain_events} danger={dashboard.weekly_summary.pain_events > 0} />
        </div>
      </section>

      <ActionList actions={dashboard.next_actions} />

      {!workoutId && (
        <div className="workout-switch" aria-label="Выбор тренировки">
          {["A", "B"].map((type) => (
            <button
              key={type}
              className={selectedWorkoutType === type ? "active" : ""}
              onClick={() => onSelectWorkoutType(type)}
              type="button"
            >
              <Dumbbell aria-hidden="true" />
              <span>{type}</span>
            </button>
          ))}
        </div>
      )}

      {!activeExercise && (
        <button className="primary start-button" onClick={onStart}>
          <Dumbbell aria-hidden="true" />
          <span>{workoutId ? "Workout" : `Workout ${selectedWorkoutType}`}</span>
        </button>
      )}

      {activeExercise && (
        <article className="exercise">
          <div className="exercise-head">
            <div>
              <p className="eyebrow">{activeIndex + 1}/{plan.length} · {activeExercise.block}</p>
              <h2>{activeExercise.name}</h2>
            </div>
            <span className="progress-chip">{progress}%</span>
          </div>
          <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
          <div className="plan-line">
            <span>План: {activeExercise.planned_sets} x {activeExercise.planned_reps}</span>
            <span>Отдых: {activeExercise.rest_seconds} сек</span>
          </div>
          <form className="set-form" onSubmit={onSaveSet}>
            <label>Подход <input name="set_index" type="number" min="1" defaultValue="1" /></label>
            <label>Повторы <input name="reps" type="number" min="0" inputMode="numeric" /></label>
            <label>Вес, кг <input name="weight" type="number" min="0" step="0.5" inputMode="decimal" /></label>
            <label>RIR <input name="rir" type="number" min="0" max="5" defaultValue="2" /></label>
            <label>Боль 0-3 <input name="pain_level" type="number" min="0" max="3" defaultValue="0" /></label>
            <label className="check"><input name="technique_ok" type="checkbox" defaultChecked /> Техника чистая</label>
            <button className="primary" type="submit"><Save aria-hidden="true" /><span>Сохранить</span></button>
          </form>
          <div className="actions">
            <button onClick={onNext}><ChevronRight aria-hidden="true" /><span>Следующее</span></button>
            <button onClick={onFinish}><CheckCircle2 aria-hidden="true" /><span>Завершить</span></button>
          </div>
        </article>
      )}
    </section>
  );
}

function Metric({ icon: Icon, label, value, danger = false }: { icon: LucideIcon; label: string; value: number; danger?: boolean }) {
  return (
    <div className={danger ? "metric danger" : "metric"}>
      <div className="metric-top">
        <Icon aria-hidden="true" />
        <strong>{value}</strong>
      </div>
      <span>{label}</span>
    </div>
  );
}

function ActionList({ actions }: { actions: NextAction[] }) {
  if (!actions.length) return null;
  return (
    <section className="action-list">
      {actions.map((action) => (
        <article key={action.title} className={`action ${action.tone}`}>
          <h3>{action.title}</h3>
          <p>{action.body}</p>
        </article>
      ))}
    </section>
  );
}

function StatsPanel({ stats, workouts }: { stats: ExerciseStat[]; workouts: Workout[] }) {
  return (
    <section className="pane">
      <section className="section-head">
        <p className="eyebrow">Progress</p>
        <h2><BarChart3 aria-hidden="true" /> Упражнения</h2>
      </section>
      {stats.length ? (
        <section className="stat-list">
          {stats.map((stat) => <ExerciseStatCard key={stat.exercise_name} stat={stat} />)}
        </section>
      ) : (
        <section className="pane muted">Статистика появится после первых сохранённых подходов</section>
      )}
      <section className="section-head compact">
        <p className="eyebrow">History</p>
        <h2><Trophy aria-hidden="true" /> Последние тренировки</h2>
      </section>
      <section className="list">
        {workouts.length ? workouts.map((workout) => (
          <article key={workout.id} className="row">
            <h3>Workout {workout.workout_type} · {workout.status}</h3>
            <p>{workout.date}{workout.energy_level ? ` · ${workout.energy_level}` : ""}</p>
          </article>
        )) : <section className="pane muted">История пока пустая</section>}
      </section>
    </section>
  );
}

function ExerciseStatCard({ stat }: { stat: ExerciseStat }) {
  const risk = stat.pain_events > 0;
  const rirText = stat.average_rir === null || stat.average_rir === undefined ? "нет" : String(stat.average_rir);
  const bestText = bestResultText(stat);
  return (
    <article className={risk ? "stat-card risk" : "stat-card"}>
      <div className="stat-title">
        <h3>{stat.exercise_name}</h3>
        <span>{stat.trend_label}</span>
      </div>
      <p>{stat.latest_recommendation || "Копим данные для точной рекомендации."}</p>
      <div className="stat-grid">
        <small><b>{stat.sessions}</b> сессий</small>
        <small><b>{stat.total_sets}</b> подходов</small>
        <small><b>{rirText}</b> avg RIR</small>
        <small><b>{stat.pain_events}</b> pain</small>
      </div>
      <ProgressChart points={stat.recent_points} bestText={bestText} lastText={stat.last_result} />
      <div className="best-line">
        {stat.best_weight !== null && stat.best_weight !== undefined && <span>{stat.best_weight} кг</span>}
        {stat.best_reps !== null && stat.best_reps !== undefined && <span>{stat.best_reps} reps</span>}
        {stat.best_duration_seconds !== null && stat.best_duration_seconds !== undefined && <span>{stat.best_duration_seconds} сек</span>}
        <span>{stat.last_result}</span>
      </div>
    </article>
  );
}

function bestResultText(stat: ExerciseStat): string {
  const parts = [];
  if (stat.best_weight !== null && stat.best_weight !== undefined) parts.push(`${stat.best_weight} кг`);
  if (stat.best_reps !== null && stat.best_reps !== undefined) parts.push(`${stat.best_reps} reps`);
  if (stat.best_duration_seconds !== null && stat.best_duration_seconds !== undefined) parts.push(`${stat.best_duration_seconds} сек`);
  return parts.length ? parts.join(" · ") : stat.last_result;
}

function ProgressChart({
  points = [],
  bestText,
  lastText
}: {
  points?: ExerciseStat["recent_points"];
  bestText: string;
  lastText: string;
}) {
  if (!points.length) {
    return (
      <div className="chart-empty">
        <span>Точек для графика пока мало</span>
      </div>
    );
  }
  const max = Math.max(...points.map((point) => point.value), 1);
  const first = points[0];
  const last = points[points.length - 1];
  return (
    <div className="progress-chart" aria-label="Диаграмма прогресса">
      <div className="chart-summary">
        <span><b>Сейчас</b>{lastText || last.label}</span>
        <span><b>Лучшее</b>{bestText}</span>
      </div>
      <div className="chart-area">
        <div className="chart-grid" aria-hidden="true" />
        <div className="chart-bars">
          {points.map((point, index) => (
            <span
              key={`${point.date}-${point.label}-${index}`}
              title={`${point.date}: ${point.label}`}
              style={{ height: `${Math.max(16, Math.round((point.value / max) * 100))}%` }}
            >
              <i>{point.label}</i>
            </span>
          ))}
        </div>
      </div>
      <div className="chart-axis">
        <span>{first.date}</span>
        <span>{last.date}</span>
      </div>
    </div>
  );
}

function CoachPanel({
  recommendations,
  actions,
  status
}: {
  recommendations: Recommendation[];
  actions: NextAction[];
  status?: CoachStatus;
}) {
  return (
    <section className="pane">
      <section className="section-head">
        <p className="eyebrow">Coach</p>
        <h2><Bot aria-hidden="true" /> Рекомендации</h2>
      </section>
      <CoachStatusCard status={status} />
      <ActionList actions={actions} />
      <section className="list">
        {recommendations.length ? recommendations.map((item) => (
          <article key={item.id} className={`row ${item.priority === "high" ? "risk" : ""}`}>
            <div className="stat-title">
              <h3>{item.title}</h3>
              <span>{item.source}</span>
            </div>
            <p>{item.body}</p>
          </article>
        )) : <section className="pane muted">Рекомендации появятся после тренировки</section>}
      </section>
    </section>
  );
}

function CoachStatusCard({ status }: { status?: CoachStatus }) {
  const label = status?.label || "Локальный AI подключается через worker на твоём ПК";
  const detail = status?.latest_ai_at
    ? `Последний AI-разбор: ${new Date(status.latest_ai_at).toLocaleDateString()}`
    : "Backend работает и без AI. Разборы появятся, когда включён Ollama worker.";
  const tone = status?.state === "waiting_for_worker" ? "waiting" : status?.state === "ready" ? "ready" : "idle";
  return (
    <article className={`coach-status ${tone}`}>
      <div>
        <p className="eyebrow">Local AI</p>
        <h3><Laptop aria-hidden="true" /> {label}</h3>
        <p>{detail}</p>
      </div>
      {status?.pending_analysis_count ? <strong>{status.pending_analysis_count}</strong> : null}
    </article>
  );
}

function GoalsPanel({
  goals,
  onSaveGoal
}: {
  goals: Array<Record<string, unknown>>;
  onSaveGoal: (event: React.FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <section className="pane">
      <section className="section-head">
        <p className="eyebrow">Targets</p>
        <h2><Target aria-hidden="true" /> Цели</h2>
      </section>
      <form className="goal-form" onSubmit={onSaveGoal}>
        <label>Цель <input name="name" placeholder="Подтягивания" required /></label>
        <label>Категория <input name="category" placeholder="Strength" /></label>
        <label>Сейчас <input name="current_result" placeholder="+5kg x 6" /></label>
        <label>Хочу <input name="target" placeholder="+10kg x 6" /></label>
        <button className="primary" type="submit"><Plus aria-hidden="true" /><span>Добавить</span></button>
      </form>
      <section className="list">
        {goals.length ? goals.map((goal) => (
          <article key={String(goal.id)} className="row">
            <h3>{String(goal.name || "Цель")}</h3>
            <p>{String(goal.current_result || "Текущий результат не записан")} → {String(goal.target || "")}</p>
          </article>
        )) : <section className="pane muted">Цели пока не добавлены</section>}
      </section>
    </section>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
