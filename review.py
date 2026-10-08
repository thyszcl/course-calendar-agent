import os

from pydantic import BaseModel, ValidationError

#review() is called in outline.py -- Once extraction info from Gemini is received, its written into the specified file path and list of warnings is printed in the terminal
#Once this is done, code then waits for user to make changes to the .json file and press Enter into the terminal. Once this is done, it saves the info in the .json file.
#When review() is called, gemini extraction data is passed in as first argument, second argument is file path and third argument is the list of warnings 

def review(data: BaseModel, path: str, warnings: list[str] | None = None) -> BaseModel:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)       #Makes file based on file.path
    with open(path, "w", encoding="utf-8") as f:                   #Opens the file for writing
        f.write(data.model_dump_json(indent=2))                    #data object received from Gemini is a Pydantic object, .model_dump_json(indent=2) turns it into a JSON string, nicely spaced with indent of 2 across lienes so its readable and not just one giant line of characters

    for w in warnings or []: #If review() was ever called without passing in a warnings list argument, it would be saved as None - in this case the or operator kicks in and it get saved as an empty list instead
        print(f"{w}")

    while True: #Edit and check loop 
        input(f"\nCheck/edit {path}, save, then press Enter to continue...")    #input() generally waits for you to press Enter & returns what every you typed into the terminal.  
        try:
            with open(path, encoding="utf-8") as f:                 #Once user makes edits and presses Enter, code opens the edited file in read mode
                return type(data).model_validate_json(f.read())     #type(data) returns the type of the object passed in. data is the response from Gemini - an Extraction object which is a list of Session objects and a list of Deadline objects
        except ValidationError as e:                                #schema/datatype.model_validate_json() accepts a json object as argument, it uses that json object to fill up a schema/pydantic object and during this process it checks that all the field types match. If it doesnt, it raises the Validation error
            print("Fix these and try again:\n", e)                  #e is the error object, that object contains a list of everything that went wrong -- Pydantic doesn't stop at the first problem. It checks every field and collects all the failures into one error. So if your edited file has three mistakes, e holds all three.

#Under this while loop, when you press Enter, it begins checking the whole checking/validating process within a try/except block. The code in the try block is run if it causes error,
#the error isnt immediately raised instead it gets handled by the except block. Once the code in the except block is run, it goes back to check loop condition and continues with the loop. 
#return type(data).model_validate_json(f.read()) exits the loops when all the checks pass, if any errors are raised it doesnt return and it keeps the loop running.

