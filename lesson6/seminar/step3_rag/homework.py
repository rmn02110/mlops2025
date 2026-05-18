import base64
import io
import json
from pathlib import Path

import requests
from PIL import Image

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
POSE_API_URL = "http://localhost:8001/visualize"


def load_poses(path="poses_database.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ask_ollama(query):
    prompt = (
        f"Опиши 8 коротких поз для анимации '{query}'. "
        "Каждая поза с новой строки, без нумерации."
    )
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "qwen2.5:1.5b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        },
        timeout=30,
    )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]
    return [line.strip(" -0123456789.") for line in text.splitlines() if line.strip()]


def score(text, description):
    words = set(text.lower().replace(",", " ").split())
    desc_words = set(description.lower().replace(",", " ").split())
    return len(words & desc_words)


def retrieve_pose(move, database):
    return max(database, key=lambda item: score(move, item["description"]))["pose"]


def render_pose(pose):
    response = requests.post(POSE_API_URL, json={"pose": pose}, timeout=10)
    response.raise_for_status()
    image = response.json()["image"]
    return Image.open(io.BytesIO(base64.b64decode(image))).convert("RGB")


def generate_animation(query="танец макарена"):
    database = load_poses()
    moves = ask_ollama(query)

    frames = [render_pose(retrieve_pose(move, database)) for move in moves[:8]]

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{query.replace(' ', '_')}.gif"
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=400,
        loop=0,
        format="GIF",
    )
    print(output_path)


if __name__ == "__main__":
    generate_animation("танец макарена")
