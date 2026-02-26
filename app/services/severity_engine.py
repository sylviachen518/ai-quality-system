def assign_severity(section: str):
    if section in ["title", "first_paragraph"]:
        return "high"

    return "medium"