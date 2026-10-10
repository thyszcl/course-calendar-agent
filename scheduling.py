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
        3. "timetable has no X running in week N": the class exists, but not in that week (e.g. outline says lab in week 4, but the lab only runs in odd weeks)'''
    
    for s in sessions:                                       
        if s.week is None:                      #For each session in the list, if there is no week associated to it, add it to flagged list
            flagged.append((s, "no week"))
            continue                            #Move on to next session

        candidates = lookup.get((s.module, s.kind), [])             #Get the timetable slots for this session's class --> e.g. session is a BU5101 seminar → get the 3 BU5101 seminar slots. 
        if not candidates:
            flagged.append((s, "no matching class in timetable"))   #If the class isn't in your timetable at all, you get an empty list instead of a crash. Session gets added to flagged and is raised to user.
            continue                            #Move on to next session

        running = slots_for_week(candidates, s.week)                #Call slots_for_week from the slots retreived for the session's class, keep only the ones that happen in this session's week        
        if not running:                                             
            flagged.append((s, f"timetable has no {s.kind} running in week {s.week}"))
            continue                    #If none of the slots happen that week flag it and move on to next session

        # same class listed in several rooms at the same time -> ONE event, rooms merged
        by_time = defaultdict(list) #Another auto-empty-list dictionary, used to group slots by time -- key:(day, start. end), value: list of timetable slots

        for slot in running:
            by_time[(slot.day, slot.start, slot.end)].append(slot)  #Go through each slot that survived/is listed to be happening in that week, put slots with the exact same day, start and end into the same group 

        for (day, start, end), group in by_time.items():                #Go through each group of slots that are happening at the same time
            d = week_monday(s.week) + timedelta(days=DAY_OFFSET[day])   #Find the actual date 
            venues = [g.venue for g in group if g.venue]                #Collect all the venues mentioned
            events.append(CalendarEvent(                                #Make one calendar event and add it to the events list
                title=f"{s.module} {s.kind.title()}: {s.topic}",
                start=datetime.combine(d, time.fromisoformat(start)),
                end=datetime.combine(d, time.fromisoformat(end)),
                location=" / ".join(venues) or None,
                description=s.details,
            ))                                                          #Same code runs even if there is only one slot identified for the session. 

    return events, flagged                                              #Returns list of CalendarEvent Objects and the list of the flagged sessions