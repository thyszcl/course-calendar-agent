from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pydantic import BaseModel
from schemas import Session, TimetableSlot

# ---- semester config: set these from the academic calendar ----
SEMESTER_START = date(2026, 8, 10)   #Monday of teaching week 1 -- this is the anchor used to calculate the date of every session, deadline etc
RECESS_AFTER_WEEK = 7                #recess week comes after teaching week 7 -- factored into date calculations

DAY_OFFSET = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5}


class CalendarEvent(BaseModel):     #Pydantic schema for a finished, date confirmed event(session or deadline), ready for google calendar
    title: str
    start: datetime                 #full date plus time, like 2026-08-27 15:30.
    end: datetime
    location: str | None
    description: str


def week_monday(week: int) -> date:                 #find the monday of any teaching week
    offset = week - 1
    if week > RECESS_AFTER_WEEK:
        offset += 1                                 #jump over recess week
    return SEMESTER_START + timedelta(weeks=offset) #timedelta(weeks=offset) represents the duration of offset no.of weeks. Adding that to a date moves that date forward


#Only timetable slots for ONE class is passed in as a list --> List of BU5101 seminar slots etc..
def slots_for_week(slots: list[TimetableSlot], week: int) -> list[TimetableSlot]:   #For a given week, checks which slots run in that week for a specific module, takes in a list of all the timetable slots for a specific module and an integer representing a week number, returns a list of timetable slots for that one module for that week
    running = [s for s in slots if s.weeks is None or week in s.weeks] #for each slot, if no weeks is specified or if specified weeks include the input week, add it to the running list

    ''' 
    Filter 1: keep the slots that happen in this week.
    A slot with no weeks listed happens every week, so it's always kept.
    A slot with weeks listed is only kept if this week is one of them.
    
    Filter 2: if an every-week slot is at the same day and time as a slot made
    specifically for this week, drop the every-week one and keep the specific one.
    Slots at different days or times don't affect each other, so they're all kept
    '''
    
     
    specific = {(s.day, s.start) for s in running if s.weeks is not None}  #For every slot in running where a specific week number is specified, that slots day and timing is added to set
    return [s for s in running if s.weeks is not None or (s.day, s.start) not in specific] #for each slot in running if it has a specific week stated, add that to the final list, then, for slots without a specific week, check if its day and timing is in the specific set, if no: add into final list else do not

def time_groups(running: list[TimetableSlot]):  #Pass in a list of slots that run within a certain week for one class
    by_time = defaultdict(list)                 #Create a dictionary -- it will group together slots that occupy the same time 
    for slot in running:
        by_time[(slot.day, slot.start, slot.end)].append(slot)
    return sorted(by_time.items(), key=lambda item: (DAY_OFFSET[item[0][0]], item[0][1]))   #returns a list of ((day, start, end), [slots]) pairs -- sorted earliest first (by day, then start time)


def make_event(s: Session, day: str, start: str, end: str, group: list[TimetableSlot]): #Builds a finished CalendarEvent object from a matched session object and timetable slot object/multiple timetable slot objects
    d = week_monday(s.week) + timedelta(days=DAY_OFFSET[day])                           #Monday of that teaching week plus the day offset gives the actual date.
    venues = [g.venue for g in group if g.venue]                                        #All venues are combined into one list
    return CalendarEvent(
        title=f"{s.module} {s.kind.title()}: {s.topic}",
        start=datetime.combine(d, time.fromisoformat(start)),
        end=datetime.combine(d, time.fromisoformat(end)),
        location=" / ".join(venues) or None,
        description=s.details,
    )

