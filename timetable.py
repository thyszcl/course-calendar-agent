import os
import sys

from llm import extract
from review import review
from schemas import Timetable


#outline.py reads the semester plan: what happens in each specific week. "Week 3 tutorial: mergesort", "Lab report due week 6". It's different every week and covers the whole semester, including deadlines.
#timetable.py reads the weekly pattern: "SC2001 tutorial is Friday 15:30–16:20 in TR+3". It's the same slots repeating week after week.

TIMETABLE_DRAFT = "review/timetable_draft.json"             #draft is Gemini's raw output
TIMETABLE_VERIFIED = "review/timetable_verified.json"       #verified file is written only after user makes edits, saves and the edits pass the validation. 

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


def extract_timetable(file_path: str) -> Timetable:
    print("Extracting timetable...")
    draft = extract(file_path, TIMETABLE_PROMPT, Timetable)         #calls the extract function on the timetable -- file_path, prompt and schema passed in as arguments. output saved in draft variable
    verified = review(                       #Extraction from timetable with gemini is passed review() --> review() dumps it into draft file, warning printed, user given time to edit --> review() returns the pydantic object of validated data
        draft,
        TIMETABLE_DRAFT,
        warnings=["Double-check the DAY of every slot. That's the easiest thing to misread."],
    )
    with open(TIMETABLE_VERIFIED, "w", encoding="utf-8") as f:      #Once validated data is received from review(), it is dumped into the verified file
        f.write(verified.model_dump_json(indent=2))
    print(f"Saved {TIMETABLE_VERIFIED}")
    return verified

#Loads info from verified timetable and returns a timetable object, called by main.py, gets saved under timetable variable 
def load_timetable() -> Timetable:
    if not os.path.exists(TIMETABLE_VERIFIED):      #if no timetable_verified.json file exists, sys.exit() prints a given message and exits program
        sys.exit("No verified timetable yet. Run: python timetable.py <timetable.pdf>")
    with open(TIMETABLE_VERIFIED, encoding="utf-8") as f:   #Opens file specified in read mode
        return Timetable.model_validate_json(f.read())      #NOTE: Each file holds exactly one timetable object. f.read() reads the whole file/timetable object in the file and validates it against the schema with .model_validate_json


if __name__ == "__main__":
        file_path = 'outlines\\Timetable Y2S1.pdf'
        extract_timetable(file_path)