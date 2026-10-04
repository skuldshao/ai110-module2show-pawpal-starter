"""Tests for PawPal+ core classes. Run: python -m pytest"""

from datetime import time

from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", time(7, 30), 30, "high", "daily")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.tasks) == 0

    pet.add_task(Task("Dinner", time(18, 0), 10, "high", "daily"))

    assert len(pet.tasks) == 1
