import math
import random
from copy import deepcopy
from typing import List, Dict, Any
import numpy as np


class Study:
    def __init__(self, name: str, locales: int, time: int):
        self.name = name
        self.locales = locales  # Total number of stations/locales for this study
        self.time = time  # Time units needed to complete the study

    def __repr__(self):
        # Helper for printing
        return f"Study({self.name}, Loc:{self.locales}, Time:{self.time})"


class Patient:
    def __init__(self, studies: List[Study], id_num: int):
        self.required_studies_orig = studies
        self.studies_remaining = studies[:]
        self.id_num = id_num
        self.completed_studies = []

        # total_wait_time will now only accumulate wait times for specific study queues.
        self.total_wait_time = 0.0
        # time_entered_current_queue is initialized to 0.0, representing arrival at t=0 for the simulation day.
        # It will be updated to the actual time_step when the patient enters a specific study queue.
        self.time_entered_current_queue = (
            0.0
        )

    def complete_study(self, study_obj: Study):
        if study_obj in self.studies_remaining:
            self.studies_remaining.remove(study_obj)
            self.completed_studies.append(study_obj)
        # else: # Optional: for debugging if a study is completed that wasn't remaining
        # print(
        #     f"  Warning: Patient {self.id_num} tried to complete study {study_obj.name} which was not in their remaining list."
        # )

    def needs_studies(self) -> bool:
        return len(self.studies_remaining) > 0

    def __repr__(self):
        return f"Patient(ID:{self.id_num}, Remaining:{[s.name for s in self.studies_remaining]}, Wait:{self.total_wait_time})"


def get_current_mean_admission_rate(
    time_step: int, schedule: Dict[tuple, float], default_rate: float
) -> float:
    """Helper to get mean admission rate from schedule based on time_step."""
    for (start, end), rate in schedule.items():
        if start <= time_step < end:
            return rate
    return default_rate


