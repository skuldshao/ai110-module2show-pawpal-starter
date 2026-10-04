"""Core classes for PawPal+: Task, Pet, Owner, and Scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Tuple, Union

# Lower rank sorts first, so "high" priority tasks come before "low" ones.
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = ("once", "daily", "weekly")
# How far after the previous one the next copy of a recurring task is due.
# timedelta does real calendar math, so Jan 31 + 1 day is Feb 1 and Dec 31 rolls into the new year.
RECURRENCE_STEP = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


def parse_time(value: Union[time, str]) -> time:
    """Convert a start time given as a time object or an "HH:MM" string into a time object.

    Args:
        value: A datetime.time (returned unchanged) or a string such as "07:30" or "7:30".

    Returns:
        The matching datetime.time.

    Raises:
        ValueError: If value is not a time and not a valid 24-hour "HH:MM" string
            (for example "25:00", "7.30", "noon", or None).
    """
    if isinstance(value, time):
        # already a time object (e.g. from st.time_input); nothing to do
        return value
    try:
        # strptime accepts "7:30" as well as "07:30" and rejects "25:00" or "7.30".
        return datetime.strptime(value.strip(), "%H:%M").time()
    except (AttributeError, ValueError):
        # AttributeError: value isn't a string at all (e.g. None or an int).
        raise ValueError(
            f"start_time must be a time or an 'HH:MM' string, got {value!r}")


@dataclass
class Task:
    """A single pet care activity scheduled at a time of day."""

    description: str
    start_time: time  # also accepts an "HH:MM" string, converted in __post_init__
    duration_minutes: int = 15
    priority: str = "medium"  # "low", "medium", or "high"
    frequency: str = "once"  # "once", "daily", or "weekly"
    completed: bool = False
    # default_factory runs date.today() each time a Task is created, not once at import.
    due_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Normalize start_time and validate priority, frequency, and duration."""
        # Store every start time as a time object so sorting never compares strings.
        self.start_time = parse_time(self.start_time)
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    @property
    def start_minute(self) -> int:
        """Return the start time as minutes after midnight (07:30 -> 450), used for overlap math."""
        # Plain integers make overlap checks simple: 07:30 -> 450, 08:15 -> 495.
        return self.start_time.hour * 60 + self.start_time.minute

    @property
    def end_minute(self) -> int:
        """Return the end time as minutes after midnight (start_minute + duration_minutes).

        This can be 1440 or more for a task that runs past midnight.
        """
        return self.start_minute + self.duration_minutes

    def time_window(self) -> str:
        """Return the task's start and end time as text, e.g. "08:00-08:30".

        Used in conflict warnings. An end time past midnight wraps around, so a 23:50
        task lasting 20 minutes shows "23:50-00:10".
        """
        end = self.end_minute % (
            24 * 60)  # wrap past midnight so 23:50 + 20 min shows 00:10
        # end // 60 is the hour and end % 60 the minute; :02d zero-pads them, so 8 -> "08".
        return f"{self.start_time:%H:%M}-{end // 60:02d}:{end % 60:02d}"

    def mark_complete(self) -> None:
        """Mark this task as done so it is excluded from the pending schedule."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as not done so it appears in the schedule again."""
        self.completed = False

    def next_occurrence(self, today: Optional[date] = None) -> Optional[Task]:
        """Build the next occurrence of a recurring task.

        A daily task comes back one day later and a weekly task seven days later
        (see RECURRENCE_STEP). The next date counts from today, or from the current due
        date if that is later, so a task finished late isn't immediately overdue again.

        Args:
            today: The date to count from. Defaults to date.today(); tests pass a fixed date.

        Returns:
            A new, pending Task with the same description, time, duration, priority, and
            frequency and the new due_date, or None if this task's frequency is "once".
        """
        step = RECURRENCE_STEP.get(self.frequency)
        if step is None:
            return None  # "once" tasks don't come back
        base = max(self.due_date, today or date.today())
        # replace() copies every field (time, duration, priority, ...) except the ones given.
        return replace(self, due_date=base + step, completed=False)


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

    def find_task(self, description: str, pending_only: bool = False) -> Optional[Task]:
        """Find one of this pet's tasks by its description.

        Args:
            description: The exact task description to look for.
            pending_only: If True, skip completed tasks. Recurring tasks leave completed
                copies behind, so this finds the copy that still needs doing.

        Returns:
            The first matching Task, or None if there isn't one.
        """
        return next(
            (
                t
                for t in self.tasks
                if t.description == description and not (pending_only and t.completed)
            ),
            None,
        )


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
        """Return the first pet with this name, or None if the owner has no such pet.

        Matching ignores case and surrounding spaces, the same as Scheduler.get_tasks().
        """
        wanted = name.strip().lower()
        return next((p for p in self.pets if p.name.lower() == wanted), None)

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
        """Return tasks from all of the owner's pets, optionally filtered by pet and/or status.

        Both filters can be combined. A filter left as None is not applied, so get_tasks()
        with no arguments returns every task.

        Args:
            pet_name: Keep only this pet's tasks. Matching ignores case and surrounding spaces.
            completed: True keeps only completed tasks, False only pending ones.

        Returns:
            A list of (pet, task) pairs in the order the pets and tasks were added.
        """
        # Lowercase once up front so "luna", " Luna" and "LUNA" all match the pet "Luna".
        wanted_pet = pet_name.strip().lower() if pet_name is not None else None
        # Single pass: a task is kept only if it passes every filter that was given.
        return [
            (p, t)
            for p, t in self.owner.get_all_tasks()
            if (wanted_pet is None or p.name.lower() == wanted_pet)
            and (completed is None or t.completed == completed)
        ]

    # --- Organizing ----------------------------------------------------------

    @staticmethod
    def sort_by_time(tasks: List[Tuple[Pet, Task]]) -> List[Tuple[Pet, Task]]:
        """Return the tasks in timeline order without changing the original list.

        Tasks are ordered by due date, then start time. Tasks at the same date and time are
        ordered by priority (high first), then by pet name, so the result is always the same.

        Args:
            tasks: (pet, task) pairs, for example from get_tasks().

        Returns:
            A new, sorted list of the same (pet, task) pairs.
        """
        # pt is a (pet, task) pair. Tuples compare element by element, so due_date decides
        # first, then start_time, and the later fields only break ties.
        return sorted(
            tasks,
            key=lambda pt: (
                pt[1].due_date,
                pt[1].start_time,
                PRIORITY_RANK[pt[1].priority],
                pt[0].name,
            ),
        )

    @staticmethod
    def sort_by_priority(tasks: List[Tuple[Pet, Task]]) -> List[Tuple[Pet, Task]]:
        """Return a new list ordered high → low priority, breaking ties by earlier start time."""
        return sorted(
            tasks, key=lambda pt: (
                PRIORITY_RANK[pt[1].priority], pt[1].start_time)
        )

    def due_tasks(self, today: Optional[date] = None) -> List[Tuple[Pet, Task]]:
        """Return the pending tasks that should be done today.

        Overdue tasks stay on the list until they are done; future copies of recurring
        tasks are left out until their day comes.

        Args:
            today: The day to plan for. Defaults to date.today().

        Returns:
            (pet, task) pairs for tasks that are not completed and have due_date <= today.
        """
        today = today or date.today()
        return [(p, t) for p, t in self.get_tasks(completed=False) if t.due_date <= today]

    def todays_schedule(self, today: Optional[date] = None) -> List[Tuple[Pet, Task]]:
        """Build today's plan from the tasks that are due.

        Tasks are taken from high to low priority, and each one is kept only if it still fits
        in the owner's available_minutes. This is a greedy choice: it never trades a
        higher-priority task for lower-priority ones that would fill the time better.

        Args:
            today: The day to plan for. Defaults to date.today().

        Returns:
            The chosen (pet, task) pairs, ordered by start time.
        """
        chosen: List[Tuple[Pet, Task]] = []
        minutes_used = 0
        # Greedy: take the most important due tasks first. A task that doesn't fit is
        # skipped, but we keep looking, since a shorter task further down might still fit.
        for pet, task in self.sort_by_priority(self.due_tasks(today)):
            if minutes_used + task.duration_minutes <= self.owner.available_minutes:
                chosen.append((pet, task))
                minutes_used += task.duration_minutes
        # Priority decided *what* gets done; time decides the order it's shown in.
        return self.sort_by_time(chosen)

    def skipped_tasks(self, today: Optional[date] = None) -> List[Tuple[Pet, Task]]:
        """Return the due tasks that didn't make today's plan because the time budget ran out.

        Args:
            today: The day to plan for. Defaults to date.today().

        Returns:
            (pet, task) pairs that are due but not in todays_schedule(today).
        """
        # Compare by id() so two different tasks with the same description aren't confused.
        scheduled = {id(t) for _, t in self.todays_schedule(today)}
        return [(p, t) for p, t in self.due_tasks(today) if id(t) not in scheduled]

    def find_conflicts(
        self, today: Optional[date] = None
    ) -> List[Tuple[Tuple[Pet, Task], Tuple[Pet, Task]]]:
        """Find every pair of tasks in today's plan whose time windows overlap.

        Covers tasks for the same pet and for different pets, since one owner can't do two
        things at once. Uses a sort-then-sweep: tasks are sorted by start time, and each one
        is compared only with earlier tasks that are still running when it starts. Tasks
        that touch end-to-start (08:00-08:15 and 08:15-08:30) do not count as a conflict.

        Args:
            today: The day to check. Defaults to date.today().

        Returns:
            A list of ((pet, task), (pet, task)) pairs, earlier task first. Empty if there
            are no conflicts.
        """
        # Sort by clock time only: overdue tasks have an earlier due_date but still happen today.
        schedule = sorted(self.todays_schedule(today),
                          key=lambda pt: pt[1].start_time)
        conflicts = []
        # Tasks that started earlier and may still be running when the next task begins.
        running: List[Tuple[Pet, Task]] = []
        for pet, task in schedule:
            # Drop tasks that finished by the time this one starts. Using > (not >=) means
            # back-to-back tasks, e.g. 8:00-8:15 and 8:15-8:30, don't clash.
            running = [(p, t)
                       for p, t in running if t.end_minute > task.start_minute]
            # Everything still running overlaps this task.
            conflicts.extend(((p, t), (pet, task)) for p, t in running)
            # This task may still be running when later tasks start, so check it against them too.
            # Dropping finished tasks is safe: the list is sorted, so later tasks start even later.
            running.append((pet, task))
        # The sweep only sees clock order, so a task running past midnight (23:50-00:10)
        # is never compared with early-morning tasks. Check that wrapped part separately.
        found = {(id(a), id(b)) for (_, a), (_, b) in conflicts}
        for late_pet, late in schedule:
            wrapped_end = late.end_minute - 24 * 60  # minutes it runs into the next morning
            if wrapped_end <= 0:
                continue
            for pet, task in schedule:
                if task is not late and task.start_minute < wrapped_end \
                        and (id(late), id(task)) not in found and (id(task), id(late)) not in found:
                    conflicts.append(((late_pet, late), (pet, task)))
        return conflicts

    def conflict_warnings(self, today: Optional[date] = None) -> List[str]:
        """Describe each conflict from find_conflicts() as a readable warning message.

        Conflicts are reported, never raised, so the caller can print or display the
        messages and carry on. Each message names the pet(s), both tasks, their time
        windows, and whether they start at the same time or only partly overlap.

        Args:
            today: The day to check. Defaults to date.today().

        Returns:
            One warning string per conflicting pair, or an empty list if there are none.
        """
        warnings = []
        for (pet_a, a), (pet_b, b) in self.find_conflicts(today):
            # "is" checks for the same Pet object, so two different pets that share a name
            # are still reported as two pets.
            who = f"same pet: {pet_a.name}" if pet_a is pet_b else f"{pet_a.name} & {pet_b.name}"
            # Say whether it's an exact clash or one task starting partway through another.
            how = "start at the same time" if a.start_time == b.start_time else "overlap"
            # Build a message instead of raising, so callers just print it and keep going.
            warnings.append(
                f"⚠️  Conflict ({who}): '{a.description}' {a.time_window()} and "
                f"'{b.description}' {b.time_window()} {how}."
            )
        return warnings

    # --- Managing ------------------------------------------------------------

    def mark_task_complete(
        self, pet_name: str, description: str, today: Optional[date] = None
    ) -> bool:
        """Mark a pet's pending task done and, if it repeats, add its next occurrence.

        The completed task stays on the pet as history. For a daily or weekly task, a new
        pending copy from Task.next_occurrence() is added to the same pet.

        Args:
            pet_name: The pet the task belongs to.
            description: The task's description. Only a pending task with this description
                is matched, so calling this again completes the next copy.
            today: The date the task was done. Defaults to date.today().

        Returns:
            True if a task was completed, False if the pet or a pending task wasn't found.
        """
        pet = self.owner.find_pet(pet_name)
        # Only look up the task if the pet exists; either lookup failing returns False.
        task = pet.find_task(description, pending_only=True) if pet else None
        if task is None:
            return False
        task.mark_complete()
        # The completed task stays as history; daily/weekly tasks get a fresh pending copy.
        next_task = task.next_occurrence(today)
        if next_task is not None:
            pet.add_task(next_task)
        return True
