"""Terminal testing ground for PawPal+ logic. Run: python main.py"""

from datetime import time

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(owner: Owner, scheduler: Scheduler) -> None:
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
    print()


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", time(7, 30), 30, "high", "daily"))
    mochi.add_task(Task("Dinner", time(18, 0), 10, "high", "daily"))
    mochi.add_task(Task("Fetch in the yard", time(16, 0), 40, "low", "once"))
    luna.add_task(Task("Breakfast", time(8, 0), 5, "high", "daily"))
    luna.add_task(Task("Thyroid medication", time(8, 15), 5, "high", "daily"))
    luna.add_task(Task("Brush fur", time(19, 30), 15, "medium", "weekly"))

    print_schedule(owner, Scheduler(owner))


if __name__ == "__main__":
    main()
