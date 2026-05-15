"""Tests for the budget calculator (procedure 200-02 compliance)."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.budget_calculator import calculate_grant, validate_budget, optimize_budget


def test_basic_grant_calculation():
    """Test G = min(0.8 * T, 200000)."""
    result = calculate_grant(250_000)
    assert result["grant_amount"] == 200_000
    assert result["self_funding"] == 50_000
    assert result["total_budget"] == 250_000


def test_grant_capped_at_200k():
    """Grant should never exceed 200,000 NIS."""
    result = calculate_grant(300_000)
    assert result["grant_amount"] == 200_000
    assert result["total_budget"] == 250_000  # Capped


def test_small_budget():
    """Smaller budgets get 80% grant."""
    result = calculate_grant(100_000)
    assert result["grant_amount"] == 80_000
    assert result["self_funding"] == 20_000


def test_woman_entrepreneur_bonus():
    """Women entrepreneurs get 10% bonus."""
    result = calculate_grant(250_000, is_woman_entrepreneur=True)
    assert result["grant_amount"] > 200_000  # 10% bonus applied


def test_validate_valid_budget():
    """Valid budget lines should pass."""
    lines = [
        {"category": "subcontractors", "amount": 100_000, "hourly_rate": 250},
        {"category": "materials", "amount": 50_000, "hourly_rate": None},
        {"category": "ip_patents", "amount": 30_000, "hourly_rate": None},
    ]
    result = validate_budget(lines)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_forbidden_category():
    """Forbidden expense categories should fail."""
    lines = [
        {"category": "founder_salary", "amount": 100_000, "hourly_rate": None},
    ]
    result = validate_budget(lines)
    assert result.is_valid is False
    assert any("אינה מוכרת" in e for e in result.errors)


def test_validate_hourly_rate_exceeded():
    """Hourly rate above 300 NIS should fail."""
    lines = [
        {"category": "subcontractors", "amount": 100_000, "hourly_rate": 450},
    ]
    result = validate_budget(lines)
    assert result.is_valid is False
    assert any("חורג מהתקרה" in e for e in result.errors)


def test_validate_budget_over_max():
    """Total over 250,000 should fail."""
    lines = [
        {"category": "subcontractors", "amount": 200_000, "hourly_rate": 250},
        {"category": "materials", "amount": 100_000, "hourly_rate": None},
    ]
    result = validate_budget(lines)
    assert result.is_valid is False
    assert any("חורג" in e for e in result.errors)


def test_optimize_budget_targets_max():
    """Optimizer should try to fill up to 250K."""
    activities = [
        {"description": "Dev", "category": "subcontractors", "min_amount": 50_000, "max_amount": 150_000},
        {"description": "IP", "category": "ip_patents", "min_amount": 20_000, "max_amount": 50_000},
        {"description": "Biz", "category": "business_development", "min_amount": 10_000, "max_amount": 40_000},
    ]
    result = optimize_budget(activities)
    assert len(result) == 3
    total = sum(l["amount"] for l in result)
    assert total <= 250_000


def test_optimize_excludes_forbidden():
    """Optimizer should skip forbidden categories."""
    activities = [
        {"description": "Salary", "category": "founder_salary", "min_amount": 100_000, "max_amount": 100_000},
        {"description": "Dev", "category": "subcontractors", "min_amount": 50_000, "max_amount": 150_000},
    ]
    result = optimize_budget(activities)
    assert len(result) == 1
    assert result[0]["category"] == "subcontractors"


if __name__ == "__main__":
    test_basic_grant_calculation()
    test_grant_capped_at_200k()
    test_small_budget()
    test_woman_entrepreneur_bonus()
    test_validate_valid_budget()
    test_validate_forbidden_category()
    test_validate_hourly_rate_exceeded()
    test_validate_budget_over_max()
    test_optimize_budget_targets_max()
    test_optimize_excludes_forbidden()
    print("✅ All budget calculator tests passed!")
