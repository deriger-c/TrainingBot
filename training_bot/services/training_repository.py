from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from data.exercise_program import get_workout
from db.models import CoachNote, ExerciseSet, Goal, PainEvent, Recommendation, User, WorkoutSession
from services.progression_rules_service import enrich_result_with_decision


async def get_or_create_user(
    db: AsyncSession,
    *,
    telegram_id: int,
    username: str = "",
    first_name: str = "",
    last_name: str = "",
    timezone: str = "Asia/Jerusalem",
) -> User:
    user = await db.scalar(select(User).where(User.telegram_id == telegram_id))
    if user:
        user.username = username or user.username
        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        await db.commit()
        await db.refresh(user)
        return user
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        timezone=timezone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def dashboard(db: AsyncSession, user: User) -> dict:
    workouts = (
        await db.scalars(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user.id)
            .order_by(desc(WorkoutSession.workout_date), desc(WorkoutSession.id))
            .limit(8)
        )
    ).all()
    recommendations = (
        await db.scalars(
            select(Recommendation)
            .where(Recommendation.user_id == user.id)
            .order_by(desc(Recommendation.generated_at), desc(Recommendation.id))
            .limit(5)
        )
    ).all()
    goals = (
        await db.scalars(
            select(Goal)
            .where(Goal.user_id == user.id, Goal.status == "active")
            .order_by(desc(Goal.updated_at))
            .limit(6)
        )
    ).all()
    exercise_stats = await _exercise_stats(db, user)
    weekly_summary = await _weekly_summary(db, user)
    next_workout_type = _next_workout_type(workouts)
    current_workout = next((workout for workout in workouts if workout.status == "started"), None)
    return {
        "user": {"telegram_id": user.telegram_id, "first_name": user.first_name, "timezone": user.timezone},
        "today": {
            "workout_type": current_workout.workout_type if current_workout else next_workout_type,
            "current_workout_id": current_workout.id if current_workout else None,
            "current_status": current_workout.status if current_workout else "ready",
            "headline": "Продолжить тренировку" if current_workout else f"Сегодня: Workout {next_workout_type}",
        },
        "today_plan": [_exercise_payload(exercise) for exercise in get_workout(current_workout.workout_type if current_workout else next_workout_type)],
        "recent_workouts": [_workout_payload(workout) for workout in workouts],
        "recommendations": [_recommendation_payload(item) for item in recommendations],
        "goals": [_goal_payload(goal) for goal in goals],
        "weekly_summary": weekly_summary,
        "exercise_stats": exercise_stats,
        "next_actions": _next_actions(current_workout, next_workout_type, recommendations, weekly_summary),
    }


async def create_workout(db: AsyncSession, user: User, payload: dict) -> WorkoutSession:
    session_id = payload.get("session_id") or f"api-{date.today().isoformat()}-{uuid4().hex[:8]}"
    workout = WorkoutSession(
        session_id=session_id,
        user_id=user.id,
        workout_date=date.fromisoformat(payload.get("date") or date.today().isoformat()),
        workout_type=payload.get("workout_type", "A"),
        start_time=payload.get("start_time", ""),
        body_weight=payload.get("body_weight"),
        sleep_hours=payload.get("sleep_hours"),
        energy_level=payload.get("energy_level", ""),
        status="started",
    )
    db.add(workout)
    await db.commit()
    await db.refresh(workout)
    return workout


