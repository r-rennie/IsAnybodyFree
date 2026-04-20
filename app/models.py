"""Data structures for student availability and recommendations."""

from dataclasses import dataclass


@dataclass
class ScheduleBlock:
    participant_name: str
    participant_email: str
    day: str
    start_time: str
    end_time: str
    block_type: str  # e.g. "Class", "Work", "Other"


@dataclass
class Recommendation:
    start_time: str
    end_time: str
    score: float
