# app/services/whitelist_engine.py

import json
from pathlib import Path

WHITELIST_FILE = Path("data/whitelist.json")


def load_whitelist():
    if not WHITELIST_FILE.exists():
        return {
            "all": [],
            "ai": [],
            "tc_sc": [],
            "rule": [],
            "phrases": []
        }

    with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_whitelist(data):
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def apply_whitelist(errors: list, original_text: str) -> list:
    whitelist = load_whitelist()
    filtered = []

    for err in errors:
        word = err.get("wrong", "")
        category = err.get("category", "")
        start = err.get("start")
        end = err.get("end")

        # ✅ 全域
        if word in whitelist.get("all", []):
            continue

        # ✅ 分類白名單
        if word in whitelist.get(category, []):
            continue

        # ✅ 詞組白名單
        if start is not None and end is not None:
            for phrase in whitelist.get("phrases", []):
                phrase_start = original_text.find(phrase)
                if phrase_start != -1:
                    phrase_end = phrase_start + len(phrase)
                    if start >= phrase_start and end <= phrase_end:
                        break
            else:
                filtered.append(err)
            continue

        filtered.append(err)

    return filtered


def add_to_whitelist(word: str, category="all"):
    whitelist = load_whitelist()

    if category not in whitelist:
        whitelist[category] = []

    if word not in whitelist[category]:
        whitelist[category].append(word)

    save_whitelist(whitelist)