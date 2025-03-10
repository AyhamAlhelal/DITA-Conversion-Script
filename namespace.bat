@echo off
setlocal enabledelayedexpansion

:: Define the directory (modify if needed)
set "TARGET_DIR=out"

:: Check if the  folder exists
if not exist "%TARGET_DIR%" (
    echo Folder "%TARGET_DIR%" not found!
    exit /b
)

:: Process all XML and DITAMAP files in the folder
for %%F in ("%TARGET_DIR%\*.xml" "%TARGET_DIR%\*.ditamap") do (
    echo Processing: %%F
    
    :: Create a temp file
    set "TMP_FILE=%%F.tmp"

    :: Remove the xsi namespace declaration
    powershell -Command "(Get-Content '%%F') -replace ' xmlns:xsi=\""http://www.w3.org/2001/XMLSchema-instance\""', '' | Set-Content '!TMP_FILE!'"

    :: Replace the original file with the cleaned one
    move /Y "!TMP_FILE!" "%%F" >nul
)

:: Process all XML and DITAMAP files in the folder
for %%F in ("%TARGET_DIR%\*.xml" "%TARGET_DIR%\*.ditamap") do (
    echo Processing: %%F
    
    :: Create a temp file
    set "TMP_FILE=%%F.tmp"

    :: Remove the xsi namespace declaration
    powershell -Command "(Get-Content '%%F') -replace ' xmlns:atict=\""http://www.arbortext.com/namespace/atict\""', '' | Set-Content '!TMP_FILE!'"

    :: Replace the original file with the cleaned one
    move /Y "!TMP_FILE!" "%%F" >nul
)


echo Done!