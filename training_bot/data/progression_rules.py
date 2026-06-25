from __future__ import annotations


BASELINE_MAXES = {
    "strict_pullups": {
        "label": "Максимум строгих подтягиваний",
        "value": 15,
        "unit": "reps",
        "date": "2026-06-16",
    },
    "strict_dips": {
        "label": "Максимум чистых отжиманий на брусьях",
        "value": 21,
        "unit": "reps",
        "date": "2026-06-16",
    },
    "elevated_pike_pushup": {
        "label": "Максимум elevated pike push-up",
        "value": 11,
        "unit": "reps",
        "height_cm": 51,
        "date": "2026-06-16",
    },
    "chest_to_wall_handstand": {
        "label": "Стойка лицом к стене",
        "value": 40,
        "unit": "sec",
        "date": "2026-06-16",
    },
}


EXERCISE_ALIASES = {
    "chest_to_wall_handstand": [
        "Стойка лицом к стене",
        "Стойка на руках у стены",
    ],
    "elevated_pike_pushup": [
        "Pike Push Up",
        "Elevated Pike Push Up",
        "отжимания с ногами",
    ],
    "hspu_progression": ["HSPU Progression", "HSPU"],
    "pullup": ["Подтягивания", "Подтягивания или верхний блок"],
    "dip": ["Брусья", "Брусья с наклоном вперёд"],
    "romanian_deadlift": ["Румынская тяга"],
    "bulgarian_split_squat": ["Болгарские выпады"],
    "hanging_straight_leg_raise": [
        "Подъём коленей или ног в висе",
        "Подъём прямых ног в висе",
    ],
    "cable_face_pull": ["Face Pull / задняя дельта", "Face Pull"],
    "hollow_body_hold": ["Hollow Body Hold"],
    "scapular_handstand_shrugs": ["Лопаточные подъёмы в стойке"],
}


PROGRESSION_RULES = {
    "global": {
        "load_increase_upper_body_percent_max": 7.5,
        "load_increase_lower_body_percent_max": 10,
        "load_increase_machine_percent_max": 10,
        "required_successful_exposures": 2,
        "min_rir_for_progression": 2,
        "pain_blocks_progression": True,
        "technique_issue_blocks_progression": True,
    },
    "chest_to_wall_handstand": {
        "next_target": "3×20–30 секунд, отдых 90 секунд, 0 падений, контролируемый выход",
        "progression_lock_reason": "Боль в кистях и падения блокируют усложнение стойки.",
        "unlock_condition": "2 тренировки подряд без боли, без падений и с контролируемым выходом",
    },
    "elevated_pike_pushup": {
        "next_target": "51 см, 4×6–8, отдых 150 секунд",
        "increase_condition": "4×8 два раза подряд, RIR >= 2, техника чистая, боли нет",
        "next_progression": "Поднять ноги на 5–10 см или добавить дефицит 2–5 см, но не оба сразу",
    },
    "hspu_progression": {
        "levels": [
            "Pike Push Up с пола",
            "Elevated Pike Push Up",
            "Deficit Elevated Pike Push Up",
            "Partial Wall HSPU",
            "Negative Wall HSPU 3–5 секунд",
            "Full Wall HSPU",
        ],
        "unlock_condition": "2 тренировки подряд со стойкой без боли, без падений и с контролируемым выходом",
    },
    "pullup": {
        "next_target": "+2.5 кг 4×4–6, отдых 180 секунд; если веса нет — собственный вес 4×6",
        "increase_condition": "4×6 два раза подряд с тем же весом, RIR >= 2",
        "max_test_note": "Тест максимума не влияет на рабочую прогрессию.",
    },
    "dip": {
        "next_target": "Собственный вес 3×8–10, отдых 150 секунд, одинаковая глубина",
        "increase_condition": "3×10 два раза подряд, RIR >= 2, техника чистая, боли нет",
        "strict_max": 21,
    },
    "romanian_deadlift": {
        "next_target": "30 кг 3×8–10, отдых 150 секунд, записать RIR",
        "increase_condition": "30 кг 3×10 два раза подряд, RIR >= 2, спина нейтральная",
        "next_load": "32.5 кг",
    },
    "bulgarian_split_squat": {
        "next_target": "12 кг общего веса, 3×10–12 на ногу, записать RIR",
        "increase_condition": "3×12 два раза подряд, RIR >= 2, баланс стабильный",
        "next_load": "14 кг общего веса",
    },
    "hanging_straight_leg_raise": {
        "next_target": "3×8–10, отдых 90 секунд, без раскачивания",
        "increase_condition": "3×10 два раза подряд, RIR/запас >= 2, чистая техника",
    },
    "cable_face_pull": {
        "next_target": "10 кг 2×12–15 одинаковым весом",
        "increase_condition": "2×20 два раза подряд с тем же весом, RIR >= 2",
    },
    "hollow_body_hold": {
        "next_target": "2×20 секунд; не превращать разминку в тяжёлое упражнение",
        "increase_condition": "2×20 два раза подряд с запасом 10+ секунд и прижатой поясницей",
    },
}


RECOMMENDATION_MESSAGES = {
    "increase": "Можно повышать нагрузку, если это уже второе подряд сопоставимое успешное занятие.",
    "keep": "Вес или сложность пока оставляем.",
    "decrease": "Нагрузку стоит снизить или упростить вариант.",
    "pain_stop": "Остановись из-за боли. Прогрессию сегодня блокируем.",
    "safe_stop": "Ты правильно остановил подход при потере контроля. Это не провал.",
    "max_test": "Максимальный тест сохранён, но не влияет на рабочую прогрессию.",
    "rest_increase": "В следующий раз можно добавить 30 секунд отдыха.",
}