def simulate_workflow(
    get_fastest_study_func, # Renamed to avoid conflict with the helper function below if it's in the same scope
    initial_patient_list: List[Patient],
    study_defs: Dict[str, Study],
    time_period: int,
    admission_schedule: Dict[tuple, float] = None,
    default_initial_admission_rate: float = 1.0,
    show_steps: bool = True,
    lookahead=1,
):
    patient_arrival_queue = initial_patient_list[:]
    waiting_patients: List[Dict[str, Any]] = []
    active_sessions: Dict[str, List[Dict[str, Any]]] = {
        name: [] for name in study_defs.keys()
    }
    lines: Dict[str, int] = {name: 0 for name in study_defs.keys()}
    completed_patients: List[Patient] = []

    for time_step in range(time_period):
        if show_steps:
            print(f"\n--- Time Step: {time_step} ---")

        # 1. Process Active Sessions (Decrement time, handle completions)
        if show_steps: print(" Processing Active Sessions:")
        patients_finished_study_this_step = []
        for study_name, sessions in active_sessions.items():
            finished_indices = []
            for i, session_info in enumerate(sessions):
                session_info["remaining_time"] -= 1
                if session_info["remaining_time"] <= 0:
                    patient = session_info["patient"]
                    study_obj = session_info["study_obj"]
                    patient.complete_study(study_obj)
                    finished_indices.append(i)
                    if show_steps: print(f"  Patient {patient.id_num} finished {study_obj.name}.")
                    if patient.needs_studies():
                        patients_finished_study_this_step.append(patient)
                    else:
                        if show_steps: print(f"  Patient {patient.id_num} completed all studies.")
                        completed_patients.append(patient)
            # Remove finished sessions from active_sessions
            for i in sorted(finished_indices, reverse=True):
                del active_sessions[study_name][i]

        # 2. Assign Waiting Patients to Free Locales
        if show_steps: print(" Assigning Waiting Patients:")
        moved_from_waiting_indices = []
        for i, wait_info in enumerate(waiting_patients):
            patient = wait_info["patient"]
            assigned_study = wait_info["assigned_study"]
            study_name = assigned_study.name
            if len(active_sessions[study_name]) < study_defs[study_name].locales:
                # Patient is moving from a specific study queue to an active session.
                # Calculate wait time for this specific queue.
                if patient.time_entered_current_queue != -1.0: # -1.0 indicates not in a queue (e.g. active)
                    wait_duration = (
                        float(time_step) - patient.time_entered_current_queue
                    )
                    patient.total_wait_time += wait_duration
                    if show_steps: print(f"  Patient {patient.id_num} waited {wait_duration} for {study_name}. Total wait: {patient.total_wait_time}")
                
                patient.time_entered_current_queue = -1.0 # Mark as no longer waiting in a queue (now active)
                
                active_sessions[study_name].append(
                    {
                        "patient": patient,
                        "study_obj": assigned_study,
                        "remaining_time": assigned_study.time,
                    }
                )
                moved_from_waiting_indices.append(i)
                lines[study_name] -= 1
                if show_steps: print(f"  Patient {patient.id_num} started {study_name}.")
        # Remove assigned patients from waiting_patients
        for i in sorted(moved_from_waiting_indices, reverse=True):
            del waiting_patients[i]

        # 3. Re-assign Patients who just finished a study
        if show_steps: print(" Re-assigning Patients who finished a study:")
        for patient in patients_finished_study_this_step:
            if not patient.needs_studies():
                continue # Already handled if they completed all studies
            
            next_study = get_fastest_study_func(patient.studies_remaining, lines, lookahead)
            if next_study:
                # Patient is entering a new specific study queue.
                patient.time_entered_current_queue = float(time_step) # Mark entry time into this new queue
                
                waiting_patients.append(
                    {"patient": patient, "assigned_study": next_study}
                )
                lines[next_study.name] = lines.get(next_study.name, 0) + 1
                if show_steps: print(f"  Patient {patient.id_num} now waiting for {next_study.name}.")
            # else: # No next study available (e.g., all locales full or no studies left that can be done)
                # if show_steps: print(f"  Patient {patient.id_num} has no available next study right now.")


        # 4. Admit New Patients from Arrival Queue
        if show_steps: print(" Admitting New Patients:")
        num_to_attempt_admission = 0
        if admission_schedule:
            mean_rate_this_step = get_current_mean_admission_rate(
                time_step, admission_schedule, default_initial_admission_rate
            )
            if mean_rate_this_step > 0:
                num_to_attempt_admission = np.random.poisson(lam=mean_rate_this_step)
            else:
                num_to_attempt_admission = 0
        else:
            num_to_attempt_admission = int(default_initial_admission_rate)

        admitted_count = 0
        idx = 0
        while (
            idx < len(patient_arrival_queue)
            and admitted_count < num_to_attempt_admission
        ):
            current_patient = patient_arrival_queue[idx]
            if not current_patient.needs_studies(): # Should ideally not happen if they start in arrival queue
                completed_patients.append(current_patient)
                # If they somehow had no studies and were in arrival queue, their wait time is 0 as per new logic.
                # Their time_entered_current_queue was 0.0, but we are not adding initial wait.
                current_patient.time_entered_current_queue = -1.0 # Mark as not waiting
                patient_arrival_queue.pop(idx)
                if show_steps: print(f"  Patient {current_patient.id_num} admitted and already completed (no studies).")
                continue

            fastest_study = get_fastest_study_func(
                current_patient.studies_remaining, lines, lookahead
            )
            if fastest_study:
                # MODIFICATION: The time spent in patient_arrival_queue (from t=0 to now)
                # is NOT added to current_patient.total_wait_time.
                # We only care about waits for specific study queues.
                
                # Set the time they enter the queue for the *first specific study*.
                # The wait for *this* queue will be calculated in Section 2.
                current_patient.time_entered_current_queue = float(time_step)
                
                waiting_patients.append(
                    {"patient": current_patient, "assigned_study": fastest_study}
                )
                lines[fastest_study.name] = lines.get(fastest_study.name, 0) + 1
                patient_arrival_queue.pop(idx) # Remove from arrival queue
                admitted_count += 1
                if show_steps: print(f"  Patient {current_patient.id_num} admitted, now waiting for {fastest_study.name}.")
            else: # Cannot find a study for this patient from arrival queue yet
                idx += 1
                if show_steps: print(f"  Patient {current_patient.id_num} in arrival queue, no study assigned yet.")
        
        if show_steps:
            print(f"  End of Time Step {time_step}:")
            print(f"    Arrival Queue: {len(patient_arrival_queue)}")
            print(f"    Waiting Patients: {len(waiting_patients)}")
            print(f"    Active Sessions: {sum(len(s) for s in active_sessions.values())}")
            print(f"    Completed Patients: {len(completed_patients)}")
            print(f"    Current Lines: {lines}")


    if completed_patients:
        total_wait_time_for_completed = sum(
            p.total_wait_time for p in completed_patients
        )
        average_wait_time_completed = total_wait_time_for_completed / len(
            completed_patients
        )
    else:
        average_wait_time_completed = 0.0

    return {
        "completed_patients": completed_patients,
        "waiting_patients_final_state_objects": [
            wp["patient"] for wp in waiting_patients
        ],
        "active_sessions_final_state_patients": [
            s["patient"] for sessions in active_sessions.values() for s in sessions
        ],
        "lines": lines,
        "still_in_arrival_queue": patient_arrival_queue,
        "average_wait_time_completed": average_wait_time_completed,
    }


