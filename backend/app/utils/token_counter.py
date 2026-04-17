INPUT_COST_PER_MTK = 3.0
OUTPUT_COST_PER_MTK = 15.0
CACHE_WRITE_COST_PER_MTK = 3.75
CACHE_READ_COST_PER_MTK = 0.30


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    cache_write_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> float:
    billable_input = max(0, input_tokens - cache_read_tokens - cache_write_tokens)
    cost = (
        billable_input * INPUT_COST_PER_MTK / 1_000_000
        + output_tokens * OUTPUT_COST_PER_MTK / 1_000_000
        + cache_write_tokens * CACHE_WRITE_COST_PER_MTK / 1_000_000
        + cache_read_tokens * CACHE_READ_COST_PER_MTK / 1_000_000
    )
    return round(cost, 6)
