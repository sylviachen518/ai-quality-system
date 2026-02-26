def combine_feedback(rule_issues, ai_feedback):
    if not rule_issues:
        return ai_feedback

    issue_texts = [issue["issue"] for issue in rule_issues]

    rule_part = "檢測到以下問題：" + "、".join(issue_texts)

    if ai_feedback:
        return rule_part + "。另外，AI 建議：" + ai_feedback

    return rule_part