def simulate_workflow_random(
    initial_patient_list: List[Patient],
    study_defs: Dict[str, Study],
    time_period: int,
    admission_schedule: Dict[tuple, float] = None,
    default_initial_admission_rate: float = 1.0,
    show_steps: bool = True,
):
    patient_arrival_queue = initial_patient_list[:]
    waiting_patients: List[Dict[str, Any]] = []
    active_sessions: Dict[str, List[Dict[str, Any]]] = {
        name: [] for name in study_defs.keys()
    }
    lines: Dict[str, int] = {name: 0 for name in study_defs.keys()}
    completed_patients: List[Patient] = []

    for time_step in range(time_period):
        # (Sections 1, 2, 3 are similar to simulate_workflow with appropriate wait time logic)
        # 1. Process Active Sessions
        patients_finished_study_this_step = []
        for study_name, sessions in active_sessions.items():
            finished_indices = []
            for i, session_info in enumerate(sessions):
                session_info["remaining_time"] -= 1
                if session_info["remaining_time"] <= 0:
                    patient = session_info["patient"]
                    study_obj = session_info["study_obj"]
                    patient.complete_study(study_obj)
                    finished_indices.append(i)
                    if patient.needs_studies():
                        patients_finished_study_this_step.append(patient)
                    else:
                        completed_patients.append(patient)
            for i in sorted(finished_indices, reverse=True):
                del active_sessions[study_name][i]

        # 2. Assign Waiting Patients to Free Locales
        moved_from_waiting_indices = []
        for i, wait_info in enumerate(waiting_patients):
            patient = wait_info["patient"]
            assigned_study = wait_info["assigned_study"]
            study_name = assigned_study.name
            if (
                study_name in study_defs # Ensure study_name is valid
                and len(active_sessions[study_name]) < study_defs[study_name].locales
            ):
                if patient.time_entered_current_queue != -1.0:
                    wait_duration = (
                        float(time_step) - patient.time_entered_current_queue
                    )
                    patient.total_wait_time += wait_duration
                patient.time_entered_current_queue = -1.0
                active_sessions[study_name].append(
                    {
                        "patient": patient,
                        "study_obj": assigned_study,
                        "remaining_time": assigned_study.time,
                    }
                )
                moved_from_waiting_indices.append(i)
                lines[study_name] -= 1
        for i in sorted(moved_from_waiting_indices, reverse=True):
            del waiting_patients[i]

        # 3. Re-assign Patients who just finished a study (RANDOM choice)
        for patient in patients_finished_study_this_step:
            if not patient.needs_studies():
                continue
            if patient.studies_remaining:
                performable_studies = [
                    s
                    for s in patient.studies_remaining
                    if s.name in study_defs and study_defs[s.name].locales > 0
                ]
                if performable_studies:
                    next_study_obj = random.choice(performable_studies)
                    patient.time_entered_current_queue = float(time_step) # Entering new specific queue
                    waiting_patients.append(
                        {"patient": patient, "assigned_study": next_study_obj}
                    )
                    lines[next_study_obj.name] = lines.get(next_study_obj.name, 0) + 1
        
        # 4. Admit New Patients from Arrival Queue (MODIFIED PART for probabilistic admission)
        num_to_attempt_admission = 0
        if admission_schedule:
            mean_rate_this_step = get_current_mean_admission_rate(
                time_step, admission_schedule, default_initial_admission_rate
            )
            if mean_rate_this_step > 0:
                num_to_attempt_admission = np.random.poisson(lam=mean_rate_this_step)
            else:
                num_to_attempt_admission = 0
        else:
            num_to_attempt_admission = int(default_initial_admission_rate)

        admitted_this_step_count = 0
        idx = 0
        while (
            idx < len(patient_arrival_queue)
            and admitted_this_step_count < num_to_attempt_admission
        ):
            current_patient = patient_arrival_queue[idx]
            if not current_patient.needs_studies():
                completed_patients.append(current_patient)
                current_patient.time_entered_current_queue = -1.0
                patient_arrival_queue.pop(idx)
                continue

            if current_patient.studies_remaining:
                performable_studies = [
                    s
                    for s in current_patient.studies_remaining
                    if s.name in study_defs and study_defs[s.name].locales > 0
                ]
                if performable_studies:
                    chosen_study_obj = random.choice(performable_studies)
                    
                    # MODIFICATION: Time spent in patient_arrival_queue is NOT added.
                    # Set time_entered_current_queue for the first specific study queue.
                    current_patient.time_entered_current_queue = float(time_step)
                    
                    waiting_patients.append(
                        {"patient": current_patient, "assigned_study": chosen_study_obj}
                    )
                    lines[chosen_study_obj.name] = (
                        lines.get(chosen_study_obj.name, 0) + 1
                    )
                    patient_arrival_queue.pop(idx) # Remove from arrival queue
                    admitted_this_step_count += 1
                else: # No performable studies from arrival queue at this time
                    idx += 1
            else: # Should be caught by "not current_patient.needs_studies()"
                idx += 1
                
    if completed_patients:
        total_wait_time_for_completed = sum(
            p.total_wait_time for p in completed_patients
        )
        average_wait_time_completed = total_wait_time_for_completed / len(
            completed_patients
        )
    else:
        average_wait_time_completed = 0.0

    return {
        "completed_patients": completed_patients,
        "waiting_patients_final_state_objects": [
            wp["patient"] for wp in waiting_patients
        ],
        "active_sessions_final_state_patients": [
            s["patient"] for sessions in active_sessions.values() for s in sessions
        ],
        "lines": lines,
        "still_in_arrival_queue": patient_arrival_queue,
        "average_wait_time_completed": average_wait_time_completed,
    }


def get_fastest_study( # This is the original helper, ensure the simulation functions call the passed one.
    patient_remaining_studies: List[Study], lines: Dict[str, int]
) -> Study | None:
    if not patient_remaining_studies:
        return None

    times = {}
    for study in patient_remaining_studies:
        if study.locales <= 0: # Cannot be performed if no locales
            continue

        line_length = lines.get(study.name, 0)
        cycle_number = math.ceil((line_length + 1) / study.locales)
        estimated_wait = (cycle_number - 1) * study.time
        times[estimated_wait] = study

    if not times:
        return None

    min_wait = min(times.keys())
    return times[min_wait]
