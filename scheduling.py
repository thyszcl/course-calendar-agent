from collections import defaultdict
from datetime import date, datetime, time, timedelta

from pydantic import BaseModel

from schemas import Session, TimetableSlot

# ---- semester config: set these from the academic calendar ----
SEMESTER_START = date(2026, 8, 10)   # Monday of teaching week 1 (CHECK THIS)
RECESS_AFTER_WEEK = 7                # recess week comes after teaching week 7

DAY_OFFSET = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5}


class CalendarEvent(BaseModel):
    title: str
    start: datetime
    end: datetime
    location: str | None
    description: str


def week_monday(week: int) -> date:
    offset = week - 1
    if week > RECESS_AFTER_WEEK:
        offset += 1                  # jump over recess week
    return SEMESTER_START + timedelta(weeks=offset)


def slots_for_week(slots: list[TimetableSlot], week: int) -> list[TimetableSlot]:
    """Keep only slots that actually run in this teaching week."""
    running = [s for s in slots if s.weeks is None or week in s.weeks]

    # a slot listed for specific weeks overrides an "every week" slot at the same time
    # (e.g. BU5101 seminar moves to a different room in Wk8 and Wk13)
    specific = {(s.day, s.start) for s in running if s.weeks is not None}
    return [s for s in running if s.weeks is not None or (s.day, s.start) not in specific]


def build_session_events(sessions: list[Session], slots: list[TimetableSlot]):
    # address book: (module, kind) -> all its slots
    lookup = defaultdict(list)
    for slot in slots:
        lookup[(slot.module, slot.kind)].append(slot)

    events: list[CalendarEvent] = []
    flagged: list[tuple[Session, str]] = []

    for s in sessions:                                    # loop over the GUEST LIST
        if s.week is None:
            flagged.append((s, "no week"))
            continue

        candidates = lookup.get((s.module, s.kind), [])
        if not candidates:
            flagged.append((s, "no matching class in timetable"))
            continue

        running = slots_for_week(candidates, s.week)
        if not running:
            flagged.append((s, f"timetable has no {s.kind} running in week {s.week}"))
            continue

        # same class listed in several rooms at the same time -> ONE event, rooms merged
        by_time = defaultdict(list)
        for slot in running:
            by_time[(slot.day, slot.start, slot.end)].append(slot)

        for (day, start, end), group in by_time.items():
            d = week_monday(s.week) + timedelta(days=DAY_OFFSET[day])
            venues = [g.venue for g in group if g.venue]
            events.append(CalendarEvent(
                title=f"{s.module} {s.kind.title()}: {s.topic}",
                start=datetime.combine(d, time.fromisoformat(start)),
                end=datetime.combine(d, time.fromisoformat(end)),
                location=" / ".join(venues) or None,
                description=s.details,
            ))

    return events, flagged