from typing import Literal
from pydantic import BaseModel
from google import genai

#Since Gemini is multimodal, it will be able to extract info from the file regardless of what format its in
OUTLINE_TEXT = """
Week 3 – Tutorial 1: Mergesort analysis. Attempt Q1–Q5 before class.
Week 6 – Lab report 1 due Friday 23:59 via NTULearn.
"""

#Gemini API call accepts a Pydantic model directly under the response_schema argument. This works better than passing in the schema in the prompt instruction.
#But the prompt instruction input doesnt work as well, when you pass it in thru the prompt sometime it breaks and the error doesnt get raised until its propcessed later on. 
#However when you pass it in as a proper schema, everytime you get data back, Pydantic validates it. If something's off, you get a clear error right there.

#Session schema is the schema for the class info -- lectures, tutorials, labs 
class Session(BaseModel): 
    module: str
    kind: Literal["lecture", "tutorial", "lab"]
    week: int
    topic: str
    details: str

#Deadline schema is the schema for the deliverable info -- like assignments, due dates etc etc
class Deadline(BaseModel):
    module: str
    title: str
    week: int | None
    explicit_date: str | None
    due_time: str | None
    requirements: str
    source_quote: str

#Wrapper for schemas since Gemini returns ONE object
class Extraction(BaseModel):
    sessions: list[Session]
    deadlines: list[Deadline]


