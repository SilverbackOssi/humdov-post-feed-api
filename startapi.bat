@echo off
REM Activate virtual environment if it exists
IF EXIST "venv\Scripts\activate.bat" (
	call venv\Scripts\activate.bat
)

REM Start the FastAPI server with uvicorn
uvicorn app.main:app --reload
