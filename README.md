# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🛠️ Implementation Summary

I built the core logic for PawPal+ in `pawpal_system.py` as four classes that build on each other:

- **`Task`** is a single care activity. I gave it a description, start time, duration, priority (low, medium or high), frequency (once, daily or weekly), a completed flag and a due date. It checks its own values when it's created, so a bad priority, a zero-minute task or a time like `"25:00"` is rejected right away.
- **`Pet`** stores a pet's name, species and age, along with its own list of tasks. I can add, find and remove tasks on each pet.
- **`Owner`** holds several pets and the number of minutes the owner has free today. Its `get_all_tasks()` method collects every task from every pet into one list of `(pet, task)` pairs.
- **`Scheduler`** is the "brain." I made it read all of its data through `Owner.get_all_tasks()` instead of from any single pet, so every pet is always included. From that list it can:
  - filter tasks by pet or status
  - sort them by time or priority
  - build today's schedule by keeping the highest-priority tasks that fit the time budget, then ordering them by start time
  - report the tasks that didn't fit
  - flag tasks whose times overlap, as readable warnings
  - mark tasks complete, and automatically add the next copy of daily and weekly tasks

Together, they work like this: `Owner` → `Pet` → `Task` holds the data, and `Scheduler` sits on top of `Owner` and makes the decisions. `main.py` is my terminal testing ground. It creates an owner with two pets and eight tasks (added out of order on purpose), completes a few of them, and prints each sorted and filtered view, then today's schedule and any conflicts. `tests/test_pawpal.py` has 25 tests covering every feature in the Smarter Scheduling section below.

## 🖥️ Sample Output

Output from running `python main.py` (the end of it, after the sorted and filtered lists):

```
🐾 Today's Schedule for Jordan
============================================================
Time   Pet     Task                  Length   Priority
------------------------------------------------------------
07:30  Mochi   Morning walk          30 min   high
07:30  Mochi   Flea treatment        5 min    high
08:15  Luna    Thyroid medication    5 min    high
08:15  Mochi   Brush teeth           10 min   medium
18:00  Mochi   Dinner                10 min   high
------------------------------------------------------------
Total: 60 of 90 available minutes

Conflicts:
  ⚠️  Conflict (same pet: Mochi): 'Morning walk' 07:30-08:00 and 'Flea treatment' 07:30-07:35 start at the same time.
  ⚠️  Conflict (Luna & Mochi): 'Thyroid medication' 08:15-08:20 and 'Brush teeth' 08:15-08:25 start at the same time.
```

Jordan has 90 minutes free today. Breakfast, Brush fur and Fetch in the yard were already marked done, so they're not on the plan, and the new copies of Breakfast (tomorrow) and Brush fur (next week) aren't due yet. The scheduler fit every remaining task into 60 minutes, listed them by start time, and warned me about the two clashes I added on purpose.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.8.8, pytest-8.3.5, pluggy-1.5.0
collected 25 items

tests/test_pawpal.py .........................                           [100%]

============================== 25 passed in 0.02s ==============================
```

## 📐 Smarter Scheduling

After the basic scheduler worked, I added four features that make PawPal+ more useful for a real pet owner. They all live on the `Scheduler` and `Task` classes in `pawpal_system.py`. Each method has a docstring explaining its inputs, its output and its edge cases, and each feature has its own tests in `tests/test_pawpal.py`.

| Feature | Method(s) | What it does |
| --- | --- | --- |
| Sorting by time | `Scheduler.sort_by_time()`, `parse_time()` | Orders tasks by due date, then start time, with fixed tie-breakers |
| Filtering | `Scheduler.get_tasks(pet_name, completed)`, `Scheduler.due_tasks()` | Narrows tasks by pet, by done or pending, and by due date |
| Conflict detection | `Scheduler.find_conflicts()`, `Scheduler.conflict_warnings()` | Finds overlapping tasks and returns warning messages instead of crashing |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.mark_task_complete()` | Completing a daily or weekly task adds its next copy automatically |

### 1. Sorting tasks by time

**Methods:** `Scheduler.sort_by_time()` and the helper `parse_time()`

