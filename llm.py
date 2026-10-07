import os

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

#In current code, Gemini API is called twice, once to extract module timings from the timetable and once more on the course outline to extract deadlines and sessions
#Both gemini api calls follow the same framework the only thing that differes is the file, prompt and the schema. 
#Inside this file is the function/code framework for the api call -- extract() 
#extract() accepts file, prompt and schema as arguments and can be called accordingly depending on whether its for the timetable or the course outline
#extract() is used outline.py and timetable.py for extraction from outline doc and timetable doc

load_dotenv()
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash-lite"


def extract(file_path: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
    """Send a file + prompt to Gemini, get back a validated object of `schema`."""
    uploaded = _client.files.upload(file=file_path)
    response = _client.models.generate_content(
        model=MODEL,
        contents=[uploaded, prompt],
        config={
            "response_mime_type": "application/json",
            "response_schema": schema,
        },
    )
    # validate ourselves so our own field_validators (times, week remarks) run too
    return schema.model_validate_json(response.text)