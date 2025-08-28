@echo off
echo Running Humdov API tests...

rem Process command-line arguments
set TEST_TYPE=api
set CONCURRENT=false

if "%1"=="--test-type" (
    if "%2"=="concurrent" set TEST_TYPE=concurrent
    if "%2"=="all" set TEST_TYPE=all
)

if "%1"=="--concurrent" set CONCURRENT=true
if "%3"=="--concurrent" set CONCURRENT=true

rem Run the tests using the Python script
python run_api_tests.py --test-type %TEST_TYPE% %CONCURRENT:true=--concurrent%

echo Test execution complete.
