# app/services/whitelist_engine.py

GLOBAL_WHITELIST = {
    "ai": [
        "默念"
    ],
    "tc_sc": [
        "宣布"
    ],
    "all": [
        "Vivi Tam"
    ]
}


def apply_whitelist(errors: list) -> list:
    filtered = []

    for err in errors:
        word = err.get("wrong", "").strip()
        category = err.get("category", "")

        # 全域白名單
        if word in GLOBAL_WHITELIST.get("all", []):
            continue

        # 分類白名單
        if word in GLOBAL_WHITELIST.get(category, []):
            continue

        filtered.append(err)

    return filtered