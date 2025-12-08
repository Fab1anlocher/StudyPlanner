"""
planning.py
-----------
Pure logic functions for calculating available study time slots.
This module contains no Streamlit dependencies and can be tested independently.
"""

from datetime import datetime, date, time, timedelta
from typing import List, Tuple, Dict, Any, Optional

from constants import WEEKDAY_INDEX_TO_EN, WEEKDAY_INDEX_TO_DE


def calculate_free_slots(
    study_start: date,
    study_end: date,
    busy_times: List[Dict[str, Any]],
    absences: List[Dict[str, Any]],
    rest_days: List[str],
    max_hours_day: float,
    max_hours_week: float,
    min_session_duration: float,
    earliest_study_time: time,
    latest_study_time: time,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """
    Calculate available time slots for studying based on user constraints.

    Args:
        study_start: Start date of the study period
        study_end: End date of the study period
        busy_times: List of recurring busy time blocks (e.g., lectures)
        absences: List of absence periods
        rest_days: List of weekday names where no study should occur (e.g., ["saturday", "sunday"])
        max_hours_day: Maximum study hours allowed per day
        earliest_study_time: Earliest time to start studying each day
        latest_study_time: Latest time to end studying each day

    Returns:
        Tuple of (free_slots_list, error_message)
        - free_slots_list: List of dicts with date, day, start_time, end_time
        - error_message: String error if validation fails, None otherwise
    """

    # Validation
    if not study_start or not study_end:
        return None, "Semester-Start und Semester-Ende müssen gesetzt sein."

    if study_start >= study_end:
        return None, "Semester-Start muss vor Semester-Ende liegen."

    # DEFENSIVE GUARD: Prevent extreme timeframes (performance & realism)
    days_difference = (study_end - study_start).days
    if days_difference > 365:
        return None, "Planungszeitraum darf maximal 1 Jahr (365 Tage) betragen."
    
    if days_difference < 1:
        return None, "Planungszeitraum muss mindestens 1 Tag betragen."

    # Build absence lookup for quick checks
    # OPTIMIZATION: Build absence lookup set for O(1) membership testing during iteration
    absence_lookup = set()
    for absence in absences:
        absence_start_date = absence.get("start")
        absence_end_date = absence.get("end")

        if absence_start_date and absence_end_date:
            # DEFENSIVE GUARD: Skip invalid absences (end before start)
            if absence_start_date > absence_end_date:
                # Log warning but continue (non-breaking)
                continue
            
            current_date = absence_start_date
            while current_date <= absence_end_date:
                absence_lookup.add(current_date)
                current_date += timedelta(days=1)

    # Pre-group busy times by weekday for lookup
    # FEATURE: Support for time-limited busy times (valid_from/valid_until)
    # Each entry now includes validity period info
    # Format: {weekday: [(start_time, end_time, valid_from, valid_until), ...]}
    busy_times_by_day: Dict[str, List[Tuple[time, time, Optional[date], Optional[date]]]] = {}
    for busy in busy_times:
        day = busy.get("day")
        busy_start = busy.get("start")
        busy_end = busy.get("end")
        valid_from = busy.get("valid_from")  # date or None
        valid_until = busy.get("valid_until")  # date or None
        if day and busy_start and busy_end:
            if day not in busy_times_by_day:
                busy_times_by_day[day] = []
            busy_times_by_day[day].append((busy_start, busy_end, valid_from, valid_until))

    # Convert rest_days to a set for O(1) lookup
    rest_days_set = set(rest_days)

    free_slots = []
    current_date = study_start

    # Process each day in the semester
    while current_date <= study_end:
        weekday_index = current_date.weekday()
        weekday_name = WEEKDAY_INDEX_TO_EN[weekday_index]

        # Skip rest days (O(1) lookup with set)
        if weekday_name in rest_days_set:
            current_date += timedelta(days=1)
            continue

        # Skip absence days
        if current_date in absence_lookup:
            current_date += timedelta(days=1)
            continue

        # Start with the full day as a free slot (from earliest to latest study time)
        free_intervals = [(earliest_study_time, latest_study_time)]

        # Subtract busy times for this weekday, filtering by validity period
        day_busy_times = busy_times_by_day.get(weekday_name, [])
        for busy_start, busy_end, valid_from, valid_until in day_busy_times:
            # Check if this busy time is valid for the current date
            if valid_from is not None and current_date < valid_from:
                # Busy time hasn't started yet
                continue
            if valid_until is not None and current_date > valid_until:
                # Busy time has ended (e.g., lectures ended mid-December)
                continue
            
            # Apply busy time to all current free intervals
            new_intervals = []
            for free_start, free_end in free_intervals:
                remaining = subtract_time_interval(
                    free_start, free_end, busy_start, busy_end
                )
                new_intervals.extend(remaining)
            free_intervals = new_intervals

        # Truncate to max hours per day
        free_intervals = truncate_intervals_to_max_hours(free_intervals, max_hours_day)

        # Filter by minimum session duration
        free_intervals = filter_by_min_duration(free_intervals, min_session_duration)

        # Add valid intervals to result
        for start_time, end_time in free_intervals:
            free_slots.append(
                {
                    "date": current_date,
                    "day": WEEKDAY_INDEX_TO_DE[weekday_index],
                    "start_time": start_time,
                    "end_time": end_time,
                }
            )

        current_date += timedelta(days=1)

    # Apply weekly limit if specified
    if max_hours_week > 0:
        free_slots = apply_weekly_limit(free_slots, max_hours_week)

    return free_slots, None


def subtract_time_interval(
    free_start: time, free_end: time, busy_start: time, busy_end: time
) -> List[Tuple[time, time]]:
    """
    Subtract a busy time interval from a free time interval.
    
    ALGORITHM: Handle all possible overlap cases between intervals
    - No overlap: return original interval
    - Complete overlap: return empty list
    - Partial overlap: return remaining segment(s)

    Args:
        free_start: Start time of free interval
        free_end: End time of free interval
        busy_start: Start time of busy interval
        busy_end: End time of busy interval

    Returns:
        List of remaining free time intervals after subtraction
    """
    # No overlap cases
    if busy_end <= free_start or busy_start >= free_end:
        return [(free_start, free_end)]

    # Busy interval completely covers free interval
    if busy_start <= free_start and busy_end >= free_end:
        return []

    # Busy interval is in the middle of free interval (split into two)
    if busy_start > free_start and busy_end < free_end:
        return [(free_start, busy_start), (busy_end, free_end)]

    # Busy interval overlaps the start of free interval
    if busy_start <= free_start and busy_end < free_end:
        return [(busy_end, free_end)]

    # Busy interval overlaps the end of free interval
    if busy_start > free_start and busy_end >= free_end:
        return [(free_start, busy_start)]

    # Default: return original (shouldn't reach here)
    return [(free_start, free_end)]


def truncate_intervals_to_max_hours(
    intervals: List[Tuple[time, time]], max_hours: float
) -> List[Tuple[time, time]]:
    """
    Truncate a list of time intervals to not exceed a maximum total duration.

    Args:
        intervals: List of (start_time, end_time) tuples
        max_hours: Maximum total hours allowed

    Returns:
        Truncated list of intervals
    """
    result = []
    accumulated_hours = 0.0

    for start_time, end_time in intervals:
        interval_hours = (
            datetime.combine(date.min, end_time)
            - datetime.combine(date.min, start_time)
        ).total_seconds() / 3600

        if accumulated_hours >= max_hours:
            break

        if accumulated_hours + interval_hours <= max_hours:
            # This interval fits completely
            result.append((start_time, end_time))
            accumulated_hours += interval_hours
        else:
            # Partial interval - truncate to fit remaining hours
            remaining_hours = max_hours - accumulated_hours
            remaining_seconds = int(remaining_hours * 3600)
            new_end_time = (
                datetime.combine(date.min, start_time)
                + timedelta(seconds=remaining_seconds)
            ).time()
            result.append((start_time, new_end_time))
            accumulated_hours = max_hours
            break

    return result


def filter_by_min_duration(
    intervals: List[Tuple[time, time]], min_duration_hours: float
) -> List[Tuple[time, time]]:
    result = []
    for start_time, end_time in intervals:
        duration_hours = (
            datetime.combine(date.min, end_time)
            - datetime.combine(date.min, start_time)
        ).total_seconds() / 3600
        if duration_hours >= min_duration_hours:
            result.append((start_time, end_time))
    return result


def apply_weekly_limit(
    slots: List[Dict[str, Any]], max_hours_week: float
) -> List[Dict[str, Any]]:
    from collections import defaultdict
    weeks = defaultdict(list)
    for slot in slots:
        slot_date = slot["date"]
        days_since_monday = slot_date.weekday()
        week_start = slot_date - timedelta(days=days_since_monday)
        weeks[week_start].append(slot)
    result = []
    for week_start in sorted(weeks.keys()):
        week_slots = weeks[week_start]
        week_hours = 0.0
        for slot in week_slots:
            slot_hours = (
                datetime.combine(date.min, slot["end_time"])
                - datetime.combine(date.min, slot["start_time"])
            ).total_seconds() / 3600
            if week_hours + slot_hours <= max_hours_week:
                result.append(slot)
                week_hours += slot_hours
            elif week_hours < max_hours_week:
                remaining_hours = max_hours_week - week_hours
                remaining_seconds = int(remaining_hours * 3600)
                new_end_time = (
                    datetime.combine(date.min, slot["start_time"])
                    + timedelta(seconds=remaining_seconds)
                ).time()
                result.append({
                    "date": slot["date"],
                    "day": slot["day"],
                    "start_time": slot["start_time"],
                    "end_time": new_end_time,
                })
                week_hours = max_hours_week
                break
            else:
                break
    return result
