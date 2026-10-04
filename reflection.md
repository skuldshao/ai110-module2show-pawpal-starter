# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**Core user actions**

1. **Add a pet.** The user enters their own details (name, how much time they have each day, any preferences) and their pet's details (name, species or breed, age, special needs). The system stores this so later plans fit this owner and this pet.
2. **Schedule a care task.** The user adds a task such as a walk, feeding, medication, enrichment or grooming. Each task has a duration in minutes and a priority (low, medium or high), and the user can edit or remove it later.
3. **See today's tasks.** The user asks for today's plan. The system picks and orders tasks to fit the time available, puts high-priority tasks first, and explains why each task was included or left out.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
