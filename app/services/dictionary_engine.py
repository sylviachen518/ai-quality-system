from app.services.spelling_dictionary import COMMON_MISTAKES


def check_dictionary(text: str):
    issues = []

    for wrong, correct in COMMON_MISTAKES.items():
        start = 0

        while True:
            index = text.find(wrong, start)

            if index == -1:
                break

            issues.append({
                "wrong": wrong,
                "correct": correct,
                "position": index
            })

            start = index + len(wrong)

    return issues