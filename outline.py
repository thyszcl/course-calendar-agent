import glob     #module built into Python for finding files by pattern --> glob.glob is the function that does the searching 
import os
import sys

from llm import extract
from review import review
from schemas import Extraction

#outline.py reads the semester plan: what happens in each specific week. "Week 3 tutorial: mergesort", "Lab report due week 6". It's different every week and covers the whole semester, including deadlines.
#timetable.py reads the weekly pattern: "SC2001 tutorial is Friday 15:30–16:20 in TR+3". It's the same slots repeating week after week.

OUTLINE_DIR = "review/outlines"   #used by glob.glob to search for verified json files in load_outlines()


OUTLINE_PROMPT = """You are extracting a university course schedule.
From the attached course outline, extract:
- every lecture, tutorial, lab and seminar, one entry per week it occurs
- every submission/deadline (assignments, reports, quizzes, projects)

Rules:
- Use teaching week numbers only. Do NOT convert weeks to calendar dates.
- If the outline gives an actual date for a deadline, put it in explicit_date.
- If something isn't stated (including the week), use null. Never guess.
- source_quote must be copied exactly from the outline.
"""


def extract_outline(file_path: str) -> Extraction:                              #function takes in string file_path and outputs object that fits the Extraction schema 
    name = os.path.splitext(os.path.basename(file_path))[0]                     #os.path.basename(file_path) -- extracts the file name from the path, os.path.splitext("SC2001.pdf") splits the name from the its extension and returns a tuple of the name and the extension, [0] is used to access the name.
    draft_path = f"{OUTLINE_DIR}/{name}_draft.json"                             #Initial info extracted by gemini gets stored in this draft file, user can make changes to this, once these changes are validated by the pydantic schema, finalized info will be stored in verified file.
    verified_path = f"{OUTLINE_DIR}/{name}_verified.json"

    print(f"Extracting {file_path}...")                                         #call extract function that extracts info from course outline document -- pass in file path, prompt and schema
    result = extract(file_path, OUTLINE_PROMPT, Extraction)                     #Output from the gemini api call is saved under the result variable

    warnings = []                                                               #For each session or deadline that is extracted some key info may be missing, identify missing ones and raise them to user 
    for s in result.sessions:
        if s.week is None:                                                              #checks each session's week slot 
            warnings.append(f"NO WEEK  session: {s.module} {s.kind} – {s.topic}")
    for d in result.deadlines:
        if d.week is None and d.explicit_date is None:                                  #checks each deadline's week and date slot 
            warnings.append(f"NO WEEK  deadline: {d.module} – {d.title}")

    verified = review(result, draft_path, warnings)                             #calls review function from review.py -- writes output from gemini(result) into the specified file(second arg), list of warnings(third argument)/ fields to flag is printed in the terminal, wait for user to make changes, validates the changed info               
    with open(verified_path, "w", encoding="utf-8") as f:                       #Once review procedure finishes & all changes are validated by schema, all the info is transfered to the verified folder
        f.write(verified.model_dump_json(indent=2))                             
    print(f"Saved {verified_path}")
    return verified

#Current procedure --> Results get saved into the draft .json file, Warnings are printed on the terminal, user can and make edits in the json file to address the warnings. 
#Once done, they hit enter - schema checks are carried out to ensure all fields are valid then everything gets written into verified .json file, then the program proceeds 


#Loads info/extraction object from every verified outline into a list called outlines, called by main.py
def load_outlines() -> list[Extraction]:
    paths = sorted(glob.glob(f"{OUTLINE_DIR}/*_verified.json")) #saves a list of file paths that have the specified directory in their file path and end with _verified.json e.g: ["review/outlines/SC2001_verified.json", "review/outlines/SC3000_verified.json"]
    if not paths:                                               #if the paths list comes up empty then there are no verified course outlines 
        sys.exit("No verified outlines yet. Run: python outline.py <outline.pdf>")
    outlines = []
    for path in paths:
        with open(path, encoding="utf-8") as f:                         #Opens each file specified in paths list in read mode
            outlines.append(Extraction.model_validate_json(f.read()))   #NOTE: Each file holds exactly one extraction object. f.read() reads the whole file/extraction object in the file validates it against the extraction schema with .model_validate_json, then appends it to outlines list
    return outlines


if __name__ == "__main__":
        file_path = 'outlines\\SC2001.pdf'
        extract_outline(file_path)
