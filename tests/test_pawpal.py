"""Tests for PawPal+ core classes. Run: python -m pytest"""

from datetime import date, time, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


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


def make_scheduler() -> Scheduler:
    owner = Owner(name="Jordan")
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Dinner", "18:00", 10, "high"))
    mochi.add_task(Task("Morning walk", "7:30", 30, "high"))
    luna.add_task(Task("Brush fur", "08:00", 15, "low"))
    luna.add_task(Task("Breakfast", "08:00", 5, "high"))
    return Scheduler(owner)


def test_task_accepts_hh_mm_string():
    assert Task("Walk", "7:05").start_time == time(7, 5)
    assert Task("Walk", "19:45").start_time == time(19, 45)


@pytest.mark.parametrize("bad", ["25:00", "7.30", "noon", ""])
def test_task_rejects_bad_time_string(bad):
    with pytest.raises(ValueError):
        Task("Walk", bad)


def test_sort_by_time_orders_chronologically_with_priority_tiebreak():
    scheduler = make_scheduler()

    ordered = [t.description for _, t in scheduler.sort_by_time(scheduler.get_tasks())]

    assert ordered == ["Morning walk", "Breakfast", "Brush fur", "Dinner"]


def test_get_tasks_filters_by_pet_name_case_insensitively():
    scheduler = make_scheduler()

    tasks = scheduler.get_tasks(pet_name="luna")

    assert {t.description for _, t in tasks} == {"Brush fur", "Breakfast"}


def test_get_tasks_filters_by_status_and_pet_together():
    scheduler = make_scheduler()
    scheduler.mark_task_complete("Mochi", "Dinner")

    assert [t.description for _, t in scheduler.get_tasks(completed=True)] == ["Dinner"]
    assert [t.description for _, t in scheduler.get_tasks("Mochi", completed=False)] == ["Morning walk"]
    assert scheduler.get_tasks(pet_name="Nobody") == []


TODAY = date(2026, 10, 3)


@pytest.mark.parametrize(
    "frequency, expected_due",
    [("daily", date(2026, 10, 4)), ("weekly", date(2026, 10, 10))],
)
def test_next_occurrence_moves_due_date_forward(frequency, expected_due):
    task = Task("Walk", "07:30", 30, "high", frequency, due_date=TODAY)
    task.mark_complete()

    nxt = task.next_occurrence(today=TODAY)

    assert nxt.due_date == expected_due
    assert nxt.completed is False
    assert (nxt.description, nxt.start_time, nxt.priority) == ("Walk", time(7, 30), "high")


def test_next_occurrence_is_none_for_one_off_task():
    assert Task("Vet visit", "10:00", frequency="once").next_occurrence() is None


def test_next_occurrence_handles_month_and_year_rollover():
    assert Task("Feed", "8:00", frequency="daily", due_date=date(2026, 1, 31)).next_occurrence(
        today=date(2026, 1, 31)
    ).due_date == date(2026, 2, 1)
    assert Task("Feed", "8:00", frequency="weekly", due_date=date(2026, 12, 29)).next_occurrence(
        today=date(2026, 12, 29)
    ).due_date == date(2027, 1, 5)


def test_overdue_task_finished_late_is_next_due_tomorrow():
    task = Task("Feed", "8:00", frequency="daily", due_date=TODAY - timedelta(days=3))

    assert task.next_occurrence(today=TODAY).due_date == TODAY + timedelta(days=1)


def test_completing_daily_task_adds_tomorrows_copy():
    owner = Owner(name="Jordan")
    mochi = Pet(name="Mochi", species="dog")
    owner.add_pet(mochi)
    mochi.add_task(Task("Walk", "07:30", 30, "high", "daily", due_date=TODAY))
    scheduler = Scheduler(owner)

    assert scheduler.mark_task_complete("Mochi", "Walk", today=TODAY) is True

    done, upcoming = mochi.tasks
    assert done.completed is True and done.due_date == TODAY
    assert upcoming.completed is False and upcoming.due_date == TODAY + timedelta(days=1)
    # Tomorrow's copy isn't on today's schedule, but shows up tomorrow.
    assert scheduler.todays_schedule(today=TODAY) == []
    assert scheduler.todays_schedule(today=TODAY + timedelta(days=1)) == [(mochi, upcoming)]


def test_completing_one_off_task_adds_nothing():
    owner = Owner(name="Jordan")
    mochi = Pet(name="Mochi", species="dog")
    owner.add_pet(mochi)
    mochi.add_task(Task("Vet visit", "10:00", frequency="once", due_date=TODAY))

    Scheduler(owner).mark_task_complete("Mochi", "Vet visit", today=TODAY)

    assert len(mochi.tasks) == 1


