# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My first design had four classes. Data flows down from the owner, and one class makes the decisions:

- **`Task`**: one care activity, with a description, start time, duration, priority, frequency and a completed flag. It checks its own values when it's created.
- **`Pet`**: a pet's name, species and age, plus its own list of tasks. It can add, find and remove them.
- **`Owner`**: the owner's name, their free minutes for the day, and their pets. `get_all_tasks()` collects every task from every pet as `(pet, task)` pairs.
- **`Scheduler`**: the "brain." It holds no data of its own and reads everything through `Owner.get_all_tasks()`. From there it filters, sorts, builds today's plan within the time budget, and reports skipped tasks and time conflicts.

`Owner` owns its pets and each `Pet` owns its tasks (composition). `Scheduler` only points at `Owner`. The final diagram is in `diagrams/uml_final.mmd`.

**Core user actions**

1. **Add a pet.** The user enters their own details (name, how much time they have each day, any preferences) and their pet's details (name, species or breed, age, special needs). The system stores this so later plans fit this owner and this pet.
2. **Schedule a care task.** The user adds a task such as a walk, feeding, medication, enrichment or grooming. Each task has a duration in minutes and a priority (low, medium or high), and the user can edit or remove it later.
3. **See today's tasks.** The user asks for today's plan. The system picks and orders tasks to fit the time available, puts high-priority tasks first, and explains why each task was included or left out.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes. The core structure stayed the same, but recurring tasks changed a lot.

**Recurring tasks: from "reset" to "next copy."** My first version had `Scheduler.reset_recurring_tasks()`, which flipped finished daily tasks back to pending. That had two problems. It lost the record of what was done, and it had no idea of *when* a task was due, so a weekly task looked the same as a daily one. I replaced it with a `due_date` field and `Task.next_occurrence()`. Now finishing a task keeps it as history and adds a new pending copy, due 1 or 7 days later. To support that, I added `due_tasks()` so future copies stay off today's plan, and `find_task(..., pending_only=True)` so "mark done" always picks up the copy that's still pending.

Other changes:
- **Times as real `time` objects.** I added `parse_time()` so `"7:30"` and `"07:30"` both become a `datetime.time`. Sorting the raw strings would put `"10:00"` before `"7:30"`.
- **Case-insensitive pet lookup.** A test showed `find_pet("mochi")` failed while `get_tasks("mochi")` worked, so I made both ignore case and extra spaces.
- **Planned features I dropped.** My core actions mentioned owner preferences, pet special needs, and editing tasks. None of these made it into the code. The time budget and priority turned out to cover the main scheduling decisions, so I left the others for a later version.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler looks at four things:

1. **Due date.** Only pending tasks due today or earlier are considered. Overdue tasks stay on the list until they're done.
2. **Priority.** High tasks are picked first, then medium, then low.
3. **Time budget.** A task is kept only if it still fits in the owner's free minutes for the day.
4. **Start time.** Start times order the final plan, and overlapping times are flagged as conflicts.

I ranked them by what goes wrong if they're ignored. Skipping a medication or meal is worse than leaving 10 minutes unused, so **priority comes before filling the time**. The time budget is a hard limit, because the owner really only has that many minutes. Start time decides the *order* of the plan, not *whether* a task is in it. That's also why conflicts are warnings instead of errors: the owner can fix a clash by moving a task, so the scheduler shouldn't throw a task out because of one.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Tradeoff: priority first, not the best fit for the time.** `todays_schedule()` is greedy. It sorts the due tasks from high to low priority and keeps each one that still fits in the owner's free minutes. It never goes back to look for a better combination. That means it can leave time unused, or fit in fewer tasks than it could have.

For example, say the owner has 60 minutes and three tasks:
- a 50-minute grooming session (medium priority)
- two 30-minute play sessions (low priority)

The scheduler keeps the grooming and skips both play sessions, so 10 minutes go unused. Picking the two play sessions instead would fill all 60 minutes and get two tasks done instead of one.

