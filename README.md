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

`requirements.txt` includes `tabulate` and `wcwidth`, which `main.py` uses for its terminal tables (see [Output Formatting](#-output-formatting)).

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
- **`Owner`** holds several pets and the number of minutes the owner has free today. Its `get_all_tasks()` method collects every task from every pet into one list of `(pet, task)` pairs. It can also save itself, with all pets and tasks, to `data.json` and load back from it.
- **`Scheduler`** is the "brain." I made it read all of its data through `Owner.get_all_tasks()` instead of from any single pet, so every pet is always included. From that list it can:
  - filter tasks by pet or status
  - sort them by time or priority
  - build today's schedule by keeping the highest-priority tasks that fit the time budget, then ordering them by start time or by priority
  - report the tasks that didn't fit
  - flag tasks whose times overlap, as readable warnings
  - find the next free time slot that fits a task of a given length
  - mark tasks complete, and automatically add the next copy of daily and weekly tasks

Together, they work like this: `Owner` → `Pet` → `Task` holds the data, and `Scheduler` sits on top of `Owner` and makes the decisions. `main.py` is my terminal testing ground. It creates an owner with two pets and eight tasks (added out of order on purpose), completes a few of them, and prints each sorted and filtered view, then today's schedule, any conflicts, a priority-first view and some free slots. `formatting.py` holds the emoji, badge and color helpers that `main.py` and `app.py` share. `tests/test_pawpal.py` and `tests/test_formatting.py` have 92 tests covering every feature below, plus edge cases like empty data and tasks that run past midnight.

## ✨ Features

Every feature below is a method on `Task` or `Scheduler` in `pawpal_system.py`, and each one is covered by tests in `tests/test_pawpal.py`.

- **Sorting by time.** `Scheduler.sort_by_time()` orders tasks by due date, then start time, then priority (high first), then pet name. So the list reads like a timeline, and ties always come out in the same order. Start times are turned into real `time` objects by `parse_time()` when a task is created, so `"10:00"` never sorts before `"7:30"`.
- **Priority-based scheduling.** Every task has a priority (low, medium or high; `"High"` and `"HIGH"` work too). `Scheduler.sort_by_priority()` sorts by priority first, then by time (due date, then start time), with pet name as the last tie-breaker. The scheduler uses this order to decide which tasks fit in the time budget, and `todays_schedule(order="priority")` lists the plan most-important-first. See [Priority-based scheduling](#6-priority-based-scheduling).
- **Filtering by pet and status.** `Scheduler.get_tasks(pet_name, completed)` keeps only the tasks that pass every filter given, in one pass. Pet names ignore case and extra spaces, and an unknown pet gives an empty list instead of an error.
- **Due-date filtering.** `Scheduler.due_tasks()` keeps pending tasks due today or earlier. Overdue tasks stay on the list until they're done, and future copies of recurring tasks wait for their day.
- **Priority-first daily plan within a time budget.** `Scheduler.todays_schedule()` is a greedy algorithm. It takes due tasks from high to low priority and keeps each one that still fits in the owner's free minutes. If a long task doesn't fit, a shorter one further down the list can still be picked. The kept tasks are then shown in start-time order.
- **Skipped-task report.** `Scheduler.skipped_tasks()` lists the due tasks that didn't fit, so the owner can see what was left out and why.
- **Conflict warnings.** `Scheduler.find_conflicts()` sorts today's plan by start time, then walks through it with a list of the tasks still running, to find every pair whose times overlap. That covers the same pet or two different pets, and tasks that run past midnight. Back-to-back tasks don't count. `Scheduler.conflict_warnings()` turns each pair into a readable message instead of raising an error.
- **Next available slot.** `Scheduler.find_next_available_slot()` finds the earliest start time when a task of a given length fits into today's plan without overlapping anything, between an earliest and a latest time (06:00 to 22:00 by default). The app uses it to suggest conflict-free times when two tasks clash.
- **Daily and weekly recurrence.** `Scheduler.mark_task_complete()` marks the pending task done, keeps it as history, and adds the next copy from `Task.next_occurrence()`. That copy is due in 1 day for a daily task and in 7 days for a weekly one, using `timedelta`, so month and year boundaries are handled. If a task is finished late, the next copy counts from today, so it isn't overdue straight away.
- **Readable output.** Emojis for each task type (🦮 walk, 💊 meds, 🍖 food ...), 🔴🟡🟢 priority badges, ✅⏳❗📅 status badges, colored terminal text, a time-budget bar, and `tabulate` tables in the CLI. See [Output Formatting](#-output-formatting).
- **Saving between runs.** `Owner.save_to_json()` and `Owner.load_from_json()` store the owner, pets and tasks in `data.json`, so the app remembers everything after it's closed. See [Data Persistence](#-data-persistence).
- **Input validation.** `Task` rejects an unknown priority or frequency, a zero or negative duration, and a bad time like `"25:00"` as soon as it's created. The app shows these as error messages instead of crashing.

The final class diagram is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) ([PNG](diagrams/uml_final.png)).

## 🖥️ Sample Output

Output from running `python main.py` (the end of it, after the sorted and filtered lists):

```
🐾 Today's Schedule for Jordan
╭─────────────┬───────┬───────────────────────┬───────┬────────────┬─────────╮
│ Time        │ Pet   │ Task                  │   Min │ Priority   │ Clash   │
├─────────────┼───────┼───────────────────────┼───────┼────────────┼─────────┤
│ 07:30-08:00 │ Mochi │ 🦮 Morning walk       │    30 │ 🔴 high    │ ⚡      │
│ 07:30-07:35 │ Mochi │ 💊 Flea treatment     │     5 │ 🔴 high    │ ⚡      │
│ 08:15-08:20 │ Luna  │ 💊 Thyroid medication │     5 │ 🔴 high    │ ⚡      │
│ 08:15-08:25 │ Mochi │ 🦷 Brush teeth        │    10 │ 🟡 medium  │ ⚡      │
│ 18:00-18:10 │ Mochi │ 🍖 Dinner             │    10 │ 🔴 high    │         │
╰─────────────┴───────┴───────────────────────┴───────┴────────────┴─────────╯
Time budget  ████████████████████░░░░░░░░░░ 60/90 min (67%)

Conflicts (2):
  ⚠️  Conflict (same pet: Mochi): 'Morning walk' 07:30-08:00 and 'Flea treatment' 07:30-07:35 start at the same time.
  ⚠️  Conflict (Luna & Mochi): 'Thyroid medication' 08:15-08:20 and 'Brush teeth' 08:15-08:25 start at the same time.

⭐ Priority-first view of today's plan

Budget 90 min  ████████████████████░░░░░░░░░░ 60/90 min (67%)
╭─────┬────────────┬────────┬───────┬───────────────────────┬───────┬────────────╮
│   # │ Priority   │ Time   │ Pet   │ Task                  │   Min │ Plan       │
├─────┼────────────┼────────┼───────┼───────────────────────┼───────┼────────────┤
│   1 │ 🔴 high    │ 07:30  │ Mochi │ 🦮 Morning walk       │    30 │ ✅ planned │
│   2 │ 🔴 high    │ 07:30  │ Mochi │ 💊 Flea treatment     │     5 │ ✅ planned │
│   3 │ 🔴 high    │ 08:15  │ Luna  │ 💊 Thyroid medication │     5 │ ✅ planned │
│   4 │ 🔴 high    │ 18:00  │ Mochi │ 🍖 Dinner             │    10 │ ✅ planned │
│   5 │ 🟡 medium  │ 08:15  │ Mochi │ 🦷 Brush teeth        │    10 │ ✅ planned │
╰─────┴────────────┴────────┴───────┴───────────────────────┴───────┴────────────╯

Budget 50 min  ██████████████████████████████ 50/50 min (100%)
╭─────┬────────────┬────────┬───────┬───────────────────────┬───────┬────────────╮
│   # │ Priority   │ Time   │ Pet   │ Task                  │   Min │ Plan       │
├─────┼────────────┼────────┼───────┼───────────────────────┼───────┼────────────┤
│   1 │ 🔴 high    │ 07:30  │ Mochi │ 🦮 Morning walk       │    30 │ ✅ planned │
│   2 │ 🔴 high    │ 07:30  │ Mochi │ 💊 Flea treatment     │     5 │ ✅ planned │
│   3 │ 🔴 high    │ 08:15  │ Luna  │ 💊 Thyroid medication │     5 │ ✅ planned │
│   4 │ 🔴 high    │ 18:00  │ Mochi │ 🍖 Dinner             │    10 │ ✅ planned │
│   - │ 🟡 medium  │ 08:15  │ Mochi │ 🦷 Brush teeth        │    10 │ ❌ no time │
╰─────┴────────────┴────────┴───────┴───────────────────────┴───────┴────────────╯

🔎 Next free slots
╭──────────┬──────────────┬───────────╮
│ Length   │ Not before   │ Free at   │
├──────────┼──────────────┼───────────┤
│ 10 min   │ 07:00        │ 07:00     │
│ 45 min   │ 07:00        │ 08:25     │
│ 30 min   │ 18:00        │ 18:10     │
╰──────────┴──────────────┴───────────╯
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

I have **92 tests**: 68 in `tests/test_pawpal.py` for the scheduling logic and 24 in `tests/test_formatting.py` for the display helpers. Before I wrote the first set, I listed the five behaviors PawPal+ can't get wrong, then wrote at least one "happy path" test for each (the normal case works) and several edge-case tests (empty data, ties, boundaries, odd dates).

**1. Sorting (tasks come back in chronological order)**

- Tasks I add out of order come back sorted by time. When two tasks start at the same minute, the high-priority one comes first.
- `sort_by_priority()` puts high before medium before low, and breaks ties by earlier start time.
- Sorting an empty list returns an empty list instead of crashing.
- An overdue task from yesterday is listed before today's tasks, because due date is the first sort key.
- Times given as strings (`"7:05"`, `"19:45"`) turn into real times, and bad ones (`"25:00"`, `"7.30"`, `"noon"`, `""`) are rejected.

**2. Recurring tasks (finishing a daily task creates tomorrow's copy)**

- Marking a daily task complete keeps the finished one as history and adds a new pending copy due the next day. That copy stays off today's schedule and shows up on tomorrow's.
- Daily tasks move forward 1 day and weekly tasks 7 days, including across a month (Jan 31 → Feb 1) and a year (Dec 29 → Jan 5).
- A task I finish three days late is next due tomorrow, not in the past. A weekly task I finish early is next due a week after its _original_ due date.
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

**6. Next available slot**

- With nothing planned, the slot is the earliest allowed time (06:00, or whatever `earliest` I pass).
- Busy time is skipped, and a slot can start exactly when the previous task ends.
- A gap that's too short is skipped in favor of the next one that fits, and nothing is offered inside a long task.
- It returns `None` when nothing fits before `latest`.
- Completed tasks don't block a slot, and `ignore` leaves out the task being moved.
- A task running past midnight blocks the early morning.
- A task placed at the returned time creates no conflicts.
- A zero duration is rejected.

**8. Priority-based scheduling**

- `"High"`, `"HIGH"` and `" high "` are all accepted and stored as `"high"`.
- Sorting by priority puts high before medium before low. Within a priority, an overdue task comes before today's, then earlier start times come first, then pet names alphabetically. A low task at 06:00 still comes after a high task at 20:00.
- `todays_schedule(order="priority")` lists the plan high → low, and `order="time"` lists it as a timeline. Both contain exactly the same tasks, because the order only changes how the plan is shown, not what's in it.
- An unknown order like `"alphabetical"` raises `ValueError`.

**9. Output formatting** (`tests/test_formatting.py`)
- Each task type gets the right emoji, with tricky cases: "Brush teeth" gets 🦷 but "Brush fur" gets 🧼, "Flea treatment" is medicine and not a food treat, and "Brunch" doesn't count as a walk.
- Priority badges use the traffic-light dots, and status is done, overdue, due today or upcoming. A finished task is "done" even if it was late.
- Colors are only added when they're turned on. They're off when output goes to a file or `NO_COLOR` is set.
- A tabulate table with emojis and colors has the same visible width on every line, so the borders line up.
- The budget bar draws correctly for full, empty and zero-minute budgets (no division by zero).

**7. Saving and loading (persistence)**

- Saving and loading gives back an owner equal to the original, field by field, including completed tasks, recurring copies and due dates.
- The loaded owner produces the same schedule and the same conflicts.
- The file stores times as `"07:30"` and dates as `"2026-01-31"`, and no temporary file is left behind.
- Saving again replaces the old data.
- Loading a file that doesn't exist returns `None`. Broken JSON, missing fields and bad values (like `"25:00"`) all raise `ValueError`.

### Bugs my tests caught

Two of my edge-case tests failed at first, and in both cases the bug was in `pawpal_system.py`, not in the test:

1. **Pet names were case-sensitive in one place.** `get_tasks("mochi")` found Mochi, but `mark_task_complete("mochi", ...)` didn't, because `Owner.find_pet()` compared names exactly. I made `find_pet()` ignore case and extra spaces, like `get_tasks()` does.
2. **Overlaps across midnight were missed.** `find_conflicts()` compares tasks in clock order, so a 23:50 task lasting 20 minutes was never compared with a 00:05 task, even though they overlap. I added a check for the part of a task that runs past midnight.

I kept both tests in the suite so these bugs can't sneak back in.

### Test results

Output from `python -m pytest`:

```
============================= test session starts ==============================
platform darwin -- Python 3.8.8, pytest-8.3.5, pluggy-1.5.0
rootdir: /Users/skuldshao/Desktop/New/ai110-module2show-pawpal-starter
collected 92 items

tests/test_formatting.py ........................                        [ 26%]
tests/test_pawpal.py ................................................... [ 81%]
.................                                                        [100%]

============================== 92 passed in 0.07s ==============================
```

### Confidence level: ⭐⭐⭐⭐☆ (4 out of 5)

I'm confident in the scheduling logic itself. All 92 tests pass, every core behavior has both happy-path and edge-case tests, and writing those tests found and fixed two real bugs. I pinned the date in the date-based tests, so they give the same result no matter what day I run them.

I'm not giving it 5 stars, for these reasons:

- **The Streamlit UI isn't tested automatically.** My tests check `pawpal_system.py`, but I've only checked `app.py` by clicking through it by hand.
- **The scheduler is greedy, not optimal.** It always takes the highest-priority task that fits, so it sometimes leaves time unused that a different mix of lower-priority tasks could fill. The tests confirm it behaves the way I designed it, but that design has limits.
- **It plans one day at a time.** It doesn't plan ahead across a week, and it never moves conflicting tasks on its own. The app suggests a free start time for a conflicting task, but the owner still has to move it.
- **Saving is simple.** Data is saved to one local `data.json` file. There's no support for several users, and if two browser tabs edit at once, the last save wins.

## 📐 Smarter Scheduling

After the basic scheduler worked, I added six features that make PawPal+ more useful for a real pet owner. They all live on the `Scheduler` and `Task` classes in `pawpal_system.py`. Each method has a docstring explaining its inputs, its output and its edge cases, and each feature has its own tests in `tests/test_pawpal.py`.

| Feature                   | Method(s)                                                              | What it does                                                                    |
| ------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Sorting by time           | `Scheduler.sort_by_time()`, `parse_time()`                             | Orders tasks by due date, then start time, with fixed tie-breakers              |
| Filtering                 | `Scheduler.get_tasks(pet_name, completed)`, `Scheduler.due_tasks()`    | Narrows tasks by pet, by done or pending, and by due date                       |
| Conflict detection        | `Scheduler.find_conflicts()`, `Scheduler.conflict_warnings()`          | Finds overlapping tasks and returns warning messages instead of crashing        |
| Recurring tasks           | `Task.next_occurrence()`, `Scheduler.mark_task_complete()`             | Completing a daily or weekly task adds its next copy automatically              |
| Next available slot       | `Scheduler.find_next_available_slot()`                                 | Finds the earliest free time that fits a task of a given length                 |
| Priority-based scheduling | `Scheduler.sort_by_priority()`, `Scheduler.todays_schedule(order=...)` | Sorts by priority first, then time, and uses that order to fill the time budget |

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

I also made `Task` accept start times as `"HH:MM"` strings. `parse_time()` turns `"7:30"` or `"07:30"` into a real `datetime.time` when the task is created, and raises a clear `ValueError` for input like `"25:00"`, `"7.30"` or `"noon"`. I did it this way because sorting the raw strings is risky. `"07:30"` and `"18:00"` sort correctly as text, but without the leading zero, `"10:00"` sorts _before_ `"7:30"`, because `"1"` comes before `"7"`. Turning every time into a `time` object once, up front, means the sort can never get that wrong.

The Streamlit task table and the schedule both use this ordering.

### 2. Filtering by pet or status

**Methods:** `Scheduler.get_tasks(pet_name=None, completed=None)` and `Scheduler.due_tasks(today=None)`

`get_tasks()` is how I narrow down the full task list. It reads every task from every pet through `Owner.get_all_tasks()` and keeps only the ones that pass the filters I give it:

- `pet_name="Mochi"` keeps only Mochi's tasks. Matching ignores upper and lower case and extra spaces, so `"mochi"` and `" MOCHI "` both work. An unknown name returns an empty list instead of an error.
- `completed=True` keeps only finished tasks, and `completed=False` keeps only pending ones.
- I can combine both filters, for example `get_tasks("Luna", completed=False)` for Luna's to-do list. Any filter I leave as `None` is skipped, so `get_tasks()` with no arguments returns everything.

Both filters are checked in a single pass over the list, inside one list comprehension.

`due_tasks()` adds a filter by date. It returns pending tasks whose `due_date` is today or earlier. That keeps overdue tasks on the list until they're done, and leaves out future copies of recurring tasks until their day comes. `todays_schedule()`, `skipped_tasks()` and `find_conflicts()` all start from `due_tasks()`, so tomorrow's walk never shows up in today's plan.

In `main.py` I print every filter: all tasks, Mochi only, completed only, and Luna's pending tasks. In the app, the task list has **Filter by pet** and **Filter by status** dropdowns that call `get_tasks()`, and the "Mark a task done" dropdown uses `get_tasks(completed=False)`.

### 3. Conflict detection

**Methods:** `Scheduler.find_conflicts()` and `Scheduler.conflict_warnings()`, with the helpers `Task.start_minute`, `Task.end_minute` and `Task.time_window()`

One owner can't do two things at once, so I wanted PawPal+ to warn me when two tasks on today's plan overlap. That includes two tasks for the **same pet** and tasks for **different pets**.

**How the overlap check works.** I turn every start time into minutes after midnight, so 07:30 becomes 450, and each task's end is its start plus its duration. Two tasks overlap when _each one starts before the other one ends_. That rule catches exact matches, like two tasks both at 08:15, and partial overlaps, like a 07:45 breakfast in the middle of a 07:30–08:00 walk. It does **not** flag back-to-back tasks: a walk ending at 08:00 and a breakfast starting at 08:00 are fine.

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

Nothing is ever raised. If there are no conflicts, the method returns an empty list, so the caller just prints whatever comes back. `main.py` prints these lines under the schedule. The Streamlit app shows them in a yellow warning above the schedule, marks the conflicting rows with ⚡, and suggests the next free start time for the later task (see [Next available slot](#5-next-available-slot)).

**What it doesn't do.** It reports conflicts but doesn't fix them, because I want the owner to decide what to move. The app only suggests a new time. It only checks tasks on today's plan, so completed tasks, tasks skipped for time and future recurring copies are ignored. It does handle a late-night task that runs past midnight: a 23:50–00:10 task is still flagged against one at 00:05.

### 4. Recurring tasks

**Methods:** `Task.next_occurrence()` and `Scheduler.mark_task_complete()`, plus the `Task.due_date` field and `Pet.find_task(..., pending_only=True)`

Pet care repeats: Luna needs breakfast every day and her fur brushed every week. I didn't want to re-enter those tasks every time, so when a daily or weekly task is marked complete, PawPal+ automatically creates the next one.

- **Every task has a `due_date`.** It defaults to the day the task was created.
- **`Task.next_occurrence(today)`** builds the next copy. It uses Python's `timedelta` to move the date forward: `timedelta(days=1)` for daily tasks and `timedelta(weeks=1)` for weekly ones. `timedelta` does real calendar math, so January 31 + 1 day is February 1, and December 29 + 1 week is January 5 of the next year. The copy keeps the same description, time, duration, priority and frequency, and starts out pending. A `"once"` task returns `None`, because it doesn't come back.
- **The new date counts from today, or from the old due date if that is later.** If I finish a daily task three days late, the next one is due tomorrow, not two days ago. That way a task I'm catching up on isn't immediately overdue again.
- **`Scheduler.mark_task_complete(pet_name, description)`** ties it together. It finds the pet's **pending** task with that description, marks it done, and adds the next copy to the same pet. The finished task stays on the list as history. Because only the pending copy is matched, calling it again on the same task completes the new copy rather than the old one. It returns `False`, without raising an error, if the pet or task doesn't exist.

Here is what that looks like in `main.py`:

| I marked complete         | Frequency | Result                                  |
| ------------------------- | --------- | --------------------------------------- |
| Luna's Breakfast          | daily     | New pending Breakfast due **tomorrow**  |
| Luna's Brush fur          | weekly    | New pending Brush fur due **in 7 days** |
| Mochi's Fetch in the yard | once      | Marked done, no new copy                |

In the Streamlit app, I added a **Mark a task done** form. After you click it, the app tells you when the next copy is due, for example "Done! Next 'Morning walk' for Mochi is due Sun Oct 04." The task table also has a **Due** column, so you can see the new copies lined up.

### 5. Next available slot

**Method:** `Scheduler.find_next_available_slot(duration_minutes, earliest="06:00", latest="22:00", today=None, ignore=None)`

Conflict warnings tell me _that_ two tasks clash, but I still had to work out where to move one. My first version of the app just suggested "start it when the earlier task ends", which could land right on top of a third task. This method answers the real question: _when is the next time I'm actually free for N minutes?_

**How it works.** It's another sweep, like `find_conflicts()`:

1. Collect today's busy windows from `todays_schedule()` as `(start, end)` minutes after midnight. A task that runs past midnight also blocks the start of the morning.
2. Sort the windows by start time and set the candidate start to `earliest`.
3. Walk through the windows. If the next window starts at or after `candidate + duration`, the gap is big enough, so stop. Otherwise push the candidate to the end of that window (if it's later) and keep going.
4. If the task still finishes by `latest`, return the candidate as a `time`; otherwise return `None`.

Because the windows are sorted, the first gap that's big enough is the earliest one, and one pass is enough. It uses the same rules as `find_conflicts()`: it only looks at tasks on today's plan, and back-to-back is allowed. So a task placed at the returned time never triggers a conflict warning (there's a test that checks exactly this).

The `ignore` argument leaves one task out of the busy time. The app passes the task it's suggesting a new time for, so the task doesn't block its own move.

**Example.** With Walk 07:00–07:30, Meds 07:40–07:45 and Brush 08:00–08:15:

| Task length | Next free slot from 07:00 | Why                                                    |
| ----------- | ------------------------- | ------------------------------------------------------ |
| 10 min      | 07:30                     | The 10-minute gap before Meds is just enough           |
| 15 min      | 07:45                     | Too long for that gap, but fits between Meds and Brush |
| 20 min      | 08:15                     | Neither gap is long enough, so it goes after Brush     |

**In the app.** Each conflict now ends with "💡 Next free slot for ...", found by searching from when the earlier task ends. There's also a **🔎 Find a free slot** box under today's schedule: enter a length and a time window, and it tells you the earliest free start time. `main.py` prints a few example slots at the end.

### 6. Priority-based scheduling

**Methods:** `Scheduler.sort_by_priority()`, `Scheduler.todays_schedule(today=None, order="time")`, and the `Task.priority` field

Sorting by time tells me _when_ things happen, but not what matters most. Every `Task` has a **priority**: `"low"`, `"medium"` or `"high"`. `Task.__post_init__` lowercases it, so `"High"` works too, and rejects anything else. `PRIORITY_RANK` turns it into a number for sorting (high = 0, medium = 1, low = 2).

**Priority first, then time.** `sort_by_priority()` uses the same kind of tuple key as `sort_by_time()`, with priority moved to the front:

```python
key=lambda pt: (PRIORITY_RANK[pt[1].priority], pt[1].due_date, pt[1].start_time, pt[0].name)
```

1. **Priority** decides first: every high task comes before every medium task, even a medium task that starts earlier in the day.
2. **Due date** comes next, so among high tasks an overdue one from yesterday is handled before today's.
3. **Start time** orders the rest of the tasks within a priority.
4. **Pet name** breaks any exact tie, so the order is the same every run.

My first version only used priority and start time. I added due date and pet name so that overdue tasks are taken first when time is short, and the order is always repeatable.

**How it drives the plan.** `todays_schedule()` walks through the due tasks in this order and keeps each one that still fits in the owner's available minutes. So when time is short, low-priority tasks are the ones that get dropped, never high ones (unless a high task is too long to fit). The new `order` argument chooses how the kept tasks are shown:

- `order="time"` (the default) is a timeline for the day.
- `order="priority"` is a "most important first" list.

The order doesn't change _which_ tasks are in the plan, only how they're listed. A test checks that both orders contain exactly the same tasks.

**CLI output.** `main.py` prints today's plan in time order, then the same plan in priority order with two time budgets. This is real output from `python main.py`:

```
🐾 Today's Schedule for Jordan
╭─────────────┬───────┬───────────────────────┬───────┬────────────┬─────────╮
│ Time        │ Pet   │ Task                  │   Min │ Priority   │ Clash   │
├─────────────┼───────┼───────────────────────┼───────┼────────────┼─────────┤
│ 07:30-08:00 │ Mochi │ 🦮 Morning walk       │    30 │ 🔴 high    │ ⚡      │
│ 07:30-07:35 │ Mochi │ 💊 Flea treatment     │     5 │ 🔴 high    │ ⚡      │
│ 08:15-08:20 │ Luna  │ 💊 Thyroid medication │     5 │ 🔴 high    │ ⚡      │
│ 08:15-08:25 │ Mochi │ 🦷 Brush teeth        │    10 │ 🟡 medium  │ ⚡      │
│ 18:00-18:10 │ Mochi │ 🍖 Dinner             │    10 │ 🔴 high    │         │
╰─────────────┴───────┴───────────────────────┴───────┴────────────┴─────────╯
Time budget  ████████████████████░░░░░░░░░░ 60/90 min (67%)
...

⭐ Priority-first view of today's plan

Budget 90 min  ████████████████████░░░░░░░░░░ 60/90 min (67%)
╭─────┬────────────┬────────┬───────┬───────────────────────┬───────┬────────────╮
│   # │ Priority   │ Time   │ Pet   │ Task                  │   Min │ Plan       │
├─────┼────────────┼────────┼───────┼───────────────────────┼───────┼────────────┤
│   1 │ 🔴 high    │ 07:30  │ Mochi │ 🦮 Morning walk       │    30 │ ✅ planned │
│   2 │ 🔴 high    │ 07:30  │ Mochi │ 💊 Flea treatment     │     5 │ ✅ planned │
│   3 │ 🔴 high    │ 08:15  │ Luna  │ 💊 Thyroid medication │     5 │ ✅ planned │
│   4 │ 🔴 high    │ 18:00  │ Mochi │ 🍖 Dinner             │    10 │ ✅ planned │
│   5 │ 🟡 medium  │ 08:15  │ Mochi │ 🦷 Brush teeth        │    10 │ ✅ planned │
╰─────┴────────────┴────────┴───────┴───────────────────────┴───────┴────────────╯

Budget 50 min  ██████████████████████████████ 50/50 min (100%)
╭─────┬────────────┬────────┬───────┬───────────────────────┬───────┬────────────╮
│   # │ Priority   │ Time   │ Pet   │ Task                  │   Min │ Plan       │
├─────┼────────────┼────────┼───────┼───────────────────────┼───────┼────────────┤
│   1 │ 🔴 high    │ 07:30  │ Mochi │ 🦮 Morning walk       │    30 │ ✅ planned │
│   2 │ 🔴 high    │ 07:30  │ Mochi │ 💊 Flea treatment     │     5 │ ✅ planned │
│   3 │ 🔴 high    │ 08:15  │ Luna  │ 💊 Thyroid medication │     5 │ ✅ planned │
│   4 │ 🔴 high    │ 18:00  │ Mochi │ 🍖 Dinner             │    10 │ ✅ planned │
│   - │ 🟡 medium  │ 08:15  │ Mochi │ 🦷 Brush teeth        │    10 │ ❌ no time │
╰─────┴────────────┴────────┴───────┴───────────────────────┴───────┴────────────╯
```

What this shows:

- **Time order vs. priority order.** In the timeline, Brush teeth (medium, 08:15) comes before Dinner (high, 18:00). In the priority view, all four high tasks come first, and Brush teeth is last, even though it's earlier in the day.
- **Time breaks ties within a priority.** The four high tasks are listed 07:30, 07:30, 08:15, 18:00. The two 07:30 tasks are both Mochi's, so they keep the order they were added in (Python's sort is stable).
- **Priority decides what's dropped.** With 90 minutes everything fits. With only 50 minutes, the four high tasks use all 50, so the medium task is the one left out, even though it's only 10 minutes long.

**In the app.** Under **Today's Schedule**, a **Show plan by: Time / Priority** toggle switches between the two orders. The "Why this plan" caption changes to match.

### How I tested it

Every feature above has its own tests. See [Testing PawPal+](#-testing-pawpal) for the full list and the latest results.

## 🎨 Output Formatting

I wanted the output to be readable at a glance, in the terminal and in the app. All the display logic lives in one new module, **`formatting.py`**, so `main.py` and `app.py` show tasks the same way. It only turns values into text and never changes any data, so the scheduling code in `pawpal_system.py` didn't change.

### What I added

| Feature | Looks like | Function / library | Used in |
| --- | --- | --- | --- |
| Task-type emojis | 🦮 Morning walk, 💊 Thyroid medication, 🍖 Dinner, 🦷 Brush teeth, 🧼 Brush fur, 🎾 Fetch, 🩺 Vet, 🧹 Litter, 🐾 anything else | `task_emoji()`, `task_label()` | CLI tables, app tables, "Mark a task done" list |
| Priority badges | 🔴 high · 🟡 medium · 🟢 low | `priority_badge()` | CLI and app |
| Status badges | ✅ done · ❗ overdue · ⏳ due today · 📅 upcoming | `task_status()`, `status_badge()` | CLI task tables, app **Status** column |
| Terminal colors | high in bold red, medium in yellow, low in green, finished and skipped rows dimmed | `colorize()`, `color_enabled()` (ANSI escape codes) | CLI |
| Structured tables | rounded box-drawing tables | **`tabulate`** (`tablefmt="rounded_outline"`, `missingval`) | every table in `main.py` |
| Time-budget bar | `████████████████████░░░░░░░░░░ 60/90 min (67%)` | `budget_bar()` in `main.py`; `st.progress()` in the app | CLI and app |
| Conflict marker | ⚡ in a **Clash** column | `find_conflicts()` + table column | CLI and app |
| Legend | "Priority: 🔴 high · 🟡 medium · 🟢 low \| Status: ✅ done · ..." | `st.caption()` built from the same badge dicts | app |

### How it works

- **Task-type emojis.** `task_emoji()` looks for keywords in the task description, ignoring case, and returns the emoji of the first group that matches. The order matters: "teeth" is checked before "brush", so "Brush teeth" gets 🦷 and "Brush fur" gets 🧼, and the medicine group comes first so "Flea treatment" isn't mistaken for a food "treat". Anything that doesn't match gets 🐾. The keyword lists are in `TASK_EMOJIS`, so adding a new type is a one-line change.
- **Status.** `task_status()` compares a task with today: completed → done, due before today → overdue, due today → due today, due later → upcoming (like the next copy of a recurring task).
- **Colors that don't get in the way.** `colorize()` wraps text in ANSI escape codes, which a terminal reads as "switch color". `color_enabled()` turns color off when output isn't going to a terminal (for example `python main.py > out.txt`) or when the [`NO_COLOR`](https://no-color.org) environment variable is set. That's why the sample output in this README has no stray codes in it.
- **Tables with `tabulate`.** `main.py` builds each table as a list of rows and calls `tabulate(rows, headers=..., tablefmt="rounded_outline")`. Emojis are two columns wide in a terminal, so I also installed **`wcwidth`**: when it's installed, tabulate uses it to measure emoji width correctly. tabulate also ignores ANSI codes when measuring, so colored cells don't push the borders out. I only picked emojis that are a single character (no variation selector like in ⚠️), because those are the ones terminals draw at a reliable width. A test checks that every line of a colored, emoji-filled table has the same width.
- **In the app.** Streamlit already draws tables, so the app reuses the badge functions in its `st.table` rows, adds a **Status** column and a legend, and shows the time budget with `st.progress()`.

### Example

`python main.py` (task list and today's plan; colors show in a real terminal):

```
All tasks sorted by time
╭────────────┬────────┬───────┬───────────────────────┬────────────┬──────────────╮
│ Due        │ Time   │ Pet   │ Task                  │ Priority   │ Status       │
├────────────┼────────┼───────┼───────────────────────┼────────────┼──────────────┤
│ Sun Oct 04 │ 07:30  │ Mochi │ 🦮 Morning walk       │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 07:30  │ Mochi │ 💊 Flea treatment     │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 08:00  │ Luna  │ 🍖 Breakfast          │ 🔴 high    │ ✅ done      │
│ Sun Oct 04 │ 08:15  │ Luna  │ 💊 Thyroid medication │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 08:15  │ Mochi │ 🦷 Brush teeth        │ 🟡 medium  │ ⏳ due today │
│ Sun Oct 04 │ 16:00  │ Mochi │ 🎾 Fetch in the yard  │ 🟢 low     │ ✅ done      │
│ Sun Oct 04 │ 18:00  │ Mochi │ 🍖 Dinner             │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 19:30  │ Luna  │ 🧼 Brush fur          │ 🟡 medium  │ ✅ done      │
│ Mon Oct 05 │ 08:00  │ Luna  │ 🍖 Breakfast          │ 🔴 high    │ 📅 upcoming  │
│ Sun Oct 11 │ 19:30  │ Luna  │ 🧼 Brush fur          │ 🟡 medium  │ 📅 upcoming  │
╰────────────┴────────┴───────┴───────────────────────┴────────────┴──────────────╯
```

The full output is under [Sample CLI output](#sample-cli-output).

### Files modified

| File | Change |
| --- | --- |
| `formatting.py` (new) | Emoji, badge, status and color helpers shared by the CLI and the app |
| `main.py` | Every printout is now a `tabulate` table with emojis, badges and colors, plus a time-budget bar |
| `app.py` | Uses the shared helpers for task, priority and status columns; adds a legend, a ⚡ Clash column and a time-budget progress bar |
| `requirements.txt` | Added `tabulate` and `wcwidth` |
| `tests/test_formatting.py` (new) | 24 tests for the helpers, color switching, table alignment and the budget bar |

## 💾 Data Persistence

PawPal+ remembers your pets and tasks between runs by saving them to `data.json`.

### How it works

```
Owner ──to_dict()──▶ plain dicts/lists ──json.dump──▶ data.json
data.json ──json.load──▶ plain dicts/lists ──from_dict()──▶ Owner (with Pets and Tasks)
```

`json` can only write basic types (dicts, lists, strings, numbers, booleans). My `Owner` holds `Pet` objects, which hold `Task` objects, which hold a `datetime.time` and a `datetime.date`. So each class converts itself:

- **`Task.to_dict()`** turns `start_time` into `"07:30"` and `due_date` into `"2026-10-04"`. **`Task.from_dict()`** goes through the normal `Task(...)` constructor, so `__post_init__` still checks the data. A damaged file with `"25:00"` or `"priority": "urgent"` is rejected, not loaded silently.
- **`Pet.to_dict()` / `Pet.from_dict()`** do the same for a pet and its list of tasks.
- **`Owner.to_dict()` / `Owner.from_dict()`** do the same for the owner, their time budget and all their pets.

On top of those:

- **`Owner.save_to_json(path="data.json")`** writes the whole owner as indented JSON. It writes to `data.json.tmp` first and then swaps it in with `os.replace()`, so a crash halfway through can't leave a half-written file.
- **`Owner.load_from_json(path="data.json")`** is a class method that returns a new `Owner`. If the file doesn't exist yet (the first run), it returns `None`. If the file is broken, it raises one `ValueError` with a clear message, whatever the cause: bad JSON, a missing field or a bad value.

A saved task looks like this:

```json
{
  "description": "Walk",
  "start_time": "07:30",
  "duration_minutes": 20,
  "priority": "high",
  "frequency": "daily",
  "completed": false,
  "due_date": "2026-10-05"
}
```

Completed tasks are saved too, so the history and the next copies of recurring tasks come back exactly as they were.

### In the app

1. **On startup**, `app.py` calls `Owner.load_from_json()` once per session. If there's no file yet, it starts with a new owner. If the file is broken, it shows an error and starts fresh instead of crashing.
2. **The Owner name and minutes fields** start from the loaded owner, so a returning user sees their own settings.
3. **After every change**, meaning adding a pet, adding a task, marking a task done, or editing the name or minutes, the app calls `save_to_json()`. There's no Save button to forget.

`data.json` is saved next to `app.py`, so it's the same file whichever folder you start Streamlit from. To start over, delete `data.json`. It's listed in `.gitignore`, because it holds personal data and not code.

### Why a custom dictionary conversion and not marshmallow

I asked my AI assistant about both options. marshmallow is a library where you write a schema class for each object, and it handles converting and validating. For PawPal+, the custom `to_dict()` / `from_dict()` methods were the better fit:

- **No new dependency.** It only uses `json`, `os` and `pathlib` from the standard library.
- **Validation already exists.** `Task.__post_init__` already checks priority, frequency, duration and time format. `from_dict()` reuses it, so the rules live in one place. A marshmallow schema would repeat them.
- **The data is small and simple.** Three classes with a few fields each, and only two fields (`time` and `date`) need converting.

marshmallow would be worth it if the data grew: many more classes, version changes to the file format, or detailed per-field error messages.

### Files modified

| File                   | Change                                                                                                                             |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `pawpal_system.py`     | Added `to_dict()` / `from_dict()` to `Task`, `Pet` and `Owner`, plus `Owner.save_to_json()` and `Owner.load_from_json()`           |
| `app.py`               | Loads `data.json` on startup, fills the owner fields from it, and saves after every change                                         |
| `tests/test_pawpal.py` | 8 new tests for saving and loading (round trip, same schedule after loading, file format, overwriting, missing file, broken files) |
| `.gitignore`           | Ignores `data.json` and `data.json.tmp`                                                                                            |
| `README.md`            | This section, plus the feature list and test notes                                                                                 |

## 📸 Demo Walkthrough

Start the app with:

```bash
streamlit run app.py
```

### What you can do in the app

The page is one column with four sections, from top to bottom:

| Section              | What you can do                                                                                                                                                                                                                                       |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Owner**            | Enter your name and how many minutes you have free today. Changing the minutes updates the schedule right away.                                                                                                                                       |
| **Pets**             | Add a pet with a name, species and age. A table lists your pets and how many tasks each one has. Blank and duplicate names are rejected with an error.                                                                                                |
| **Tasks**            | Add a task for a pet with a start time, duration, priority and frequency (once, daily or weekly). Mark a pending task done. Browse every task with **Filter by pet**, **Filter by status** (All, Pending or Done) and **Sort by** (Time or Priority). |
| **Today's Schedule** | See today's plan with summary numbers (tasks planned, minutes used, conflicts), any conflict warnings with a suggested fix, the plan table, and an expander listing tasks that didn't fit.                                                            |

### Example workflow

1. **Set up the owner.** Keep the name "Jordan" and set **Minutes available today** to 60.
2. **Add two pets.** Add Mochi (dog, 3) and Luna (cat, 5). Both appear in the pets table with 0 tasks.
3. **Schedule some tasks.**
   - Mochi: "Morning walk" at 08:00, 30 min, high, daily.
   - Luna: "Breakfast" at 08:15, 10 min, medium, daily.
   - Luna: "Grooming" at 10:00, 45 min, low, once.
4. **Browse the task list.** All three tasks appear in time order. Switch **Sort by** to Priority, and Morning walk moves to the top while Grooming moves to the bottom. Set **Filter by pet** to Luna to see only her two tasks.
5. **Check today's schedule.** The plan keeps Morning walk and Breakfast (40 of 60 minutes). Grooming doesn't fit in the 20 minutes left, so it appears under **Skipped today**.
6. **Read the conflict warning.** A yellow warning says there is 1 timing conflict, because Luna's Breakfast at 08:15 starts during Mochi's 08:00-08:30 walk. Both rows are marked ⚡ in the table, and the warning suggests the next free slot for Breakfast, **08:30**, when the walk ends. The app can't edit or delete tasks yet, so in practice you'd use that time when you schedule Breakfast.
7. **Mark a task done.** Choose Mochi's Morning walk under **Mark a task done**. The app says "Done! Next 'Morning walk' for Mochi is due" tomorrow, because it's a daily task. The task list now shows the finished walk as ✅ done and a new copy dated tomorrow as 📅 upcoming.
8. **Watch the schedule update.** With the walk done, the conflict is gone and a green "No overlapping tasks" message appears. Breakfast and Grooming now fit together (55 of 60 minutes), so Grooming moves from **Skipped today** into the plan.

### Scheduler behaviors you can see in the app

- **Sorting:** the task list uses `sort_by_time()` or `sort_by_priority()`, depending on **Sort by**. The schedule uses time order by default, and the **Show plan by** toggle switches it to priority order.
- **Filtering:** the pet and status filters call `get_tasks(pet_name, completed)`. The "Mark a task done" list uses `get_tasks(completed=False)`.
- **Planning within the time budget:** `todays_schedule()` builds the plan, and `skipped_tasks()` fills the **Skipped today** list. Raising the available minutes brings those tasks back into the plan.
- **Conflict warnings:** `find_conflicts()` and `conflict_warnings()` drive the warning banner, the ⚡ Clash column and the suggested start times.
- **Next available slot:** `find_next_available_slot()` gives the 💡 suggestion under each conflict and powers the **🔎 Find a free slot** box.
- **Recurrence:** `mark_task_complete()` adds the next daily or weekly copy, which you can see in the **Due** column.

### Sample CLI output

`main.py` runs the same classes without the UI. It creates an owner with two pets and eight tasks (added out of order on purpose), completes three of them, then prints each sorted and filtered view, today's schedule and any conflicts. Output from `python main.py`:

```
All tasks (insertion order)
╭────────────┬────────┬───────┬───────────────────────┬────────────┬──────────────╮
│ Due        │ Time   │ Pet   │ Task                  │ Priority   │ Status       │
├────────────┼────────┼───────┼───────────────────────┼────────────┼──────────────┤
│ Sun Oct 04 │ 18:00  │ Mochi │ 🍖 Dinner             │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 16:00  │ Mochi │ 🎾 Fetch in the yard  │ 🟢 low     │ ✅ done      │
│ Sun Oct 04 │ 07:30  │ Mochi │ 🦮 Morning walk       │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 08:15  │ Mochi │ 🦷 Brush teeth        │ 🟡 medium  │ ⏳ due today │
│ Sun Oct 04 │ 07:30  │ Mochi │ 💊 Flea treatment     │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 19:30  │ Luna  │ 🧼 Brush fur          │ 🟡 medium  │ ✅ done      │
│ Sun Oct 04 │ 08:15  │ Luna  │ 💊 Thyroid medication │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 08:00  │ Luna  │ 🍖 Breakfast          │ 🔴 high    │ ✅ done      │
│ Mon Oct 05 │ 08:00  │ Luna  │ 🍖 Breakfast          │ 🔴 high    │ 📅 upcoming  │
│ Sun Oct 11 │ 19:30  │ Luna  │ 🧼 Brush fur          │ 🟡 medium  │ 📅 upcoming  │
╰────────────┴────────┴───────┴───────────────────────┴────────────┴──────────────╯

All tasks sorted by time
╭────────────┬────────┬───────┬───────────────────────┬────────────┬──────────────╮
│ Due        │ Time   │ Pet   │ Task                  │ Priority   │ Status       │
├────────────┼────────┼───────┼───────────────────────┼────────────┼──────────────┤
│ Sun Oct 04 │ 07:30  │ Mochi │ 🦮 Morning walk       │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 07:30  │ Mochi │ 💊 Flea treatment     │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 08:00  │ Luna  │ 🍖 Breakfast          │ 🔴 high    │ ✅ done      │
│ Sun Oct 04 │ 08:15  │ Luna  │ 💊 Thyroid medication │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 08:15  │ Mochi │ 🦷 Brush teeth        │ 🟡 medium  │ ⏳ due today │
│ Sun Oct 04 │ 16:00  │ Mochi │ 🎾 Fetch in the yard  │ 🟢 low     │ ✅ done      │
│ Sun Oct 04 │ 18:00  │ Mochi │ 🍖 Dinner             │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 19:30  │ Luna  │ 🧼 Brush fur          │ 🟡 medium  │ ✅ done      │
│ Mon Oct 05 │ 08:00  │ Luna  │ 🍖 Breakfast          │ 🔴 high    │ 📅 upcoming  │
│ Sun Oct 11 │ 19:30  │ Luna  │ 🧼 Brush fur          │ 🟡 medium  │ 📅 upcoming  │
╰────────────┴────────┴───────┴───────────────────────┴────────────┴──────────────╯

Mochi's tasks
╭────────────┬────────┬───────┬──────────────────────┬────────────┬──────────────╮
│ Due        │ Time   │ Pet   │ Task                 │ Priority   │ Status       │
├────────────┼────────┼───────┼──────────────────────┼────────────┼──────────────┤
│ Sun Oct 04 │ 07:30  │ Mochi │ 🦮 Morning walk      │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 07:30  │ Mochi │ 💊 Flea treatment    │ 🔴 high    │ ⏳ due today │
│ Sun Oct 04 │ 08:15  │ Mochi │ 🦷 Brush teeth       │ 🟡 medium  │ ⏳ due today │
│ Sun Oct 04 │ 16:00  │ Mochi │ 🎾 Fetch in the yard │ 🟢 low     │ ✅ done      │
│ Sun Oct 04 │ 18:00  │ Mochi │ 🍖 Dinner            │ 🔴 high    │ ⏳ due today │
╰────────────┴────────┴───────┴──────────────────────┴────────────┴──────────────╯

Completed tasks
╭────────────┬────────┬───────┬──────────────────────┬────────────┬──────────╮
│ Due        │ Time   │ Pet   │ Task                 │ Priority   │ Status   │
├────────────┼────────┼───────┼──────────────────────┼────────────┼──────────┤
│ Sun Oct 04 │ 16:00  │ Mochi │ 🎾 Fetch in the yard │ 🟢 low     │ ✅ done  │
│ Sun Oct 04 │ 19:30  │ Luna  │ 🧼 Brush fur         │ 🟡 medium  │ ✅ done  │
│ Sun Oct 04 │ 08:00  │ Luna  │ 🍖 Breakfast         │ 🔴 high    │ ✅ done  │
╰────────────┴────────┴───────┴──────────────────────┴────────────┴──────────╯

Luna's pending tasks
╭────────────┬────────┬───────┬───────────────────────┬────────────┬──────────────╮
│ Due        │ Time   │ Pet   │ Task                  │ Priority   │ Status       │
├────────────┼────────┼───────┼───────────────────────┼────────────┼──────────────┤
│ Sun Oct 04 │ 08:15  │ Luna  │ 💊 Thyroid medication │ 🔴 high    │ ⏳ due today │
│ Mon Oct 05 │ 08:00  │ Luna  │ 🍖 Breakfast          │ 🔴 high    │ 📅 upcoming  │
│ Sun Oct 11 │ 19:30  │ Luna  │ 🧼 Brush fur          │ 🟡 medium  │ 📅 upcoming  │
╰────────────┴────────┴───────┴───────────────────────┴────────────┴──────────────╯

🐾 Today's Schedule for Jordan
╭─────────────┬───────┬───────────────────────┬───────┬────────────┬─────────╮
│ Time        │ Pet   │ Task                  │   Min │ Priority   │ Clash   │
├─────────────┼───────┼───────────────────────┼───────┼────────────┼─────────┤
│ 07:30-08:00 │ Mochi │ 🦮 Morning walk       │    30 │ 🔴 high    │ ⚡      │
│ 07:30-07:35 │ Mochi │ 💊 Flea treatment     │     5 │ 🔴 high    │ ⚡      │
│ 08:15-08:20 │ Luna  │ 💊 Thyroid medication │     5 │ 🔴 high    │ ⚡      │
│ 08:15-08:25 │ Mochi │ 🦷 Brush teeth        │    10 │ 🟡 medium  │ ⚡      │
│ 18:00-18:10 │ Mochi │ 🍖 Dinner             │    10 │ 🔴 high    │         │
╰─────────────┴───────┴───────────────────────┴───────┴────────────┴─────────╯
Time budget  ████████████████████░░░░░░░░░░ 60/90 min (67%)

Conflicts (2):
  ⚠️  Conflict (same pet: Mochi): 'Morning walk' 07:30-08:00 and 'Flea treatment' 07:30-07:35 start at the same time.
  ⚠️  Conflict (Luna & Mochi): 'Thyroid medication' 08:15-08:20 and 'Brush teeth' 08:15-08:25 start at the same time.

⭐ Priority-first view of today's plan

Budget 90 min  ████████████████████░░░░░░░░░░ 60/90 min (67%)
╭─────┬────────────┬────────┬───────┬───────────────────────┬───────┬────────────╮
│   # │ Priority   │ Time   │ Pet   │ Task                  │   Min │ Plan       │
├─────┼────────────┼────────┼───────┼───────────────────────┼───────┼────────────┤
│   1 │ 🔴 high    │ 07:30  │ Mochi │ 🦮 Morning walk       │    30 │ ✅ planned │
│   2 │ 🔴 high    │ 07:30  │ Mochi │ 💊 Flea treatment     │     5 │ ✅ planned │
│   3 │ 🔴 high    │ 08:15  │ Luna  │ 💊 Thyroid medication │     5 │ ✅ planned │
│   4 │ 🔴 high    │ 18:00  │ Mochi │ 🍖 Dinner             │    10 │ ✅ planned │
│   5 │ 🟡 medium  │ 08:15  │ Mochi │ 🦷 Brush teeth        │    10 │ ✅ planned │
╰─────┴────────────┴────────┴───────┴───────────────────────┴───────┴────────────╯

Budget 50 min  ██████████████████████████████ 50/50 min (100%)
╭─────┬────────────┬────────┬───────┬───────────────────────┬───────┬────────────╮
│   # │ Priority   │ Time   │ Pet   │ Task                  │   Min │ Plan       │
├─────┼────────────┼────────┼───────┼───────────────────────┼───────┼────────────┤
│   1 │ 🔴 high    │ 07:30  │ Mochi │ 🦮 Morning walk       │    30 │ ✅ planned │
│   2 │ 🔴 high    │ 07:30  │ Mochi │ 💊 Flea treatment     │     5 │ ✅ planned │
│   3 │ 🔴 high    │ 08:15  │ Luna  │ 💊 Thyroid medication │     5 │ ✅ planned │
│   4 │ 🔴 high    │ 18:00  │ Mochi │ 🍖 Dinner             │    10 │ ✅ planned │
│   - │ 🟡 medium  │ 08:15  │ Mochi │ 🦷 Brush teeth        │    10 │ ❌ no time │
╰─────┴────────────┴────────┴───────┴───────────────────────┴───────┴────────────╯

🔎 Next free slots
╭──────────┬──────────────┬───────────╮
│ Length   │ Not before   │ Free at   │
├──────────┼──────────────┼───────────┤
│ 10 min   │ 07:00        │ 07:00     │
│ 45 min   │ 07:00        │ 08:25     │
│ 30 min   │ 18:00        │ 18:10     │
╰──────────┴──────────────┴───────────╯
```

Breakfast and Brush fur each appear twice: once as the finished copy and once as the next one (tomorrow and next week). Fetch in the yard is a "once" task, so it doesn't come back.
