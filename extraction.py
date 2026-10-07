from google import genai
import os
from dotenv import load_dotenv

load_dotenv()



#Since Gemini is multimodal, it will be able to extract info from the file regardless of what format its in

FILE_PATH = "SC2001.pdf"   # replaces OUTLINE_TEXT

PROMPT = """You are extracting a university course schedule.
From the attached course outline, extract:
- every lecture, tutorial and lab, one entry per week it occurs
- every submission/deadline (assignments, reports, quizzes, projects)

Rules:
- Use teaching week numbers only. Do NOT convert weeks to calendar dates.
- If the outline gives an actual date for a deadline, put it in explicit_date.
- If something isn't stated, use null. Never guess.
- source_quote must be copied exactly from the outline.
"""

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  # reads your GEMINI_API_KEY env var

uploaded = client.files.upload(file=FILE_PATH)

response = client.models.generate_content(
    model="gemini-3.5-flash",  
    contents=[uploaded, PROMPT],
    config={
        "response_mime_type": "application/json",
        "response_schema": Extraction,
    },
)

result: Extraction = response.parsed

for s in result.sessions:
    print(s.week, s.kind, s.topic)
for d in result.deadlines:
    print(d.title, d.week, d.due_time)
