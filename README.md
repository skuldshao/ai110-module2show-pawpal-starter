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

Together, they work like this: `Owner` → `Pet` → `Task` holds the data, and `Scheduler` sits on top of `Owner` and makes the decisions. `main.py` is my terminal testing ground. It creates an owner with two pets and eight tasks (added out of order on purpose), completes a few of them, and prints each sorted and filtered view, then today's schedule and any conflicts. `tests/test_pawpal.py` has 44 tests covering every feature in the Smarter Scheduling section below, plus edge cases like empty data and tasks that run past midnight.

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

### How to run the tests

From the project folder, with the virtual environment active, I run:

```bash
python -m pytest
```

That finds and runs every test in `tests/test_pawpal.py`. If I want to see each test's name as it runs, I add `-v`:

```bash
python -m pytest -v
```

### What my tests cover

I have **44 tests** in `tests/test_pawpal.py`. Before I wrote them, I listed the five behaviors PawPal+ can't get wrong, then wrote at least one "happy path" test for each (the normal case works) and several edge-case tests (empty data, ties, boundaries, odd dates).

**1. Sorting (tasks come back in chronological order)**
- Tasks I add out of order come back sorted by time. When two tasks start at the same minute, the high-priority one comes first.
- `sort_by_priority()` puts high before medium before low, and breaks ties by earlier start time.
- Sorting an empty list returns an empty list instead of crashing.
- An overdue task from yesterday is listed before today's tasks, because due date is the first sort key.
- Times given as strings (`"7:05"`, `"19:45"`) turn into real times, and bad ones (`"25:00"`, `"7.30"`, `"noon"`, `""`) are rejected.

**2. Recurring tasks (finishing a daily task creates tomorrow's copy)**
- Marking a daily task complete keeps the finished one as history and adds a new pending copy due the next day. That copy stays off today's schedule and shows up on tomorrow's.
- Daily tasks move forward 1 day and weekly tasks 7 days, including across a month (Jan 31 → Feb 1) and a year (Dec 29 → Jan 5).
- A task I finish three days late is next due tomorrow, not in the past. A weekly task I finish early is next due a week after its *original* due date.
- A `"once"` task doesn't come back.
- Completing the same task twice in a row completes the new copy, not the old one.
- Asking to complete a task for a pet or task that doesn't exist returns `False` instead of crashing.

**3. Conflict detection (flagging duplicate and overlapping times)**
- Two tasks at the exact same time are flagged, whether they're for the same pet or for different pets, and the warning says "start at the same time."
- A partial overlap (a 07:45 breakfast during a 07:30–08:00 walk) is flagged, and the warning shows both full time windows.
- Back-to-back tasks (one ends at 08:00, the next starts at 08:00) are **not** a conflict.
- One long task overlapping two short ones is reported twice, and three tasks at the same time give all three pairs.
- Completed tasks, future copies and tasks skipped because time ran out are never reported as conflicts.
- A task that runs past midnight (23:50–00:10) is flagged against one at 00:05.

**4. Building today's plan within the time budget**
- Tasks that exactly fill the available minutes are all kept.
- If a task doesn't fit, it's skipped, but a shorter, lower-priority task after it can still fit. `skipped_tasks()` returns exactly the ones left out.
- With 0 minutes available, the plan is empty and everything is reported as skipped.
- `due_tasks()` includes overdue tasks and leaves out future and completed ones.

**5. Filtering, empty data and validation**
- Filtering by pet name ignores case, and the pet and status filters work together. An unknown pet gives an empty list.
- An owner with no pets, and a pet with no tasks, both get empty results from every scheduler method, with no errors.
- A task with a bad priority, a bad frequency or a zero or negative duration is rejected when it's created.
- `remove_task()` removes every task with that description, including completed history copies.

### Bugs my tests caught

Two of my edge-case tests failed at first, and in both cases the bug was in `pawpal_system.py`, not in the test:

1. **Pet names were case-sensitive in one place.** `get_tasks("mochi")` found Mochi, but `mark_task_complete("mochi", ...)` didn't, because `Owner.find_pet()` compared names exactly. I made `find_pet()` ignore case and extra spaces, like `get_tasks()` does.
2. **Overlaps across midnight were missed.** `find_conflicts()` compares tasks in clock order, so a 23:50 task lasting 20 minutes was never compared with a 00:05 task, even though they overlap. I added a check for the part of a task that runs past midnight.

I kept both tests in the suite so these bugs can't sneak back in.

### Test results

Output from `python -m pytest`:

```
============================= test session starts ==============================
platform darwin -- Python 3.8.8, pytest-6.2.3, py-1.10.0, pluggy-0.13.1
rootdir: /Users/skuldshao/Desktop/New/ai110-module2show-pawpal-starter
plugins: anyio-4.5.2
collected 44 items

tests/test_pawpal.py ............................................        [100%]

============================== 44 passed in 0.03s ==============================
```

### Confidence level: ⭐⭐⭐⭐☆ (4 out of 5)

I'm confident in the scheduling logic itself. All 44 tests pass, every core behavior has both happy-path and edge-case tests, and writing those tests found and fixed two real bugs. I pinned the date in the date-based tests, so they give the same result no matter what day I run them.

I'm not giving it 5 stars, for these reasons:

- **The Streamlit UI isn't tested automatically.** My tests check `pawpal_system.py`, but I've only checked `app.py` by clicking through it by hand.
- **The scheduler is greedy, not optimal.** It always takes the highest-priority task that fits, so it sometimes leaves time unused that a different mix of lower-priority tasks could fill. The tests confirm it behaves the way I designed it, but that design has limits.
- **It plans one day at a time.** It doesn't plan ahead across a week, and it only reports conflicts without suggesting a fix.
- **Nothing is saved.** Tasks live in memory, so there's nothing yet to test around saving and loading data.

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

**What it doesn't do.** It reports conflicts but doesn't fix them, because I want the owner to decide what to move. It only checks tasks on today's plan, so completed tasks, tasks skipped for time and future recurring copies are ignored. It does handle a late-night task that runs past midnight: a 23:50–00:10 task is still flagged against one at 00:05.

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

Every feature above has its own tests. See [Testing PawPal+](#-testing-pawpal) for the full list and the latest results.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** _(optional)_: <!-- Insert a screenshot or link to a demo video here -->
