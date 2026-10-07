import os

from pydantic import BaseModel, ValidationError


def review(data: BaseModel, path: str, warnings: list[str] | None = None) -> BaseModel:
    """Dump data to a JSON file, let the user edit it, reload + re-validate."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data.model_dump_json(indent=2))

    for w in warnings or []:
        print(f"⚠️  {w}")

    while True:
        input(f"\nCheck/edit {path}, save, then press Enter to continue...")
        try:
            with open(path, encoding="utf-8") as f:
                # type(data) = whichever schema we were given (Extraction, Timetable, ...)
                return type(data).model_validate_json(f.read())
        except ValidationError as e:
            print("❌ Fix these and try again:\n", e)