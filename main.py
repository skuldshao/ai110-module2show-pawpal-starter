"""Terminal testing ground for PawPal+ logic. Run: python main.py"""

from datetime import time

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(owner: Owner, scheduler: Scheduler) -> None:
    """Print today's plan as a table, then any skipped tasks and conflict warnings."""
    schedule = scheduler.todays_schedule()
    total = sum(task.duration_minutes for _, task in schedule)

    print()
    print(f"🐾 Today's Schedule for {owner.name}")
    print("=" * 60)
    print(f"{'Time':<7}{'Pet':<8}{'Task':<22}{'Length':<9}{'Priority'}")
    print("-" * 60)
    for pet, task in schedule:
        print(
            f"{task.start_time.strftime('%H:%M'):<7}"
            f"{pet.name:<8}"
            f"{task.description:<22}"
            f"{str(task.duration_minutes) + ' min':<9}"
            f"{task.priority}"
        )
    print("-" * 60)
    print(f"Total: {total} of {owner.available_minutes} available minutes")

    skipped = scheduler.skipped_tasks()
    if skipped:
        print("\nSkipped (not enough time):")
        for pet, task in skipped:
            print(f"  - {pet.name}: {task.description} ({task.duration_minutes} min, {task.priority})")

    # Conflicts come back as warning strings, so printing them never stops the program.
    warnings = scheduler.conflict_warnings()
    print()
    if warnings:
        print("Conflicts:")
        for warning in warnings:
            print(f"  {warning}")
    else:
        print("No time conflicts.")
    print()


def print_tasks(title: str, tasks) -> None:
    """Print a titled list of (pet, task) pairs with due date, time, priority, and status."""
    print(f"{title}:")
    for pet, task in tasks:
        status = "done" if task.completed else "pending"
        print(
            f"  {task.due_date:%a %b %d} {task.start_time.strftime('%H:%M')}  {pet.name:<6} "
            f"{task.description:<20} {task.priority:<7}{status}"
        )
    if not tasks:
        print("  (none)")
    print()


def main() -> None:
    """Build a sample owner with two pets, then demo each scheduling feature."""
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of order; some times are "HH:MM" strings.
    mochi.add_task(Task("Dinner", "18:00", 10, "high", "daily"))
    mochi.add_task(Task("Fetch in the yard", "16:00", 40, "low", "once"))
    mochi.add_task(Task("Morning walk", time(7, 30), 30, "high", "daily"))
    luna.add_task(Task("Brush fur", "19:30", 15, "medium", "weekly"))
    luna.add_task(Task("Thyroid medication", "8:15", 5, "high", "daily"))
    luna.add_task(Task("Breakfast", time(8, 0), 5, "high", "daily"))
    # Deliberate conflicts: same time for different pets, and same time for the same pet.
    mochi.add_task(Task("Brush teeth", "08:15", 10, "medium", "daily"))  # = Luna's medication
    mochi.add_task(Task("Flea treatment", "07:30", 5, "high", "once"))  # = Mochi's walk

    scheduler = Scheduler(owner)
    # Completing recurring tasks adds their next occurrence automatically.
    scheduler.mark_task_complete("Luna", "Breakfast")  # daily  -> new copy due tomorrow
    scheduler.mark_task_complete("Luna", "Brush fur")  # weekly -> new copy due in 7 days
    scheduler.mark_task_complete("Mochi", "Fetch in the yard")  # once -> no new copy

    print()
    print_tasks("All tasks (insertion order)", scheduler.get_tasks())
    print_tasks("All tasks sorted by time", scheduler.sort_by_time(scheduler.get_tasks()))
    print_tasks("Mochi's tasks", scheduler.sort_by_time(scheduler.get_tasks(pet_name="Mochi")))
    print_tasks("Completed tasks", scheduler.get_tasks(completed=True))
    print_tasks(
        "Luna's pending tasks",
        scheduler.sort_by_time(scheduler.get_tasks(pet_name="luna", completed=False)),
    )

    print_schedule(owner, scheduler)


if __name__ == "__main__":
    main()
