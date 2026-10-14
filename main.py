from outline import load_outlines
from scheduling import build_session_events
from timetable import load_timetable
from scheduling import build_deadline_events, build_session_events

#main.py doesnt reaaly do anything the actuay extraction and reviewing and everything is done in outlines.py/timetable.py/review.py
#This code just presents info from already verified timetables/outlines in the terminal
def main():
    # just loads verified files: no Gemini, no review pauses
    timetable = load_timetable()
    outlines = load_outlines()     #list of extraction objects
    sessions = []
    deadlines = []
    for outline in outlines:
        sessions.extend(outline.sessions)
        deadlines.extend(outline.deadlines)

    session_events, flagged_sessions = build_session_events(sessions, timetable.slots)
    deadline_events, flagged_deadlines = build_deadline_events(deadlines)
    events = session_events + deadline_events
    #Prints a preview of all events

    print(f"\n===== PREVIEW: {len(session_events)} sessions + {len(deadline_events)} deadlines =====")
    for e in sorted(events, key=lambda e: e.start):
        if e.all_day:
            print(f"{e.start:%a %d %b}  (all day)    {e.title}")
        else:
            print(f"{e.start:%a %d %b %H:%M}-{e.end:%H:%M}  {e.title}  @ {e.location}")

    if flagged_sessions:
        print(f"\n===== FLAGGED SESSIONS: {len(flagged_sessions)} (won't be added) =====")
        for s, reason in flagged_sessions:
            print(f"⚠️  {s.module} {s.kind} wk{s.week} – {s.topic}  →  {reason}")

    if flagged_deadlines:
        print(f"\n===== FLAGGED DEADLINES: {len(flagged_deadlines)} (won't be added) =====")
        for d, reason in flagged_deadlines:
            print(f"⚠️  {d.module} – {d.title}  →  {reason}")