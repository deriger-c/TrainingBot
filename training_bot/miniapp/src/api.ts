import type { Dashboard } from "./types";

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData: string;
        ready: () => void;
        expand: () => void;
        HapticFeedback?: { impactOccurred: (style: "light" | "medium" | "heavy") => void };
      };
    };
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

function initData(): string {
  return window.Telegram?.WebApp?.initData || "";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData(),
      ...(options.headers || {})
    }
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function getDashboard(): Promise<Dashboard> {
  return request<Dashboard>("/api/miniapp/dashboard");
}

export async function createWorkout(input: {
  workout_type: string;
  body_weight?: number;
  sleep_hours?: number;
  energy_level?: string;
}) {
  return request<{ ok: boolean; workout: { id: number } }>("/api/miniapp/workouts", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function addSet(workoutId: number, input: {
  exercise_name: string;
  set_index: number;
  reps?: number;
  weight?: number;
  rir?: number;
  pain_level: number;
  technique_ok: boolean;
  planned_sets: string;
  planned_reps: string;
}) {
  return request<{ ok: boolean; set: { recommendation: string; progression_status: string } }>(
    `/api/miniapp/workouts/${workoutId}/sets`,
    { method: "POST", body: JSON.stringify(input) }
  );
}

export async function finishWorkout(workoutId: number, notes: string) {
  return request(`/api/miniapp/workouts/${workoutId}/finish`, {
    method: "POST",
    body: JSON.stringify({ notes })
  });
}
