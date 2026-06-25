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

export type Dashboard = {
  user: { telegram_id: number; first_name: string; timezone: string };
  today_plan: Exercise[];
  recent_workouts: Workout[];
  recommendations: Recommendation[];
  goals: Goal[];
};
