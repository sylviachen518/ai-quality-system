from app.services.dictionary_engine import check_dictionary
from app.services.severity_engine import assign_severity


def evaluate_spelling(title: str, content: str):
    issues = []

    # ✅ 組合全文
    full_text = title + "\n" + content
    title_length = len(title)

    # ==========
    # 1️⃣ 標題
    # ==========

    title_errors = check_dictionary(title)

    for err in title_errors:
        start = err["position"]
        end = start + len(err["wrong"])

        issues.append({
            "wrong": err["wrong"],
            "correct": err["correct"],
            "position": start,
            "end_position": end,
            "section": "title",
            "severity": assign_severity("title")
        })

    # ==========
    # 2️⃣ 內文（算絕對位置）
    # ==========

    content_errors = check_dictionary(content)

    # 判斷首段範圍
    first_paragraph_end = content.find("\n")
    if first_paragraph_end == -1:
        first_paragraph_end = len(content)

    for err in content_errors:
        absolute_start = title_length + 1 + err["position"]
        absolute_end = absolute_start + len(err["wrong"])

        if err["position"] < first_paragraph_end:
            section = "first_paragraph"
        else:
            section = "body"

        issues.append({
            "wrong": err["wrong"],
            "correct": err["correct"],
            "position": absolute_start,
            "end_position": absolute_end,
            "section": section,
            "severity": assign_severity(section)
        })

    # ✅ 排序（確保依照全文順序）
    issues.sort(key=lambda x: x["position"])

    return issues