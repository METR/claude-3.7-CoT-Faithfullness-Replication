def get_model_short_name(model_name: str) -> str:
    if "claude-3-7-sonnet" in model_name:
        return "Claude 3.7 Sonnet"
    elif "Qwen3" in model_name:
        return "Qwen3-235B"
    elif "claude-opus-4" in model_name:
        return "Claude Opus"
    return "Unknown Model"