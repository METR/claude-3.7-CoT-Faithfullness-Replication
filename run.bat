@echo off
REM Configuration - Set your prompt file name here
set PROMPT_FILE=custom_prompt.py

echo Starting evaluation runs with prompt: %PROMPT_FILE%
echo.

REM Create virtual environment if it doesn't exist
echo Checking for virtual environment...
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error creating virtual environment. Please check Python installation.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error activating virtual environment.
    pause
    exit /b 1
)

REM Install requirements
echo Installing/updating requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing requirements.
    pause
    exit /b 1
)

REM Change to src directory
echo Changing to src directory...
cd /d src
if %errorlevel% neq 0 (
    echo Error: src directory not found.
    pause
    exit /b 1
)

REM Start inspect view using python module
echo Starting inspect view in new window...
start "Inspect View" cmd /k "python -m inspect_ai view"

REM Wait a moment for inspect to start
timeout /t 5 /nobreak >nul

REM Open inspect web interface in default browser
echo Opening inspect web interface...
start http://127.0.0.1:7575/

echo.
echo Running monitorability judge...
echo This may take a while - you should see a progress bar.
echo.

REM Run monitorability judge
python main.py --model together/Qwen/Qwen3-235B-A22B-fp8-tput --reasoning_difficulty_model together/Qwen/Qwen3-235B-A22B-fp8-tput --base_model together/Qwen/Qwen3-235B-A22B-fp8-tput --display full --temperature 0.6 --max_connections 60 --free_response --filtered_csv problem_difficulty/claude-opus-4-20250514_hard-math-v0_difficulty.csv --question_prompt utils/question_prompts/%PROMPT_FILE% --judge_prompt utils/judge_prompts/monitorability.py

echo.
echo Monitorability judge completed.
echo.
echo Running faithfulness judge...
echo.

REM Run faithfulness judge  
python main.py --model together/Qwen/Qwen3-235B-A22B-fp8-tput --reasoning_difficulty_model together/Qwen/Qwen3-235B-A22B-fp8-tput --base_model together/Qwen/Qwen3-235B-A22B-fp8-tput --display full --temperature 0.6 --max_connections 60 --free_response --filtered_csv problem_difficulty/claude-opus-4-20250514_hard-math-v0_difficulty.csv --question_prompt utils/question_prompts/%PROMPT_FILE% --judge_prompt utils/judge_prompts/faithfulness_0611.py --score_faithfulness

echo.
echo Both evaluations completed!
echo.
echo The inspect view window should still be open for viewing generations.
echo Press any key to close this window...
pause >nul