async def add_set(db: AsyncSession, user: User, workout_id: int, payload: dict) -> ExerciseSet:
    workout = await db.scalar(select(WorkoutSession).where(WorkoutSession.id == workout_id, WorkoutSession.user_id == user.id))
    if not workout:
        raise ValueError("Workout not found")
    result = enrich_result_with_decision(
        {
            "exercise_name": payload["exercise_name"],
            "actual_result": payload.get("raw_result") or _raw_result_from_set(payload),
            "planned_sets": payload.get("planned_sets", ""),
            "planned_reps": payload.get("planned_reps", ""),
            "pain_level": payload.get("pain_level", 0),
            "rir": payload.get("rir"),
            "technique_ok": payload.get("technique_ok", True),
            "status": "completed",
        }
    )
    item = ExerciseSet(
        workout_id=workout.id,
        exercise_name=payload["exercise_name"],
        set_index=payload.get("set_index", 1),
        reps=payload.get("reps"),
        weight=payload.get("weight"),
        duration_seconds=payload.get("duration_seconds"),
        rir=payload.get("rir"),
        pain_level=payload.get("pain_level", 0),
        technique_ok=payload.get("technique_ok", True),
        raw_result=result["actual_result"],
        progression_status=result.get("progression_status", ""),
        recommendation=result.get("recommendation", ""),
    )
    db.add(item)
    if item.pain_level > 0:
        db.add(
            PainEvent(
                user_id=user.id,
                workout_id=workout.id,
                exercise_name=item.exercise_name,
                pain_level=item.pain_level,
                notes=item.raw_result,
            )
        )
    await db.commit()
    await db.refresh(item)
    return item


async def finish_workout(db: AsyncSession, user: User, workout_id: int, notes: str = "") -> WorkoutSession:
    workout = await db.scalar(select(WorkoutSession).where(WorkoutSession.id == workout_id, WorkoutSession.user_id == user.id))
    if not workout:
        raise ValueError("Workout not found")
    workout.status = "completed"
    workout.general_notes = notes or workout.general_notes
    await db.commit()
    await db.refresh(workout)
    await create_rule_recommendation(db, user, workout)
    return workout


