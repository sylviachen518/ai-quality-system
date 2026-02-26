def analyze_text(text: str):
    text_length = len(text)

    if text_length < 20:
        score = 60
        feedback = "內容太短，可以再更詳細一些。"
    elif text_length < 100:
        score = 80
        feedback = "內容不錯，可以再補充一些細節。"
    else:
        score = 95
        feedback = "內容完整且詳細，品質很好！"

    return {
        "score": score,
        "feedback": feedback
    }