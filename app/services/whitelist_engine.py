# app/services/whitelist_engine.py

GLOBAL_WHITELIST = {
    "ai_words": set([
        "默念"
    ]),

    "tc_sc_words": set([   # ✅ 單字白名單
        # "綫"
    ]),

    "tc_sc_phrases": set([  # ✅ 詞級白名單
        "宣布",
        "大件事"
    ]),

    "all_words": set([
        "Vivi Tam"
    ])
}


def apply_whitelist(errors: list, original_text: str) -> list:
    filtered = []

    for err in errors:
        word = err.get("wrong", "").strip()
        category = err.get("category", "")
        start = err.get("start")
        end = err.get("end")

        # ✅ 1️⃣ 全域單字白名單
        if word in GLOBAL_WHITELIST["all_words"]:
            continue

        # ✅ 2️⃣ AI 單字白名單
        if category == "ai" and word in GLOBAL_WHITELIST["ai_words"]:
            continue

        # ✅ 3️⃣ 繁簡單字白名單
        if category == "tc_sc" and word in GLOBAL_WHITELIST["tc_sc_words"]:
            continue

        # ✅ 4️⃣ 繁簡詞級白名單
        if category == "tc_sc" and start is not None and end is not None:
            for phrase in GLOBAL_WHITELIST["tc_sc_phrases"]:
                phrase_start = original_text.find(phrase)
                if phrase_start != -1:
                    phrase_end = phrase_start + len(phrase)

                    # 如果錯字在白名單詞內 → 忽略
                    if start >= phrase_start and end <= phrase_end:
                        break
            else:
                filtered.append(err)
            continue

        filtered.append(err)

    return filtered