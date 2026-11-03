from datetime import date
import calendar


def calculate_weight_change(
    current_weight: float,
    target_weight: float
) -> dict:
    """Calculate the difference between current and target weight."""

    if current_weight <= 0 or target_weight <= 0:
        raise ValueError("Weights must be greater than zero.")

    difference = round(target_weight - current_weight, 2)

    if difference > 0:
        goal = "weight_gain"
    elif difference < 0:
        goal = "weight_loss"
    else:
        goal = "maintain_weight"

    return {
        "current_weight_kg": current_weight,
        "target_weight_kg": target_weight,
        "weight_difference_kg": difference,
        "goal": goal,
    }


def _add_months(start_date: date, months: int) -> date:
    """Add calendar months while handling different month lengths."""

    month_index = start_date.month - 1 + months
    year = start_date.year + month_index // 12
    month = month_index % 12 + 1

    last_day = calendar.monthrange(year, month)[1]
    day = min(start_date.day, last_day)

    return date(year, month, day)


def generate_monthly_journey(
    current_weight: float,
    target_weight: float,
    start_date: str,
    duration_months: int = 3,
) -> dict:
    """
    Create monthly weight milestones between the starting
    and target weights.

    start_date must use YYYY-MM-DD format.
    """

    if current_weight <= 0 or target_weight <= 0:
        raise ValueError("Weights must be greater than zero.")

    if duration_months < 1:
        raise ValueError("Duration must be at least one month.")

    try:
        start = date.fromisoformat(start_date)
    except (TypeError, ValueError):
        raise ValueError("start_date must use YYYY-MM-DD format.")

    milestones = []

    for month in range(duration_months + 1):
        progress = month / duration_months

        milestone_weight = (
            current_weight
            + (target_weight - current_weight) * progress
        )

        milestone_date = _add_months(start, month)

        milestones.append({
            "month": month,
            "date": milestone_date.isoformat(),
            "target_weight_kg": round(milestone_weight, 2),
        })

    result = calculate_weight_change(current_weight, target_weight)

    return {
        **result,
        "start_date": start.isoformat(),
        "duration_months": duration_months,
        "milestones": milestones,
    }