def test_mark_complete_targets_pending_copy_each_time():
    owner = Owner(name="Jordan")
    mochi = Pet(name="Mochi", species="dog")
    owner.add_pet(mochi)
    mochi.add_task(Task("Walk", "07:30", frequency="daily", due_date=TODAY))
    scheduler = Scheduler(owner)

    scheduler.mark_task_complete("Mochi", "Walk", today=TODAY)
    scheduler.mark_task_complete("Mochi", "Walk", today=TODAY)

    # Each call completes the current pending copy and adds the next one.
    assert [t.completed for t in mochi.tasks] == [True, True, False]
    assert [t.due_date.day for t in mochi.tasks] == [3, 4, 5]


def test_mark_complete_returns_false_when_missing():
    scheduler = make_scheduler()

    assert scheduler.mark_task_complete("Nobody", "Dinner") is False
    assert scheduler.mark_task_complete("Mochi", "Nap") is False


def conflict_scheduler(*tasks_by_pet):
    """Build a scheduler from (pet_name, Task) pairs, all due TODAY, with plenty of time."""
    # 600 minutes is enough that no task gets skipped, so every task is checked for conflicts.
    owner = Owner(name="Jordan", available_minutes=600)
    for pet_name, task in tasks_by_pet:
        # Reuse the pet if it already exists, so several tasks can belong to the same pet.
        pet = owner.find_pet(pet_name)
        if pet is None:
            pet = Pet(name=pet_name, species="dog")
            owner.add_pet(pet)
        # Pin the date so results don't depend on the day the tests are run.
        task.due_date = TODAY
        pet.add_task(task)
    return Scheduler(owner)


def conflict_names(scheduler):
    """Return the conflicting pairs as (description, description) tuples, which are easy to compare."""
    return [(a.description, b.description) for (_, a), (_, b) in scheduler.find_conflicts(TODAY)]


def test_same_time_different_pets_is_a_conflict():
    scheduler = conflict_scheduler(
        ("Mochi", Task("Brush teeth", "08:15", 10)),  # 08:15-08:25
        ("Luna", Task("Medication", "08:15", 5)),  # 08:15-08:20, different pet, same start
    )

    # Same time and priority, so the tie-breaker orders pets by name: Luna before Mochi.
    assert conflict_names(scheduler) == [("Medication", "Brush teeth")]
    [warning] = scheduler.conflict_warnings(TODAY)
    assert "Luna & Mochi" in warning and "start at the same time" in warning


def test_same_time_same_pet_is_a_conflict():
    scheduler = conflict_scheduler(
        ("Mochi", Task("Walk", "07:30", 30)),
        ("Mochi", Task("Flea treatment", "07:30", 5)),  # same pet, same start
    )

    # Unpacking into [warning] also checks there is exactly one warning.
    [warning] = scheduler.conflict_warnings(TODAY)
    assert "same pet: Mochi" in warning


def test_partial_overlap_is_a_conflict():
    scheduler = conflict_scheduler(
        ("Mochi", Task("Walk", "07:30", 30)),  # 07:30-08:00
        ("Luna", Task("Breakfast", "07:45", 5)),  # starts mid-walk
    )

    assert conflict_names(scheduler) == [("Walk", "Breakfast")]
    # The warning shows each task's full time window, not just its start time.
    assert "07:30-08:00" in scheduler.conflict_warnings(TODAY)[0]


def test_back_to_back_tasks_do_not_conflict():
    scheduler = conflict_scheduler(
        ("Mochi", Task("Walk", "07:30", 30)),  # ends 08:00
        ("Luna", Task("Breakfast", "08:00", 5)),  # starts the minute the walk ends
    )

    # Touching windows aren't an overlap, so there are no pairs and no warnings.
    assert scheduler.find_conflicts(TODAY) == []
    assert scheduler.conflict_warnings(TODAY) == []


def test_long_task_conflicts_with_every_task_inside_it():
    scheduler = conflict_scheduler(
        ("Mochi", Task("Hike", "09:00", 120)),  # 09:00-11:00
        ("Luna", Task("Feed", "09:30", 5)),
        ("Luna", Task("Play", "10:30", 15)),
    )

    # Feed and Play don't overlap each other, but both overlap the hike.
    assert conflict_names(scheduler) == [("Hike", "Feed"), ("Hike", "Play")]


def test_completed_and_future_tasks_are_not_checked_for_conflicts():
    scheduler = conflict_scheduler(
        ("Mochi", Task("Walk", "07:30", 30, frequency="daily")),
        ("Luna", Task("Breakfast", "07:30", 5)),
    )
    scheduler.mark_task_complete("Mochi", "Walk", today=TODAY)  # adds tomorrow's walk

    # Today's walk is done and tomorrow's isn't due yet, so Breakfast has nothing to clash with.
    assert scheduler.find_conflicts(TODAY) == []
