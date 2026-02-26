def calculate_risk_level(issues):
    if not issues:
        return "safe"

    severities = [issue["severity"] for issue in issues]

    if "high" in severities:
        return "high"

    if "medium" in severities:
        return "medium"

    return "low"