**Why this is reasonable here:**
- **Priority should win.** For a pet owner, priority means something real. A medication or a meal shouldn't be dropped so that two low-priority play sessions fit more neatly. Filling the time perfectly would mean solving a "knapsack" problem, and it could swap an important task for less important ones.
- **It's easy to explain.** The rule is "most important first, until time runs out." The app shows that rule under the schedule, and every skipped task gets a message saying there wasn't enough time. An owner can predict and trust that.
- **It's fast.** It is one sort and one pass. A day only has a handful of tasks, so a smarter search would add complexity without making the plan noticeably better.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used Claude Code in agent mode in VS Code for most steps of the build. It suggested and drafted:

- **Design:** the three core user actions (add a pet, schedule a care task, see today's tasks).
- **Implementation:**
  - the four classes in `pawpal_system.py` (`Task`, `Pet`, `Owner`, `Scheduler`)
  - a `main.py` script to test them in the terminal
  - the two starter tests in `tests/test_pawpal.py`
- **Debugging:** when `pytest` couldn't import `pawpal_system` from inside the `tests/` folder, it found the cause and suggested an empty `conftest.py` at the project root.
- **Documentation:** the one-line docstrings for every method, and the README summary and sample output.

The most helpful prompts were the ones where I pasted the assignment requirements word for word, like "Scheduler must read from that Owner method rather than from a single pet." Exact requirements gave me code that matched what was being graded. Vague prompts gave me something reasonable but slightly off target.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

**What I accepted:**
- The overall class structure: `Owner` → `Pet` → `Task` holds the data, and `Scheduler` sits on top of `Owner`.
- The scheduling rule: keep high-priority tasks first until the owner's free time runs out, then order the kept tasks by start time.
- The `conftest.py` fix for the test imports.

**What I rejected or changed:**
- **Core actions:** when I first asked for the three core user actions, the AI said section 1a already had them and made no changes. I didn't accept that. I asked it to actually write them based on my prompt, and the rewritten version names each action clearly and gives more detail about what the user enters.
- **Task fields:** the AI's first version of `Task` used `title` and `category`. When I gave it the full class requirements (description, time, frequency, completion status), I had it rename `title` to `description` and replace `category` with `frequency`. That way the code matched the spec instead of the AI's own guess.
- **Starting point:** the AI found that the original starter's `pawpal_system.py` had been removed from the repo and wrote a new one. I made sure the new version followed my own design (an `Owner` class and a time budget) rather than the old starter's.

**How I verified the results:**
- **The schedule:** I ran `python main.py` after every change. I checked by hand that the times were in order, the totals added up (65 of 90 minutes), and the low-priority 40-minute task was skipped because it wouldn't fit.
- **The tests:** I ran `pytest` and confirmed both tests passed. I ran plain `pytest` as well as `python -m pytest`, which is how I caught the import problem.
- **Extra scheduler behavior:** I checked conflict detection, marking a task complete and the daily reset with a quick script. For example, I made sure a 08:00 30-minute walk was flagged as overlapping an 08:15 feeding.
- **Docstrings:** I checked that every method had exactly one line and that no line was over 100 characters.

**c. AI strategy**

**Most effective features.**
- **Agent mode** worked best. It could read `pawpal_system.py`, `app.py` and the tests together, make changes across several files, and then run `pytest` and `main.py` itself to check them. A change came back already tested, not just as a suggestion.
- **Giving it the exact assignment text.** Pasting each step's requirements word for word kept its work aimed at what was actually asked.
- **Having it run the real app.** For the UI phase, it used Streamlit's `AppTest` to run `app.py` headless with overlapping tasks, and checked that the warning and suggested fix really appeared.
- **Asking "based on my final code, what changed?"** This was the most useful question for the UML and the README, because the answers came from the code instead of from memory.

**A suggestion I rejected or changed.** The AI's first `Task` used `title` and `category`. I had it switch to `description` and `frequency` to match the spec. `frequency` later became the base for recurring tasks, so that change mattered more than it looked at the time. A second example came from the README: the AI's first demo walkthrough told readers to "re-add Breakfast at 08:30" to clear a conflict. When it ran the steps in the real app, that didn't work, because the app can't edit or delete tasks, so the old 08:15 copy would still clash. We rewrote the step to describe what the app really does. That reminded me to check AI-written docs against the running app, not only against the code.

**Separate chat sessions for each phase.** I used a new chat for each phase: core classes, connecting the UI, smarter scheduling and tests, then polish (UI display, UML, README and this reflection). Each session started from the code in the repo instead of a long history of older ideas, so the AI couldn't rely on something we had already changed. For example, in the polish session, it noticed the README still described an old "Generate schedule" button. Ending each phase with a commit also gave me a clean checkpoint to go back to.

**Being the "lead architect."** The AI can write a lot of correct code quickly, but it optimizes for the prompt in front of it, not for the whole system. My job was to own the design: decide where each responsibility lives (decisions in `Scheduler`, data in `Owner` → `Pet` → `Task`), set the tradeoffs (priority over perfectly filling the time, warnings instead of errors), and turn requirements into precise prompts. Then I had to verify, because "it says it works" isn't the same as "it works." Running `main.py`, the tests and the app after every change is how I caught the case-sensitivity bug, the midnight-overlap bug, and the walkthrough step that the app couldn't actually do. The AI was the builder, but the architecture and the final say on what was correct stayed with me.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I wrote 44 tests in `tests/test_pawpal.py`, grouped around five behaviors:

1. **Sorting:** tasks come back in time order, ties are broken by priority, and bad time strings are rejected.
2. **Recurrence:** finishing a daily or weekly task adds the right next copy, including across month and year boundaries and when a task is finished late. "Once" tasks don't come back.
3. **Conflict detection:** exact and partial overlaps, for the same pet and different pets, and across midnight are all flagged. Back-to-back tasks are not.
4. **Time budget:** tasks that exactly fill the time are kept, a smaller task can fit after a bigger one is skipped, and 0 minutes gives an empty plan.
5. **Filtering, empty data and validation:** filters work alone and together, an owner with no pets doesn't crash anything, and bad priorities or durations are rejected.

These are the parts a pet owner depends on. A wrong sort or a missed conflict means a missed medication. They're also where the edge cases hide: dates, ties and boundaries. Two of the tests found real bugs (case-sensitive pet lookup and overlaps across midnight), which shows they were worth writing.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

**4 out of 5.** All 44 tests pass, every core behavior has normal-case and edge-case tests, and I pinned the dates so the results don't depend on what day I run them. I'm not giving it 5 because the Streamlit UI is only checked by hand and with a quick headless run, and because the greedy scheduler is predictable but not optimal.

Next I would test:
- **Two pets with the same name.** The app blocks this, but `Owner.add_pet()` doesn't. `find_pet()` would return only the first one, so the second pet's tasks couldn't be marked done.
- **Two pending tasks with the same description for one pet.** "Mark done" completes the first one it finds, which might not be the one the user picked.
- **The conflict fix the app suggests.** It doesn't check whether the new time clashes with a third task.
- **Tasks longer than a day, or a very large time budget.**
- **The UI itself**, using Streamlit's `AppTest`: adding pets and tasks, the filter dropdowns, and the conflict banner.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The conflict detection. It started as "check whether two times are equal" and ended up as a sort-then-sweep that handles partial overlaps, different pets and tasks past midnight, without ever crashing. In the app it doesn't just say something is wrong: it marks the clashing rows and suggests a start time that fixes the problem. I'm also happy that the `Scheduler` reads everything through `Owner`, which kept the classes simple even as features were added.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

- **Edit and delete tasks in the app.** Right now the only way to act on a conflict suggestion is to add a new task. The old one stays.
- **Give each task a unique ID.** Tasks are found by description, which breaks when a pet has two tasks with the same name. An ID would also make "mark done" exact.
- **Save data** to a JSON file so pets and tasks survive closing the app.
- **Use preferences in the plan**, such as preferred walk times or a pet's special needs, which were in my original core actions.
- **Plan more than one day**, so the owner can see the week and spread out weekly tasks.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

A clear design up front makes the AI much more useful. Because `Scheduler` always read through `Owner.get_all_tasks()`, every new feature (filters, recurrence, conflicts) had an obvious home, and I could check each AI change against one simple rule: data lives in `Owner` → `Pet` → `Task`, and decisions live in `Scheduler`. Whenever a suggestion didn't fit that rule, that was my sign to push back.
