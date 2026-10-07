import os

from llm import extract
from review import review
from schemas import Extraction

# paste your own tuned prompt here if you changed it since the first run
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


def get_outline(file_path: str) -> Extraction:
    print(f"Extracting {file_path}...")
    result = extract(file_path, OUTLINE_PROMPT, Extraction)

    warnings = []
    for s in result.sessions:
        if s.week is None:
            warnings.append(f"NO WEEK  session: {s.module} {s.kind} – {s.topic}")
    for d in result.deadlines:
        if d.week is None and d.explicit_date is None:
            warnings.append(f"NO WEEK  deadline: {d.module} – {d.title}")

    name = os.path.splitext(os.path.basename(file_path))[0]
    return review(result, f"review/{name}.json", warnings)