I wanted the task list to read like a timeline, no matter what order I typed the tasks in. `sort_by_time()` uses Python's `sorted()` with a `lambda` as the sort key:

```python
key=lambda pt: (pt[1].due_date, pt[1].start_time, PRIORITY_RANK[pt[1].priority], pt[0].name)
```

Each item is a `(pet, task)` pair, so `pt[1]` is the task and `pt[0]` is the pet. Python compares tuples one field at a time, so the key works like this:

1. **Due date** decides first, so tomorrow's 08:00 Breakfast comes after all of today's tasks instead of in the middle of them.
2. **Start time** orders tasks within a day.
3. **Priority** breaks ties when two tasks start at the same minute, so the high-priority one is listed first.
4. **Pet name** breaks any remaining tie, so the order is the same every time I run it.

`sort_by_time()` returns a **new** list and never changes the one I pass in.

I also made `Task` accept start times as `"HH:MM"` strings. `parse_time()` turns `"7:30"` or `"07:30"` into a real `datetime.time` when the task is created, and raises a clear `ValueError` for input like `"25:00"`, `"7.30"` or `"noon"`. I did it this way because sorting the raw strings is risky. `"07:30"` and `"18:00"` sort correctly as text, but without the leading zero, `"10:00"` sorts *before* `"7:30"`, because `"1"` comes before `"7"`. Turning every time into a `time` object once, up front, means the sort can never get that wrong.

The Streamlit task table and the schedule both use this ordering.

### 2. Filtering by pet or status

**Methods:** `Scheduler.get_tasks(pet_name=None, completed=None)` and `Scheduler.due_tasks(today=None)`

`get_tasks()` is how I narrow down the full task list. It reads every task from every pet through `Owner.get_all_tasks()` and keeps only the ones that pass the filters I give it:

- `pet_name="Mochi"` keeps only Mochi's tasks. Matching ignores upper and lower case and extra spaces, so `"mochi"` and `" MOCHI "` both work. An unknown name returns an empty list instead of an error.
- `completed=True` keeps only finished tasks, and `completed=False` keeps only pending ones.
- I can combine both filters, for example `get_tasks("Luna", completed=False)` for Luna's to-do list. Any filter I leave as `None` is skipped, so `get_tasks()` with no arguments returns everything.

Both filters are checked in a single pass over the list, inside one list comprehension.

`due_tasks()` adds a filter by date. It returns pending tasks whose `due_date` is today or earlier. That keeps overdue tasks on the list until they're done, and leaves out future copies of recurring tasks until their day comes. `todays_schedule()`, `skipped_tasks()` and `find_conflicts()` all start from `due_tasks()`, so tomorrow's walk never shows up in today's plan.

In `main.py` I print every filter: all tasks, Mochi only, completed only, and Luna's pending tasks. In the app, the "Mark a task done" dropdown uses `get_tasks(completed=False)`.

### 3. Conflict detection

**Methods:** `Scheduler.find_conflicts()` and `Scheduler.conflict_warnings()`, with the helpers `Task.start_minute`, `Task.end_minute` and `Task.time_window()`

One owner can't do two things at once, so I wanted PawPal+ to warn me when two tasks on today's plan overlap. That includes two tasks for the **same pet** and tasks for **different pets**.

**How the overlap check works.** I turn every start time into minutes after midnight, so 07:30 becomes 450, and each task's end is its start plus its duration. Two tasks overlap when *each one starts before the other one ends*. That rule catches exact matches, like two tasks both at 08:15, and partial overlaps, like a 07:45 breakfast in the middle of a 07:30–08:00 walk. It does **not** flag back-to-back tasks: a walk ending at 08:00 and a breakfast starting at 08:00 are fine.

**How `find_conflicts()` finds them.** I used a lightweight sort-then-sweep:

1. Sort today's scheduled tasks by start time.
2. Walk through them in order while keeping a short "running" list of earlier tasks that haven't finished yet.
3. For each new task, drop anything from the running list that has already ended. Whatever is left overlaps the new task, so each of those is a conflict.
4. Add the new task to the running list and move on.