async def create_goal(db: AsyncSession, user: User, payload: dict) -> Goal:
    goal = Goal(
        user_id=user.id,
        name=payload["name"].strip(),
        category=payload.get("category", "").strip(),
        target=payload.get("target", "").strip(),
        current_result=payload.get("current_result", "").strip(),
        notes=payload.get("notes", "").strip(),
        status="active",
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


async def create_rule_recommendation(db: AsyncSession, user: User, workout: WorkoutSession) -> Recommendation:
    pain_count = await db.scalar(
        select(func.count(PainEvent.id)).where(PainEvent.user_id == user.id, PainEvent.workout_id == workout.id)
    )
    title = "Следующая тренировка"
    body = "Повтори уровень. Повышай нагрузку только после чистых подходов с RIR 2+ и pain=0."
    priority = "normal"
    if pain_count:
        title = "Прогрессия заблокирована из-за боли"
        body = "На следующей тренировке не повышай нагрузку в упражнениях, где была боль. Сначала добейся pain=0."
        priority = "high"
    rec = Recommendation(
        user_id=user.id,
        workout_id=workout.id,
        status="new",
        priority=priority,
        title=title,
        body=body,
        source="rules",
        generated_at=datetime.utcnow(),
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


async def pending_workouts_for_ai(db: AsyncSession, limit: int = 5) -> list[dict]:
    workouts = (
        await db.scalars(
            select(WorkoutSession)
            .where(WorkoutSession.status == "completed")
            .order_by(desc(WorkoutSession.updated_at))
            .limit(limit)
        )
    ).all()
    items = []
    for workout in workouts:
        existing = await db.scalar(
            select(Recommendation).where(
                Recommendation.workout_id == workout.id,
                Recommendation.source == "ollama",
            )
        )
        if existing:
            continue
        sets = (
            await db.scalars(
                select(ExerciseSet).where(ExerciseSet.workout_id == workout.id).order_by(ExerciseSet.set_index)
            )
        ).all()
        items.append({"workout": _workout_payload(workout), "sets": [_set_payload(item) for item in sets]})
    return items


async def save_ai_recommendation(db: AsyncSession, payload: dict) -> Recommendation:
    workout = await db.get(WorkoutSession, int(payload["workout_id"]))
    if not workout:
        raise ValueError("Workout not found")
    rec = Recommendation(
        user_id=workout.user_id,
        workout_id=workout.id,
        status="new",
        priority=payload.get("priority", "normal"),
        title=payload.get("title", "AI-разбор тренировки"),
        body=payload.get("body", ""),
        source="ollama",
        generated_at=datetime.utcnow(),
    )
    db.add(rec)
    note = CoachNote(
        user_id=workout.user_id,
        source="ollama",
        title=rec.title,
        body=rec.body,
        tags=["ai", "workout"],
    )
    db.add(note)
    await db.commit()
    await db.refresh(rec)
    return rec


def _raw_result_from_set(payload: dict) -> str:
    if payload.get("duration_seconds") is not None:
        return f"{payload['duration_seconds']} sec"
    reps = payload.get("reps", "")
    weight = payload.get("weight")
    if weight is None:
        return str(reps)
    return f"{weight}kg {reps}"


async def _weekly_summary(db: AsyncSession, user: User) -> dict:
    since = date.today() - timedelta(days=6)
    completed_workouts = await db.scalar(
        select(func.count(WorkoutSession.id)).where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.status == "completed",
            WorkoutSession.workout_date >= since,
        )
    )
    total_sets = await db.scalar(
        select(func.count(ExerciseSet.id))
        .join(WorkoutSession, ExerciseSet.workout_id == WorkoutSession.id)
        .where(WorkoutSession.user_id == user.id, WorkoutSession.workout_date >= since)
    )
    pain_events = await db.scalar(
        select(func.count(PainEvent.id)).where(PainEvent.user_id == user.id, PainEvent.created_at >= datetime.combine(since, datetime.min.time()))
    )
    return {
        "completed_workouts": int(completed_workouts or 0),
        "total_sets": int(total_sets or 0),
        "pain_events": int(pain_events or 0),
        "range_label": "7 дней",
    }


async def _exercise_stats(db: AsyncSession, user: User, limit: int = 240) -> list[dict]:
    rows = (
        await db.execute(
            select(ExerciseSet, WorkoutSession)
            .join(WorkoutSession, ExerciseSet.workout_id == WorkoutSession.id)
            .where(WorkoutSession.user_id == user.id)
            .order_by(desc(WorkoutSession.workout_date), desc(ExerciseSet.id))
            .limit(limit)
        )
    ).all()
    grouped: dict[str, dict] = {}
    for item, workout in rows:
        stat = grouped.setdefault(
            item.exercise_name,
            {
                "exercise_name": item.exercise_name,
                "sessions": set(),
                "total_sets": 0,
                "last_date": workout.workout_date.isoformat(),
                "last_result": item.raw_result,
                "best_weight": None,
                "best_reps": None,
                "best_duration_seconds": None,
                "rir_values": [],
                "pain_events": 0,
                "latest_status": item.progression_status,
                "latest_recommendation": item.recommendation,
                "recent_points": [],
            },
        )
        stat["sessions"].add(workout.id)
        stat["total_sets"] += 1
        if item.weight is not None:
            stat["best_weight"] = max(stat["best_weight"] or item.weight, item.weight)
        if item.reps is not None:
            stat["best_reps"] = max(stat["best_reps"] or item.reps, item.reps)
        if item.duration_seconds is not None:
            stat["best_duration_seconds"] = max(stat["best_duration_seconds"] or item.duration_seconds, item.duration_seconds)
        if item.rir is not None:
            stat["rir_values"].append(item.rir)
        if item.pain_level > 0:
            stat["pain_events"] += 1
        point_value = _chart_point_value(item)
        if point_value is not None and len(stat["recent_points"]) < 8:
            stat["recent_points"].append(
                {
                    "date": workout.workout_date.isoformat(),
                    "value": point_value,
                    "label": _chart_point_label(item),
                }
            )

    payloads = []
    for stat in grouped.values():
        rir_values = stat.pop("rir_values")
        sessions = stat.pop("sessions")
        stat["sessions"] = len(sessions)
        stat["average_rir"] = round(sum(rir_values) / len(rir_values), 1) if rir_values else None
        stat["trend_label"] = _trend_label(stat["latest_status"], stat["pain_events"])
        stat["recent_points"].reverse()
        payloads.append(stat)
    return sorted(payloads, key=lambda item: (item["pain_events"], item["total_sets"]), reverse=True)[:12]


def _next_workout_type(workouts: list[WorkoutSession]) -> str:
    for workout in workouts:
        if workout.status == "started":
            return workout.workout_type or "A"
    for workout in workouts:
        if workout.status == "completed":
            return "B" if workout.workout_type == "A" else "A"
    return "A"


def _next_actions(
    current_workout: WorkoutSession | None,
    next_workout_type: str,
    recommendations: list[Recommendation],
    weekly_summary: dict,
) -> list[dict]:
    if current_workout:
        return [
            {
                "title": "Продолжить начатую тренировку",
                "body": f"Workout {current_workout.workout_type}. Дозапиши подходы и заверши сессию.",
                "tone": "primary",
            }
        ]
    actions = [
        {
            "title": f"Открыть Workout {next_workout_type}",
            "body": "Иди по плану сверху вниз. После каждого подхода записывай вес, повторы, RIR, боль и технику.",
            "tone": "primary",
        }
    ]
    important = next((item for item in recommendations if item.priority == "high"), None)
    if important:
        actions.append({"title": important.title, "body": important.body, "tone": "danger"})
    elif weekly_summary["pain_events"]:
        actions.append(
            {
                "title": "Следи за болью",
                "body": "На этой неделе были pain-события. Сегодня не повышай нагрузку в проблемных движениях.",
                "tone": "danger",
            }
        )
    else:
        actions.append(
            {
                "title": "Правило прогрессии",
                "body": "Повышай вес только после чистого выполнения верхней границы плана с RIR 2+ и pain=0.",
                "tone": "calm",
            }
        )
    return actions


def _trend_label(status: str, pain_events: int) -> str:
    if pain_events:
        return "Сначала без боли"
    if status == "comparable_success":
        return "Близко к повышению"
    if status == "keep_same":
        return "Держим уровень"
    if status == "technique_issue":
        return "Чистим технику"
    if status == "pain_stop":
        return "Прогрессия закрыта"
    return "Копим данные"


def _chart_point_value(item: ExerciseSet) -> float | None:
    if item.weight is not None and item.reps is not None:
        return round(float(item.weight) * float(item.reps), 2)
    if item.reps is not None:
        return float(item.reps)
    if item.duration_seconds is not None:
        return float(item.duration_seconds)
    return None


def _chart_point_label(item: ExerciseSet) -> str:
    if item.weight is not None and item.reps is not None:
        return f"{item.weight:g}kg x {item.reps}"
    if item.reps is not None:
        return f"{item.reps} reps"
    if item.duration_seconds is not None:
        return f"{item.duration_seconds} sec"
    return item.raw_result


def _exercise_payload(exercise) -> dict:
    return {
        "exercise_id": exercise.exercise_id,
        "name": exercise.name,
        "block": exercise.block,
        "planned_sets": exercise.planned_sets,
        "planned_reps": exercise.planned_reps,
        "rest_seconds": exercise.rest_seconds,
        "input_example": exercise.input_example,
    }


def _workout_payload(workout: WorkoutSession) -> dict:
    return {
        "id": workout.id,
        "session_id": workout.session_id,
        "date": workout.workout_date.isoformat(),
        "workout_type": workout.workout_type,
        "status": workout.status,
        "body_weight": workout.body_weight,
        "sleep_hours": workout.sleep_hours,
        "energy_level": workout.energy_level,
        "notes": workout.general_notes,
    }


def _set_payload(item: ExerciseSet) -> dict:
    return {
        "id": item.id,
        "exercise_name": item.exercise_name,
        "set_index": item.set_index,
        "reps": item.reps,
        "weight": item.weight,
        "rir": item.rir,
        "pain_level": item.pain_level,
        "technique_ok": item.technique_ok,
        "raw_result": item.raw_result,
        "progression_status": item.progression_status,
        "recommendation": item.recommendation,
    }


def _recommendation_payload(item: Recommendation) -> dict:
    return {
        "id": item.id,
        "priority": item.priority,
        "title": item.title,
        "body": item.body,
        "source": item.source,
        "generated_at": item.generated_at.isoformat(),
    }


def _goal_payload(goal: Goal) -> dict:
    return {"id": goal.id, "name": goal.name, "target": goal.target, "current_result": goal.current_result}
