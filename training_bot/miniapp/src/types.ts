export type Exercise = {
  exercise_id: string;
  name: string;
  block: string;
  planned_sets: string;
  planned_reps: string;
  rest_seconds: number;
  input_example: string;
};

export type Workout = {
  id: number;
  session_id: string;
  date: string;
  workout_type: string;
  status: string;
  body_weight?: number;
  sleep_hours?: number;
  energy_level?: string;
  notes?: string;
};

export type Recommendation = {
  id: number;
  priority: string;
  title: string;
  body: string;
  source: string;
  generated_at: string;
};

export type Goal = {
  id: number;
  name: string;
  target: string;
  current_result: string;
};

export type TodayState = {
  workout_type: string;
  current_workout_id?: number | null;
  current_status: string;
  headline: string;
};

export type WeeklySummary = {
  completed_workouts: number;
  total_sets: number;
  pain_events: number;
  range_label: string;
};

export type ExerciseStat = {
  exercise_name: string;
  sessions: number;
  total_sets: number;
  last_date: string;
  last_result: string;
  best_weight?: number | null;
  best_reps?: number | null;
  best_duration_seconds?: number | null;
  average_rir?: number | null;
  pain_events: number;
  latest_status: string;
  latest_recommendation: string;
  trend_label: string;
  recent_points: Array<{ date: string; value: number; label: string }>;
};

export type NextAction = {
  title: string;
  body: string;
  tone: "primary" | "calm" | "danger";
};

export type Dashboard = {
  user: { telegram_id: number; first_name: string; timezone: string };
  today: TodayState;
  today_plan: Exercise[];
  recent_workouts: Workout[];
  recommendations: Recommendation[];
  goals: Goal[];
  weekly_summary: WeeklySummary;
  exercise_stats: ExerciseStat[];
  next_actions: NextAction[];
};
