"""Budget calculator implementing Innovation Authority procedure 200-02 rules."""

from dataclasses import dataclass
from ..config.constants import (
    MAX_BUDGET_NIS,
    GRANT_RATE,
    MAX_GRANT_NIS,
    MAX_HOURLY_RATE_NIS,
    EQUIPMENT_DEPRECIATION_RATE,
    ELIGIBLE_CATEGORIES,
    FORBIDDEN_EXPENSES,
    WOMEN_ENTREPRENEUR_BONUS,
    BIO_MAX_BUDGET_NIS,
    BIO_GRANT_RATE,
    BIO_MAX_GRANT_NIS,
)


@dataclass
class BudgetValidation:
    is_valid: bool
    total_budget: float
    grant_amount: float
    self_funding: float
    errors: list[str]
    warnings: list[str]


def calculate_grant(
    total_budget: float,
    is_woman_entrepreneur: bool = False,
    is_bio_convergence: bool = False,
) -> dict:
    """Calculate grant amount based on total budget and track."""
    if is_bio_convergence:
        max_budget = BIO_MAX_BUDGET_NIS
        rate = BIO_GRANT_RATE
        max_grant = BIO_MAX_GRANT_NIS
    else:
        max_budget = MAX_BUDGET_NIS
        rate = GRANT_RATE
        max_grant = MAX_GRANT_NIS

    capped_budget = min(total_budget, max_budget)
    grant = min(rate * capped_budget, max_grant)

    if is_woman_entrepreneur:
        bonus = grant * WOMEN_ENTREPRENEUR_BONUS
        grant = min(grant + bonus, max_grant * 1.1)

    self_funding = capped_budget - grant

    return {
        "total_budget": capped_budget,
        "grant_amount": grant,
        "self_funding": self_funding,
        "grant_rate": grant / capped_budget if capped_budget > 0 else 0,
    }


def validate_budget(budget_lines: list[dict], is_woman_entrepreneur: bool = False) -> BudgetValidation:
    """Validate budget lines against Tnufa procedure 200-02 rules."""
    errors = []
    warnings = []
    total = 0.0

    for i, line in enumerate(budget_lines):
        category = line.get("category", "")
        amount = line.get("amount", 0)
        hourly_rate = line.get("hourly_rate")

        # Check forbidden categories
        if category in FORBIDDEN_EXPENSES:
            errors.append(
                f"שורה {i+1}: קטגוריה '{category}' אינה מוכרת במסלול תנופה"
            )
            continue

        # Check eligible categories
        if category not in ELIGIBLE_CATEGORIES:
            warnings.append(
                f"שורה {i+1}: קטגוריה '{category}' לא בסיווג המוכר - ייתכן שתידחה"
            )

        # Check hourly rate limit
        if hourly_rate and hourly_rate > MAX_HOURLY_RATE_NIS:
            errors.append(
                f"שורה {i+1}: תעריף שעתי {hourly_rate} ש\"ח חורג מהתקרה ({MAX_HOURLY_RATE_NIS} ש\"ח)"
            )

        # Check positive amounts
        if amount <= 0:
            errors.append(f"שורה {i+1}: סכום חייב להיות חיובי")
            continue

        total += amount

    # Check total budget
    if total > MAX_BUDGET_NIS:
        errors.append(
            f"תקציב כולל ({total:,.0f} ש\"ח) חורג מהתקרה ({MAX_BUDGET_NIS:,.0f} ש\"ח)"
        )

    if total < 50_000:
        warnings.append("תקציב נמוך מאוד - שקול להגדיל לניצול מיטבי של המענק")

    # Calculate grant
    grant_info = calculate_grant(total, is_woman_entrepreneur)

    return BudgetValidation(
        is_valid=len(errors) == 0,
        total_budget=grant_info["total_budget"],
        grant_amount=grant_info["grant_amount"],
        self_funding=grant_info["self_funding"],
        errors=errors,
        warnings=warnings,
    )


def optimize_budget(
    desired_activities: list[dict],
    is_woman_entrepreneur: bool = False,
) -> list[dict]:
    """Optimize budget allocation to maximize grant while staying within limits.

    Each activity: {"description": str, "category": str, "min_amount": float, "max_amount": float}
    """
    # Strategy: fill up to MAX_BUDGET_NIS for maximum grant
    target_total = MAX_BUDGET_NIS

    # Filter out forbidden categories
    valid_activities = [
        a for a in desired_activities
        if a.get("category") not in FORBIDDEN_EXPENSES
    ]

    if not valid_activities:
        return []

    # Start with minimum amounts
    budget_lines = []
    current_total = sum(a.get("min_amount", 0) for a in valid_activities)

    if current_total > target_total:
        # Scale down proportionally
        scale = target_total / current_total
        for activity in valid_activities:
            amount = activity["min_amount"] * scale
            budget_lines.append({
                "category": activity["category"],
                "description_he": activity.get("description", ""),
                "amount": round(amount, -2),  # Round to nearest 100
                "grant_portion": round(amount * GRANT_RATE, -2),
                "justification_he": activity.get("justification", ""),
                "hourly_rate": min(activity.get("hourly_rate", 0), MAX_HOURLY_RATE_NIS) or None,
                "hours": activity.get("hours"),
            })
    else:
        # Distribute remaining budget proportionally up to max
        remaining = target_total - current_total
        expandable = [
            a for a in valid_activities
            if a.get("max_amount", a["min_amount"]) > a["min_amount"]
        ]

        for activity in valid_activities:
            amount = activity["min_amount"]
            if activity in expandable and remaining > 0:
                max_extra = activity.get("max_amount", amount) - amount
                extra = min(max_extra, remaining / len(expandable))
                amount += extra
                remaining -= extra

            budget_lines.append({
                "category": activity["category"],
                "description_he": activity.get("description", ""),
                "amount": round(amount, -2),
                "grant_portion": round(amount * GRANT_RATE, -2),
                "justification_he": activity.get("justification", ""),
                "hourly_rate": min(activity.get("hourly_rate", 0), MAX_HOURLY_RATE_NIS) or None,
                "hours": activity.get("hours"),
            })

    return budget_lines