def build_session_events(sessions: list[Session], slots: list[TimetableSlot]):
    #Called in main.py -- main.py combines session objects from every verified module into one list and passes that in when calling this function 

    #lookup is an empty dictionary -- for each new key added, empty list is associated as value
    lookup = defaultdict(list)

    for slot in slots:                                  #Goes through every slot in your timetable one by one -- Puts the slot into the list for its class 
        lookup[(slot.module, slot.kind)].append(slot)   #E.g: Key is ('BU5101', 'Seminar') - any BU5101 Seminar timetable slot object is appended into the list stored as value. If any (slot.module, slot.kind) key doesnt exist, its added on the spot

    events: list[CalendarEvent] = []                    #Empty list to collect events to be made
    flagged: list[tuple[Session, str]] = []             #Empty list to store sessions that couldnt be placed --NOTE: All session should be placed, not all timetable slots will match up to a session hence not all timetable slots will be used BUT ALL EXTRACTED SESSION SHOULD BE PLACED -- if its not, there is missing info that user needs to provide

    '''Reasons a session gets flagged:
        1. "no week": the outline didn't say which week
        2. "no matching class in timetable": that module + kind isn't in your timetable AT ALL (e.g. outline has a BU5101 lecture, timetable has no BU5101 lecture in any week)
        3. "timetable has no X running in week N": the class exists, but not in that week (e.g. outline says lab in week 4, but the lab only runs in odd weeks)
        4. "N sessions in week W but M timetable slots": counts don't line up, so any pairing would be a guess'''
    
    week_groups = defaultdict(list)
    for s in sessions:      #For each session in s, group them togehter by the modele, kind and the week in which it occurs -- E.g: 2 SC2001 Lectures per week get grouped together
        if s.week is None:
            flagged.append((s, "no week"))
            continue
        week_groups[(s.module, s.kind, s.week)].append(s)   #Key = tuple of session name, kind and week -- value = list of Session objects for that class in that week, in outline order

    for (module, kind, week), group_sessions in week_groups.items():    #week_group is a dict -- key = tuple of session name, kind and week -- value = list of corresponding session slots
        candidates = lookup.get((module, kind), [])                     #candidates is a list of every timetable slot for each (module + kind), if there are no corresponding timtable slots, it returns an empty list
        if not candidates:
            flagged += [(s, "no matching class in timetable") for s in group_sessions]  #If a session has no corresponding slots in the timetable, add it to flagged list as a tuple (session object, reason)
            continue

        running = slots_for_week(candidates, week)                      #Check the weekly slots for the session -- pass in a list of the timetable slots for that module, pass in the week number
        if not running:                                                 #If there no slots that week for the module but session object has it listed for that week, it is added to flagged
            flagged += [(s, f"timetable has no {kind} running in week {week}") for s in group_sessions]
            continue

        times = time_groups(running)     #For all the timetable slots identified for a session in a week, group the ones that occupy the same time slot 

        if len(group_sessions) == len(times):                                #group_sessions is the list of session slots for a given session in one week, value of the week_groups dictionary
            for s, ((day, start, end), group) in zip(group_sessions, times): #If each session corresponds to one timetable slot -- they are assigned to each other by their order, CalendarEvent is made and appended to events list
                events.append(make_event(s, day, start, end, group))

        elif len(group_sessions) == 1:                                  
            s = group_sessions[0]                                            #If there is only session slot and there are several timetable slots/ one timetable slot -- the singular session slot is assigned to all the eligible timetable slots and calendarEvent is created and appended to events
            for (day, start, end), group in times:
                events.append(make_event(s, day, start, end, group))

        else:                                                               #Any other case -- e.g: More sessions that available slots/times -- all the sessions get added to flagged
            reason = f"{len(group_sessions)} {kind} sessions in week {week} but {len(times)} timetable slots"
            flagged += [(s, reason) for s in group_sessions]                                                    

    return events, flagged                                              #Returns list of CalendarEvent Objects and the list of the flagged sessions


'''
===================== HOW scheduling.py WORKS (full flow) =====================

GOAL: turn Session objects (WHAT happens, from course outlines) into CalendarEvent
objects (WHEN + WHERE, using the timetable). The course outline decides which
events exist; the timetable only supplies day, time and venue.

INPUT  (from main.py):
  - sessions: every Session from every verified outline, combined into one list
  - slots:    every TimetableSlot from the verified timetable
OUTPUT:
  - events:   list of finished CalendarEvents (real date + time + venue)
  - flagged:  list of (session, reason) pairs that couldn't be placed

STEP 1 - Build the address book (lookup)
  Group every timetable slot by (module, kind).
  e.g. ("SC2001", "lecture") -> [Mon slot, Thu slot]

STEP 2 - Group the sessions (week_groups)
  Sessions with no week are flagged immediately ("no week").
  The rest are grouped by (module, kind, week), keeping outline order.
  e.g. ("SC2001", "lecture", 3) -> [Heaps, Heapsort]

STEP 3 - For each session group, narrow down the timetable slots:
  a) candidates = lookup[(module, kind)]
       -> every slot for this class, any week
       -> empty? flag all sessions in the group ("no matching class in timetable")
  b) running = slots_for_week(candidates, week)
       -> keep only slots that run this week (no week remark = every week)
       -> a week-specific slot overrides an every-week slot at the same day+time
       -> empty? flag all sessions ("timetable has no X running in week N")
  c) times = time_groups(running)
       -> merge slots at the same day+time into one group (same class, several rooms)
       -> sort the groups earliest first (by day, then start time)

STEP 4 - Pair sessions with time groups:
  - same count       -> pair by position: 1st session -> earliest group, 2nd -> next...
  - 1 session, many  -> one topic for the week, so it goes on every time group
  - anything else    -> can't pair safely, flag all sessions ("N sessions but M slots")

STEP 5 - Build each event (make_event)
  date     = week_monday(week) + DAY_OFFSET[day]   (week_monday skips recess week)
  start/end = date + the slot's start/end time
  title/description come from the SESSION; time/venue come from the TIMETABLE
  venues from the same time group are joined with " / "

Every session ends up in exactly one place: events or flagged.
Unused timetable slots are normal (the outline decides which weeks have classes).
================================================================================
'''