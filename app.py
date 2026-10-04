from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# --- Owner -----------------------------------------------------------------------
# The owner's name and daily time budget. available_minutes is what the Scheduler
# uses to decide how many tasks fit into today's plan.

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input(
    "Minutes available today", min_value=0, max_value=1440, value=90, step=5
)

# Streamlit reruns this script on every interaction, so keep one Owner in session_state.
# Only create it the first time; afterwards reuse the stored instance and its pets/tasks.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name)
owner = st.session_state.owner
# Copy the latest widget values onto the stored Owner so edits take effect immediately.
owner.name = owner_name
owner.available_minutes = int(available_minutes)

# The Scheduler holds no data of its own; it reads everything through
# owner.get_all_tasks(), so it is cheap to rebuild on every rerun and always sees every pet.
scheduler = Scheduler(owner)

st.divider()

# --- Add a pet -------------------------------------------------------------------
# st.form groups the inputs so typing in them doesn't rerun the app; only clicking
# "Add pet" submits. clear_on_submit resets the fields after a successful add.

st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=40, value=3)
    if st.form_submit_button("Add pet"):
        # Validate before touching the Owner: reject blank names, and use
        # Owner.find_pet() to block duplicates (pets are looked up by name later).
        if not pet_name.strip():
            st.error("Please enter a pet name.")
        elif owner.find_pet(pet_name.strip()):
            st.error(f"{pet_name.strip()} is already one of your pets.")
        else:
            # Owner.add_pet() owns this change: the Owner is the class that manages
            # multiple pets. Because the Owner lives in session_state, the new Pet survives
            # the rerun that Streamlit triggers right after this button click.
            owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age)))
            st.success(f"Added {pet_name.strip()}!")

# Drawn after the form, so on the rerun triggered by "Add pet" this table already
# reads the updated owner.pets and shows the new pet; no manual refresh is needed.
if owner.pets:
    st.table(
        [
            {"Pet": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)}
            for p in owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Schedule a task ---------------------------------------------------------------
# Tasks always belong to a specific Pet, so this form only appears once a pet exists.

st.subheader("Tasks")
if not owner.pets:
    st.caption("Add a pet first, then you can schedule tasks for it.")
else:
    with st.form("add_task", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            # Options come from owner.pets, so newly added pets appear here automatically.
            task_pet = st.selectbox("Pet", [p.name for p in owner.pets])
            description = st.text_input("Task", value="Morning walk")
            # step=900 seconds gives 15-minute increments in the time picker.
            start_time = st.time_input("Start time", value=time(8, 0), step=900)
        with col2:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=1)
        if st.form_submit_button("Add task"):
            # Look up the chosen Pet by name, then call Pet.add_task() with a new Task.
            # Task.__post_init__ validates priority, frequency, and duration; if any value
            # is invalid it raises ValueError, which we show in the UI instead of crashing.
            try:
                owner.find_pet(task_pet).add_task(
                    Task(
                        description=description.strip(),
                        start_time=start_time,
                        duration_minutes=int(duration),
                        priority=priority,
                        frequency=frequency,
                    )
                )
                st.success(f"Added '{description.strip()}' for {task_pet}.")
            except ValueError as err:
                st.error(str(err))

    # Every task across all pets (via the Scheduler, which reads Owner.get_all_tasks()),
    # sorted by start time so the list reads like a timeline.
    all_tasks = scheduler.sort_by_time(scheduler.get_tasks())
    if all_tasks:
        st.table(
            [
                {
                    "Time": t.start_time.strftime("%H:%M"),
                    "Pet": p.name,
                    "Task": t.description,
                    "Minutes": t.duration_minutes,
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                    "Done": "✅" if t.completed else "",
                }
                for p, t in all_tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Build schedule --------------------------------------------------------------
# Runs the Scheduler's planning logic and explains the result: what was scheduled,
# what was skipped for lack of time, and which tasks overlap.

st.subheader("Today's Schedule")

if st.button("Generate schedule"):
    # todays_schedule() takes pending tasks in priority order (high -> low), keeps each
    # one that still fits in available_minutes, then re-sorts the kept tasks by start time.
    schedule = scheduler.todays_schedule()
    if not schedule:
        st.info("Nothing to schedule. Add some pending tasks first.")
    else:
        used = sum(t.duration_minutes for _, t in schedule)
        st.table(
            [
                {
                    "Time": t.start_time.strftime("%H:%M"),
                    "Pet": p.name,
                    "Task": t.description,
                    "Minutes": t.duration_minutes,
                    "Priority": t.priority,
                }
                for p, t in schedule
            ]
        )
        st.caption(f"Uses {used} of {owner.available_minutes} available minutes.")

        # Explain the plan in plain language so the user knows how tasks were chosen.
        st.markdown(
            "**Why this plan:** pending tasks were picked from high to low priority "
            "until your available time ran out, then ordered by start time."
        )
        # Pending tasks that didn't fit the time budget (usually lower-priority ones).
        for p, t in scheduler.skipped_tasks():
            st.warning(
                f"Skipped {p.name}: {t.description} ({t.duration_minutes} min, "
                f"{t.priority}) because there wasn't enough time left."
            )
        # Scheduled tasks whose time windows overlap, even if they belong to different
        # pets, since one owner can't do two things at once.
        for (pa, a), (pb, b) in scheduler.find_conflicts():
            st.error(
                f"Time conflict: {pa.name}'s '{a.description}' at "
                f"{a.start_time.strftime('%H:%M')} overlaps {pb.name}'s "
                f"'{b.description}' at {b.start_time.strftime('%H:%M')}."
            )
