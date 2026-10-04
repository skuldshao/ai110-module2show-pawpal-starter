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

- **`Task`** is a single care activity. I gave it a description, start time, duration, priority (low, medium or high), frequency (once, daily or weekly) and a completed flag. It checks its own values when it's created, so a bad priority or a zero-minute task is rejected right away.
- **`Pet`** stores a pet's name, species and age, along with its own list of tasks. I can add, find and remove tasks on each pet.
- **`Owner`** holds several pets and the number of minutes the owner has free today. Its `get_all_tasks()` method collects every task from every pet into one list of `(pet, task)` pairs.
- **`Scheduler`** is the "brain." I made it read all of its data through `Owner.get_all_tasks()` instead of from any single pet, so every pet is always included. From that list it can:
  - filter tasks by pet or status
  - sort them by time or priority
  - build today's schedule by keeping the highest-priority tasks that fit the time budget, then ordering them by start time
  - report the tasks that didn't fit
  - flag tasks whose times overlap
  - mark tasks complete, and set daily tasks back to pending for a new day

Together, they work like this: `Owner` → `Pet` → `Task` holds the data, and `Scheduler` sits on top of `Owner` and makes the decisions. `main.py` is my terminal testing ground. It creates an owner with two pets and six tasks, then prints the schedule shown below. `tests/test_pawpal.py` checks that completing a task and adding a task to a pet work correctly.

## 🖥️ Sample Output

Output from running `python main.py`:

```
🐾 Today's Schedule for Jordan
============================================================
Time   Pet     Task                  Length   Priority
------------------------------------------------------------
07:30  Mochi   Morning walk          30 min   high
08:00  Luna    Breakfast             5 min    high
08:15  Luna    Thyroid medication    5 min    high
18:00  Mochi   Dinner                10 min   high
19:30  Luna    Brush fur             15 min   medium
------------------------------------------------------------
Total: 65 of 90 available minutes

Skipped (not enough time):
  - Mochi: Fetch in the yard (40 min, low)
```

Jordan has 90 minutes free today. The scheduler keeps high-priority tasks first, lists them by start time, and skips the low-priority 40-minute fetch session because it would go over the time budget.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature           | Method(s) | Notes                             |
| ----------------- | --------- | --------------------------------- |
| Task sorting      |           | e.g., by priority, duration       |
| Filtering         |           | e.g., skip tasks if time runs out |
| Conflict handling |           | e.g., overlapping time slots      |
| Recurring tasks   |           | e.g., daily vs. weekly            |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** _(optional)_: <!-- Insert a screenshot or link to a demo video here -->
