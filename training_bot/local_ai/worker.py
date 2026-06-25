from __future__ import annotations

import argparse
import asyncio
import logging

import httpx

from config import load_config

logger = logging.getLogger(__name__)


def build_prompt(item: dict) -> str:
    workout = item["workout"]
    sets = item.get("sets", [])
    lines = [
        "Ты осторожный тренер по силовым тренировкам.",
        "Нельзя советовать повышение нагрузки, если правила или данные показывают боль, плохую технику или низкий запас.",
        "Дай короткий разбор на русском: 1) что хорошо, 2) что рискованно, 3) что сделать на следующей тренировке.",
        "",
        f"Тренировка: {workout.get('workout_type')} от {workout.get('date')}",
        f"Вес: {workout.get('body_weight')}, сон: {workout.get('sleep_hours')}, энергия: {workout.get('energy_level')}",
        "Подходы:",
    ]
    for item_set in sets:
        lines.append(
            "- {exercise}: result={result}, rir={rir}, pain={pain}, technique_ok={technique}, rule={rule}, rule_rec={rec}".format(
                exercise=item_set.get("exercise_name"),
                result=item_set.get("raw_result"),
                rir=item_set.get("rir"),
                pain=item_set.get("pain_level"),
                technique=item_set.get("technique_ok"),
                rule=item_set.get("progression_status"),
                rec=item_set.get("recommendation"),
            )
        )
    return "\n".join(lines)


async def ask_ollama(client: httpx.AsyncClient, base_url: str, model: str, prompt: str) -> str:
    response = await client.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "").strip()


async def run_once() -> int:
    config = load_config()
    if not config.public_base_url:
        raise RuntimeError("PUBLIC_BASE_URL is required for local AI worker")
    if not config.worker_token:
        raise RuntimeError("WORKER_TOKEN is required for local AI worker")

    headers = {"X-Worker-Token": config.worker_token}
    async with httpx.AsyncClient(headers=headers) as client:
        pending = await client.get(f"{config.public_base_url}/api/coach/pending", timeout=30)
        pending.raise_for_status()
        items = pending.json().get("items", [])
        saved = 0
        for item in items:
            try:
                body = await ask_ollama(client, config.ollama_base_url, config.ollama_model, build_prompt(item))
            except (httpx.HTTPError, TimeoutError) as exc:
                logger.warning("Ollama is unavailable, skipping AI analysis: %s", exc)
                return saved
            if not body:
                continue
            workout_id = item["workout"]["id"]
            response = await client.post(
                f"{config.public_base_url}/api/coach/recommendations",
                json={
                    "workout_id": workout_id,
                    "title": "AI-разбор тренировки",
                    "body": body,
                    "priority": "normal",
                },
                timeout=30,
            )
            response.raise_for_status()
            saved += 1
        return saved


async def run_loop(interval_seconds: int) -> None:
    while True:
        try:
            saved = await run_once()
            logger.info("AI recommendations saved: %s", saved)
        except Exception:
            logger.exception("AI worker cycle failed")
        await asyncio.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Ollama worker for Training Bot")
    parser.add_argument("--loop", action="store_true", help="keep checking cloud backend for new workouts")
    parser.add_argument("--interval", type=int, default=900, help="seconds between checks in --loop mode")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    if args.loop:
        interval = max(args.interval, 60)
        logger.info("AI worker loop started, interval=%ss", interval)
        asyncio.run(run_loop(interval))
        return
    saved = asyncio.run(run_once())
    logger.info("AI recommendations saved: %s", saved)


if __name__ == "__main__":
    main()
