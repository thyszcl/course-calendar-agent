from outline import load_outlines
from scheduling import build_session_events
from timetable import load_timetable

#main.py doesnt reaaly do anything the actuay extraction and reviewing and everything is done in outlines.py/timetable.py/review.py
#This code just presents info from already verified timetables/outlines in the terminal
def main():
    # just loads verified files: no Gemini, no review pauses
    timetable = load_timetable()
    outlines = load_outlines()     #list of extraction objects

    #combine sessions from every module/outline file into one list
    sessions = []                           #list of session objects
    for outline in outlines:                #Each extraction object has one list of session objects and one list of deadline objects           
        sessions.extend(outline.sessions)   #Each sessions list from the extraction object is taken and added to the sessions list 

    events, flagged = build_session_events(sessions, timetable.slots)   
    print(f"\n===== PREVIEW: {len(events)} session events =====")
    for e in sorted(events, key=lambda e: e.start):
        print(f"{e.start:%a %d %b %H:%M}-{e.end:%H:%M}  {e.title}  @ {e.location}")

    if flagged:
        print(f"\n===== FLAGGED: {len(flagged)} (won't be added) =====")
        for s, reason in flagged:
            print(f" {s.module} {s.kind} wk{s.week} – {s.topic}  →  {reason}")


if __name__ == "__main__":
    main()