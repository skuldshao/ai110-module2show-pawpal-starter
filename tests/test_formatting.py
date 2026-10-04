"""Tests for the display helpers in formatting.py. Run: python -m pytest"""

import io
import re
from datetime import date

import pytest
import wcwidth
from tabulate import tabulate

from formatting import (
    colorize,
    color_enabled,
    priority_badge,
    status_badge,
    task_emoji,
    task_label,
    task_status,
)
from main import budget_bar
from pawpal_system import Task

TODAY = date(2026, 10, 3)


@pytest.mark.parametrize(
    "description, emoji",
    [
        ("Morning walk", "🦮"),
        ("Thyroid medication", "💊"),
        ("Flea treatment", "💊"),  # "treatment" is medicine, not a food "treat"
        ("Brush teeth", "🦷"),  # teeth is checked before brush
        ("Brush fur", "🧼"),
        ("BREAKFAST", "🍖"),  # case doesn't matter
        ("Fetch in the yard", "🎾"),
        ("Vet checkup", "🩺"),
        ("Clean litter box", "🧹"),
        ("Brunch", "🐾"),  # no keyword: "run" isn't a walk keyword, so no false match
        ("Nap", "🐾"),
    ],
)
def test_task_emoji_matches_keywords(description, emoji):
    assert task_emoji(description) == emoji


def test_task_label_puts_emoji_before_description():
    assert task_label(Task("Dinner", "18:00")) == "🍖 Dinner"


def test_priority_badge_uses_traffic_light_colors():
    assert [priority_badge(p) for p in ("high", "medium", "low")] == [
        "🔴 high", "🟡 medium", "🟢 low"]


@pytest.mark.parametrize(
    "due, completed, status",
    [
        (date(2026, 10, 2), True, "done"),  # done wins, even if it was overdue
        (date(2026, 10, 2), False, "overdue"),
        (TODAY, False, "pending"),
        (date(2026, 10, 4), False, "upcoming"),
    ],
)
def test_task_status(due, completed, status):
    task = Task("Walk", "07:00", completed=completed, due_date=due)

    assert task_status(task, TODAY) == status


def test_status_badge_has_emoji():
    assert status_badge(Task("Walk", "07:00", due_date=TODAY), TODAY) == "⏳ due today"


def test_colorize_wraps_text_only_when_enabled():
    assert colorize("high", "high", enabled=False) == "high"
    colored = colorize("high", "high")
    assert colored.startswith("\033[") and colored.endswith("\033[0m") and "high" in colored


def test_color_is_off_for_non_terminals_and_no_color(monkeypatch):
    class FakeTerminal(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.delenv("NO_COLOR", raising=False)
    assert color_enabled(io.StringIO()) is False  # e.g. output redirected to a file
    assert color_enabled(FakeTerminal()) is True
    monkeypatch.setenv("NO_COLOR", "1")
    assert color_enabled(FakeTerminal()) is False


def test_colored_emoji_table_lines_up():
    # tabulate must ignore ANSI codes and count emojis as 2 columns, or borders drift.
    rows = [[task_label(Task("Walk", "07:00")), colorize(priority_badge("high"), "high")],
            [task_label(Task("Thyroid medication", "08:00")), priority_badge("low")]]
    lines = tabulate(rows, headers=["Task", "Priority"], tablefmt="rounded_outline").splitlines()

    widths = {wcwidth.wcswidth(re.sub(r"\033\[[0-9;]*m", "", line)) for line in lines}
    assert len(widths) == 1


@pytest.mark.parametrize(
    "used, available, expected",
    [
        (60, 90, "████████████████████░░░░░░░░░░ 60/90 min (67%)"),
        (0, 90, "░" * 30 + " 0/90 min (0%)"),
        (0, 0, "░" * 30 + " 0/0 min (0%)"),  # no division by zero
    ],
)
def test_budget_bar(used, available, expected):
    assert budget_bar(used, available) == expected