Because the list is sorted, a task that has ended can never overlap anything later, so it's safe to drop it. The method returns `(earlier task, later task)` pairs. A long task that overlaps several short ones, like a two-hour hike, is reported once for each.

**Warnings instead of crashes.** `conflict_warnings()` turns each pair into a sentence that says which pet or pets are involved, gives both tasks' time windows, and says whether they start at the same time or only partly overlap:

```
⚠️  Conflict (same pet: Mochi): 'Morning walk' 07:30-08:00 and 'Flea treatment' 07:30-07:35 start at the same time.
⚠️  Conflict (Luna & Mochi): 'Thyroid medication' 08:15-08:20 and 'Brush teeth' 08:15-08:25 start at the same time.
```

Nothing is ever raised. If there are no conflicts, the method returns an empty list, so the caller just prints whatever comes back. `main.py` prints these lines under the schedule, and the Streamlit app shows each one as a red warning after "Generate schedule."

**What it doesn't do.** It reports conflicts but doesn't fix them, because I want the owner to decide what to move. It only checks tasks on today's plan, so completed tasks, tasks skipped for time and future recurring copies are ignored.

### 4. Recurring tasks

**Methods:** `Task.next_occurrence()` and `Scheduler.mark_task_complete()`, plus the `Task.due_date` field and `Pet.find_task(..., pending_only=True)`

Pet care repeats: Luna needs breakfast every day and her fur brushed every week. I didn't want to re-enter those tasks every time, so when a daily or weekly task is marked complete, PawPal+ automatically creates the next one.

- **Every task has a `due_date`.** It defaults to the day the task was created.
- **`Task.next_occurrence(today)`** builds the next copy. It uses Python's `timedelta` to move the date forward: `timedelta(days=1)` for daily tasks and `timedelta(weeks=1)` for weekly ones. `timedelta` does real calendar math, so January 31 + 1 day is February 1, and December 29 + 1 week is January 5 of the next year. The copy keeps the same description, time, duration, priority and frequency, and starts out pending. A `"once"` task returns `None`, because it doesn't come back.
- **The new date counts from today, or from the old due date if that is later.** If I finish a daily task three days late, the next one is due tomorrow, not two days ago. That way a task I'm catching up on isn't immediately overdue again.
- **`Scheduler.mark_task_complete(pet_name, description)`** ties it together. It finds the pet's **pending** task with that description, marks it done, and adds the next copy to the same pet. The finished task stays on the list as history. Because only the pending copy is matched, calling it again on the same task completes the new copy rather than the old one. It returns `False`, without raising an error, if the pet or task doesn't exist.

Here is what that looks like in `main.py`:

| I marked complete | Frequency | Result |
| --- | --- | --- |
| Luna's Breakfast | daily | New pending Breakfast due **tomorrow** |
| Luna's Brush fur | weekly | New pending Brush fur due **in 7 days** |
| Mochi's Fetch in the yard | once | Marked done, no new copy |

In the Streamlit app, I added a **Mark a task done** form. After you click it, the app tells you when the next copy is due, for example "Done! Next 'Morning walk' for Mochi is due Sun Oct 04." The task table also has a **Due** column, so you can see the new copies lined up.

### How I tested it

`tests/test_pawpal.py` has 25 tests, and `python -m pytest` runs them all. Beyond the two starter tests, they cover:

- **Sorting:** times given as strings are parsed correctly, bad times are rejected, and tasks sort by time with the priority tie-breaker.
- **Filtering:** pet names match regardless of case, and the pet and status filters work together. An unknown pet returns an empty list.
- **Recurring tasks:** the daily and weekly next dates, no copy for `"once"` tasks, dates that cross a month or a year, a task finished late, completing the same task twice in a row, and tomorrow's copy staying off today's schedule.
- **Conflicts:** the same time for different pets, the same time for the same pet, a partial overlap, back-to-back tasks (no conflict), one long task overlapping two short ones, and completed or future tasks being ignored.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** _(optional)_: <!-- Insert a screenshot or link to a demo video here -->
