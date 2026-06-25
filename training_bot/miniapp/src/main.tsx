import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { addSet, createWorkout, finishWorkout, getDashboard } from "./api";
import type { Dashboard, Exercise } from "./types";
import "./styles.css";

type Tab = "train" | "history" | "coach" | "goals";

function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [tab, setTab] = useState<Tab>("train");
  const [workoutId, setWorkoutId] = useState<number | null>(null);
  const [activeExercise, setActiveExercise] = useState<Exercise | null>(null);
  const [status, setStatus] = useState("Загрузка");

  useEffect(() => {
    window.Telegram?.WebApp?.ready();
    window.Telegram?.WebApp?.expand();
    refresh();
  }, []);

  async function refresh() {
    try {
      setDashboard(await getDashboard());
      setStatus("");
    } catch {
      setStatus("Открой приложение из Telegram, чтобы пройти авторизацию.");
    }
  }

  async function startWorkout() {
    const created = await createWorkout({ workout_type: "A", energy_level: "Normal" });
    setWorkoutId(created.workout.id);
    setActiveExercise(dashboard?.today_plan[0] || null);
    setStatus("Тренировка начата");
  }

  const activeIndex = useMemo(() => {
    if (!dashboard || !activeExercise) return 0;
    return dashboard.today_plan.findIndex((item) => item.exercise_id === activeExercise.exercise_id);
  }, [dashboard, activeExercise]);

  function nextExercise() {
    if (!dashboard) return;
    const next = dashboard.today_plan[activeIndex + 1];
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

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">Training Bot</p>
          <h1>{dashboard?.user.first_name || "Тренировка"}</h1>
        </div>
        <button className="ghost" onClick={refresh}>Обновить</button>
      </header>

      <nav className="tabs" aria-label="Разделы">
        <button className={tab === "train" ? "active" : ""} onClick={() => setTab("train")}>Сегодня</button>
        <button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")}>История</button>
        <button className={tab === "coach" ? "active" : ""} onClick={() => setTab("coach")}>Коуч</button>
        <button className={tab === "goals" ? "active" : ""} onClick={() => setTab("goals")}>Цели</button>
      </nav>

      {status && <div className="status">{status}</div>}
      {tab === "train" && dashboard && (
        <section className="pane">
          {!workoutId && <button className="primary" onClick={startWorkout}>Начать Workout A</button>}
          {activeExercise && (
            <article className="exercise">
              <p className="eyebrow">{activeIndex + 1}/{dashboard.today_plan.length} · {activeExercise.block}</p>
              <h2>{activeExercise.name}</h2>
              <p>План: {activeExercise.planned_sets} x {activeExercise.planned_reps}</p>
              <p>Отдых: {activeExercise.rest_seconds} сек</p>
              <form className="set-form" onSubmit={saveSet}>
                <label>Подход <input name="set_index" type="number" min="1" defaultValue="1" /></label>
                <label>Повторы <input name="reps" type="number" min="0" inputMode="numeric" /></label>
                <label>Вес, кг <input name="weight" type="number" min="0" step="0.5" inputMode="decimal" /></label>
                <label>RIR <input name="rir" type="number" min="0" max="5" defaultValue="2" /></label>
                <label>Боль 0-3 <input name="pain_level" type="number" min="0" max="3" defaultValue="0" /></label>
                <label className="check"><input name="technique_ok" type="checkbox" defaultChecked /> Техника чистая</label>
                <button className="primary" type="submit">Сохранить подход</button>
              </form>
              <div className="actions">
                <button onClick={nextExercise}>Следующее</button>
                <button onClick={finish}>Завершить</button>
              </div>
            </article>
          )}
        </section>
      )}

      {tab === "history" && <List items={dashboard?.recent_workouts || []} empty="История пока пустая" />}
      {tab === "coach" && <List items={dashboard?.recommendations || []} empty="Рекомендации появятся после тренировки" />}
      {tab === "goals" && <List items={dashboard?.goals || []} empty="Цели пока не добавлены" />}
    </main>
  );
}

function List({ items, empty }: { items: Array<Record<string, unknown>>; empty: string }) {
  if (!items.length) return <section className="pane muted">{empty}</section>;
  return (
    <section className="pane list">
      {items.map((item) => (
        <article key={String(item.id)} className="row">
          <h3>{String(item.title || item.name || item.workout_type || "Запись")}</h3>
          <p>{String(item.body || item.target || item.date || item.current_result || "")}</p>
        </article>
      ))}
    </section>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
