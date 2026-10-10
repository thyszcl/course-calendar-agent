import re
from typing import Annotated, Literal
 
from pydantic import BaseModel, BeforeValidator, field_validator
 
# Shared vocabulary: BOTH the outline and the timetable must use these exact words,
# otherwise the join can't match ("TUT" would never equal "tutorial").
Kind = Literal["lecture", "tutorial", "lab", "seminar"]
Day = Literal["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

def clean_module(v):
    if isinstance(v, str):
        return "".join(v.split()).upper()   #Removes whitespace and capitalizes course code to ensure that outline format matches timetable format
    return v

ModuleCode = Annotated[str, BeforeValidator(clean_module)]

#Gemini API call accepts a Pydantic model directly under the response_schema argument. This works better than passing in the schema in the prompt instruction.
#But the prompt instruction input doesnt work as well, when you pass it in thru the prompt sometime it breaks and the error doesnt get raised until its propcessed later on. 
#However when you pass it in as a proper schema, everytime you get data back, Pydantic validates it. If something's off, you get a clear error right there.

#Session schema is the schema for the class info -- lectures, tutorials, labs 

# ---------- course outline ----------
 
class Session(BaseModel):
    module: ModuleCode
    kind: Kind
    week: int | None          # None = outline doesn't say -> gets flagged
    topic: str
    details: str
 
 
class Deadline(BaseModel):
    module: str
    title: str
    week: int | None
    explicit_date: str | None
    due_time: str | None
    requirements: str
    source_quote: str
 
 
class Extraction(BaseModel):
    sessions: list[Session]
    deadlines: list[Deadline]
 
 
# ---------- timetable ----------

#Function that expands remarks in the timetable into an actual list of week numbers
def parse_weeks(remark: str | None) -> set[int] | None: 
    if remark is None:
        return None                 
    weeks: set[int] = set()
    for part in remark.replace(" ", "").removeprefix("Wk").split(","):
        if "-" in part:
            a, b = part.split("-")
            weeks.update(range(int(a), int(b) + 1))
        elif part:
            weeks.add(int(part))
    return weeks
 
#Gemini extracts info from each cell in the timetable: weeks_remarks refers to the extra info under the course name, venue and timing. Gemini purely extracts the remarks text and returns it.
#It is not given the role of expanding it into individual week numbers -- LLMs occasionally mess up these tasks. The expansion part is done manually by the parse_week() function.
class TimetableSlot(BaseModel):                 
    module: str
    kind: Kind
    day: Day
    start: str                # "09:30"
    end: str                  # "11:20"
    venue: str | None
    weeks_remark: str | None  # raw text like "Wk2-13"; None = runs every week

    #pydantic only check types not the actual content/format of the input -- if you want to check for a custom format for a field, you have to use @field_validator -- pass is fields to be checked as argument and write function below that carries out the check
    #Every time a gemini produces output to be created into a timetable slot, fields are validated using this function - if it fails, error is raised
    @field_validator("start", "end")        
    @classmethod    #required syntax for pydantic validators
    def check_time(cls, v: str) -> str:
        if not re.fullmatch(r"\d{2}:\d{2}", v):     #checks that the value looks like xx:xx
            raise ValueError(f"time must look like 09:30, got {v!r}")
        return v
 
    @field_validator("weeks_remark")        
    @classmethod
    def check_weeks(cls, v: str | None) -> str | None:
        parse_weeks(v)                      #calls parse_weeks, if it cannot be parsed then it raises error
        return v

    #used to signify calculated fields within the schema. A property is a calculated field. You access it like a normal field, slot.weeks, but it's not stored anywhere. It's computed fresh from weeks_remark each time you read it - JSON file and Gemini do not every see week, after the whole the whole timetable slot object is validated, a new field is added that is built from calculations on the weeks_remarks field
    @property       
    def weeks(self) -> set[int] | None:
        return parse_weeks(self.weeks_remark)
 

#Each cell in the timetable has its info extracted and expanded -- then they are all put into one list governed by this Timetable schema
class Timetable(BaseModel): 
    slots: list[TimetableSlot]
 