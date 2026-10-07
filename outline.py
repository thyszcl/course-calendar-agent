import os

from llm import extract
from review import review
from schemas import Extraction

#Prompt to extract info from course outline document
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


def get_outline(file_path: str) -> Extraction:                              #function takes in string file_path and outputs object that fits the Extraction schema 
    result = extract(file_path, OUTLINE_PROMPT, Extraction)                 #call extract function that extracts info from course outline document -- pass in file path, prompt and schema
                                                                            #Output from the gemini api call is saved under the result variable

    warnings = []                                                           #For each session or deadline that is extracted some key info may be missing, identify missing ones and raise them to user 
    for s in result.sessions:
        if s.week is None:                                                          #checks each session's week slot 
            warnings.append(f"NO WEEK  session: {s.module} {s.kind} – {s.topic}")
    for d in result.deadlines:                                                      #checks each deadline's week and date slot 
        if d.week is None and d.explicit_date is None:
            warnings.append(f"NO WEEK  deadline: {d.module} – {d.title}")

    name = os.path.splitext(os.path.basename(file_path))[0]  #os.path.basename(file_path) -- extracts the file name from the path, os.path.splitext("SC2001.pdf") splits the name from the its extension and returns a tuple of the name and the extension, [0] is used to access the name
    return review(result, f"review/{name}.json", warnings)   #calls review function from review.py -- writes output from gemini(result) into the specified file(second arg), list of warnings(third argument)/ fields to flag is printed in the terminal.
#Current procedure --> Results get saved into the .json file, Warnings are printed on the terminal, user can and make edits in the json file to address the warnings. Once done, they print enter, then the program proceeds (Havent coded yet)