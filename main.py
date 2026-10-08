from outline import load_outlines
from scheduling import build_session_events
from timetable import load_timetable


def main():
    # just loads verified files: no Gemini, no review pauses
    timetable = load_timetable()
    outlines = load_outlines()

    # combine sessions from every module into one list
    sessions = []
    for outline in outlines:
        sessions.extend(outline.sessions)

    events, flagged = build_session_events(sessions, timetable.slots)

    print(f"\n===== PREVIEW: {len(events)} session events =====")
    for e in sorted(events, key=lambda e: e.start):
        print(f"{e.start:%a %d %b %H:%M}-{e.end:%H:%M}  {e.title}  @ {e.location}")

    if flagged:
        print(f"\n===== FLAGGED: {len(flagged)} (won't be added) =====")
        for s, reason in flagged:
            print(f"{s.module} {s.kind} wk{s.week} – {s.topic}  →  {reason}")


if __name__ == "__main__":
    main()