PRICING = {
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
    },
    "claude-haiku-4-5-20251001": {
        "input": 1.00,
        "output": 5.00,
    },
    "claude-sonnet-5-5": {
        "input": 2.00,
        "output": 10.00,
    },
}


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    if model not in PRICING:
        return 0.0

    input_price = PRICING[model]["input"]
    output_price = PRICING[model]["output"]

    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price

    total_cost = input_cost + output_cost

    return round(total_cost, 6)