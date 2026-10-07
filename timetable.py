import os

from llm import extract
from review import review
from schemas import Timetable

TIMETABLE_CACHE = "review/timetable_verified.json"
TIMETABLE_DRAFT = "review/timetable_draft.json"

TIMETABLE_PROMPT = """You are reading a university timetable laid out as a grid.
Columns are days (MON..SAT). Each cell is one class slot.

Extract every class slot in the grid:
- day: the COLUMN the cell sits in.
- start/end: use the time written INSIDE the cell (e.g. "0930to1120" -> start "09:30",
  end "11:20"). Do NOT use the row labels on the left edge.
- kind: LEC/STU -> lecture, TUT -> tutorial, LAB -> lab, SEM -> seminar.
- module: the course code, e.g. "SC2001".
- venue: the room, e.g. "LT1A", "TR+18", "ONLINE".
- weeks_remark: copy the week remark exactly, e.g. "Wk2-13" or "Wk2,4,6,8,10,12".
  If the cell has no week remark, use null.
- If the same class appears in several cells (e.g. several rooms), output one slot per cell.

Ignore the course list table below the grid.
"""


def get_timetable(file_path: str) -> Timetable:
    # timetable doesn't change during the semester: verify once, reuse after
    if os.path.exists(TIMETABLE_CACHE):
        if input("Found a verified timetable. Reuse it? (y/n) ").strip().lower() == "y":
            with open(TIMETABLE_CACHE, encoding="utf-8") as f:
                return Timetable.model_validate_json(f.read())

    print("Extracting timetable...")
    draft = extract(file_path, TIMETABLE_PROMPT, Timetable)
    verified = review(
        draft,
        TIMETABLE_DRAFT,
        warnings=["Double-check the DAY of every slot. That's the easiest thing to misread."],
    )

    # only save to the cache AFTER it passed review
    with open(TIMETABLE_CACHE, "w", encoding="utf-8") as f:
        f.write(verified.model_dump_json(indent=2))
    return verified