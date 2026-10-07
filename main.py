from outline import get_outline
from scheduling import build_session_events
from timetable import get_timetable

TIMETABLE_FILE = "outlines\\Timetable Y2S1.pdf"
OUTLINE_FILE = "outlines\\SC2001.pdf"


def main():
    timetable = get_timetable(TIMETABLE_FILE)
    outline = get_outline(OUTLINE_FILE)

    events, flagged = build_session_events(outline.sessions, timetable.slots)

    print(f"\n===== PREVIEW: {len(events)} session events =====")
    for e in sorted(events, key=lambda e: e.start):
        print(f"{e.start:%a %d %b %H:%M}-{e.end:%H:%M}  {e.title}  @ {e.location}")

    if flagged:
        print(f"\n===== FLAGGED: {len(flagged)} (won't be added) =====")
        for s, reason in flagged:
            print(f"⚠️  {s.module} {s.kind} wk{s.week} – {s.topic}  →  {reason}")


if __name__ == "__main__":
    main()