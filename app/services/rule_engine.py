# app/services/rule_engine.py

import json
import re
from pathlib import Path

RULE_FILE = Path("data/rules.json")


# ✅ 讀取規則
def load_rules():
    if not RULE_FILE.exists():
        return []

    with open(RULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ✅ 套用規則
def apply_rules(text: str) -> list:
    rules = load_rules()
    issues = []

    for rule in rules:

        # ✅ 規則開關
        if not rule.get("enabled", True):
            continue

        pattern = rule.get("pattern")
        if not pattern:
            continue

        try:
            matches = re.finditer(pattern, text)
        except re.error:
            continue  # regex 錯誤時忽略

        for match in matches:
            issues.append({
                "wrong": rule.get("wrong", ""),
                "correct": rule.get("correct", ""),
                "reason": rule.get("reason", ""),
                "start": match.start(),
                "end": match.end(),
                "category": "rule",
                "priority": rule.get("priority", 50)
            })

    return issues