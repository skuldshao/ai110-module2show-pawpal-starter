"""Core classes for PawPal+: Task, Pet, Owner, and Scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from typing import List, Optional, Tuple

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = ("once", "daily", "weekly")


@dataclass
class Task:
    """A single pet care activity scheduled at a time of day."""

    description: str
    start_time: time
    duration_minutes: int = 15
    priority: str = "medium"  # "low", "medium", or "high"
    frequency: str = "once"  # "once", "daily", or "weekly"
    completed: bool = False

    def __post_init__(self) -> None:
        """Validate priority, frequency, and duration; raise ValueError if any is invalid."""
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    @property
    def end_minute(self) -> int:
        """Return the minute of the day (minutes after midnight) when this task finishes."""
        return self.start_time.hour * 60 + self.start_time.minute + self.duration_minutes

    def mark_complete(self) -> None:
        """Mark this task as done so it is excluded from the pending schedule."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as not done so it appears in the schedule again."""
        self.completed = False


@dataclass
class Pet:
    """A pet's details and the care tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove tasks matching this description; return True if anything was removed."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.description != description]
        return len(self.tasks) < before

    def find_task(self, description: str) -> Optional[Task]:
        """Return the first task with this description, or None if the pet has no such task."""
        return next((t for t in self.tasks if t.description == description), None)


@dataclass
class Owner:
    """A pet owner who manages multiple pets and their daily time budget."""

    name: str
    available_minutes: int = 120
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove pets with this name; return True if anything was removed."""
        before = len(self.pets)
        self.pets = [p for p in self.pets if p.name != name]
        return len(self.pets) < before

    def find_pet(self, name: str) -> Optional[Pet]:
        """Return the first pet with this name, or None if the owner has no such pet."""
        return next((p for p in self.pets if p.name == name), None)

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return every task from every pet as (pet, task) pairs, in pet order."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The 'brain': retrieves, organizes, and manages tasks across all of an owner's pets.

    All task data comes from Owner.get_all_tasks(), so every pet is always included.
    """

    def __init__(self, owner: Owner) -> None:
        """Store the owner whose pets and tasks this scheduler will read from."""
        self.owner = owner

    # --- Retrieval -----------------------------------------------------------

    def get_tasks(
        self, pet_name: Optional[str] = None, completed: Optional[bool] = None
    ) -> List[Tuple[Pet, Task]]:
        """Return (pet, task) pairs from all pets, optionally filtered by pet name and/or status."""
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [(p, t) for p, t in tasks if p.name == pet_name]
        if completed is not None:
            tasks = [(p, t) for p, t in tasks if t.completed == completed]
        return tasks

    # --- Organizing ----------------------------------------------------------

    @staticmethod
    def sort_by_time(tasks: List[Tuple[Pet, Task]]) -> List[Tuple[Pet, Task]]:
        """Return a new list of (pet, task) pairs ordered from earliest to latest start time."""
        return sorted(tasks, key=lambda pt: pt[1].start_time)

    @staticmethod
    def sort_by_priority(tasks: List[Tuple[Pet, Task]]) -> List[Tuple[Pet, Task]]:
        """Return a new list ordered high → low priority, breaking ties by earlier start time."""
        return sorted(
            tasks, key=lambda pt: (PRIORITY_RANK[pt[1].priority], pt[1].start_time)
        )

    def todays_schedule(self) -> List[Tuple[Pet, Task]]:
        """Pick pending tasks by priority until the time budget is used, then order them by time."""
        chosen: List[Tuple[Pet, Task]] = []
        minutes_used = 0
        for pet, task in self.sort_by_priority(self.get_tasks(completed=False)):
            if minutes_used + task.duration_minutes <= self.owner.available_minutes:
                chosen.append((pet, task))
                minutes_used += task.duration_minutes
        return self.sort_by_time(chosen)

    def skipped_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return pending tasks left out of today's schedule because the time budget ran out."""
        scheduled = {id(t) for _, t in self.todays_schedule()}
        return [(p, t) for p, t in self.get_tasks(completed=False) if id(t) not in scheduled]

    def find_conflicts(self) -> List[Tuple[Tuple[Pet, Task], Tuple[Pet, Task]]]:
        """Return pairs of scheduled tasks whose time windows overlap, including across pets."""
        schedule = self.todays_schedule()
        conflicts = []
        for i, (pet_a, a) in enumerate(schedule):
            a_start = a.start_time.hour * 60 + a.start_time.minute
            for pet_b, b in schedule[i + 1:]:
                b_start = b.start_time.hour * 60 + b.start_time.minute
                if a_start < b.end_minute and b_start < a.end_minute:
                    conflicts.append(((pet_a, a), (pet_b, b)))
        return conflicts

    # --- Managing ------------------------------------------------------------

    def mark_task_complete(self, pet_name: str, description: str) -> bool:
        """Find a pet's task by description and mark it done; return False if either is missing."""
        pet = self.owner.find_pet(pet_name)
        task = pet.find_task(description) if pet else None
        if task is None:
            return False
        task.mark_complete()
        return True

    def reset_recurring_tasks(self) -> None:
        """Start a new day by marking daily tasks pending again; once/weekly tasks are unchanged."""
        for _, task in self.owner.get_all_tasks():
            if task.frequency == "daily":
                task.mark_incomplete()
