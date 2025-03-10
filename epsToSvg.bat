@echo off
REM Converting EPS to SVG by Inkscape

setlocal enabledelayedexpansion

set "input_folder=.\in"
set "output_folder=.\out"
set "docTypes_folder=.\docTypes"
set "allowed_chars=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"

if not exist "%input_folder%" (
    echo The folder "%input_folder%" does not exist.
    exit /b 1
)

REM Create the temp folder if it doesn't exist
if not exist "%output_folder%" (
    mkdir "%output_folder%"
)


for %%b in ("%input_folder%\*.eps") do (
    echo Copying "%%b" to out folder...
    copy "%%b" "%output_folder%\" >nul
)


REM Convert all EPS files in the ./in folder to SVG
for %%i in ("%output_folder%\*.eps") do (
    echo Converting "%%i" to SVG...
    inkscape --export-type="svg" "%%i"
)

  REM Delete all EPS files in the folder
  echo Deleting all EPS files in "%output_folder%"...
  del /q "%output_folder%\*.eps
  
  REM Copying the other images in the ./in folder to ./out folder
for %%b in ("%input_folder%\*.svg") do (
    echo Copying "%%b" to out folder...
    copy "%%b" "%output_folder%\" >nul
)

for %%b in ("%input_folder%\*.jpg") do (
    echo Copying "%%b" to out folder...
    copy "%%b" "%output_folder%\" >nul
)

for %%b in ("%input_folder%\*.bmp") do (
    echo Copying "%%b" to out folder...
    copy "%%b" "%output_folder%\" >nul
)

for %%b in ("%docTypes_folder%\*.dtd") do (
    echo Copying "%%b" to out folder...
    copy "%%b" "%output_folder%\" >nul
)


 REM Process all TIF files in the folder
for %%i in ("%output_folder%\*.png" "%output_folder%\*.pdf" "%output_folder%\*.jpg" "%output_folder%\*.bmp" "%output_folder%\*.svg") do (
    REM Extract the original full file path
    set "filepath=%%i"
    REM Extract the filename and extension separately
    set "filename=%%~nxi"

    REM Remove spaces from the filename
    
    set "renamed=!filename: =_!"
    set "renamed=!filename:+=_!"
    
    set "filtered="
    call :filter_chars "!renamed!" filtered
    
    echo Original: "!filename!"
    echo Updated:  "!filtered!"

   if not "!filename!"=="!filtered!" ren "%%i" "!filtered!"
)


echo Conversion completed!
pause


goto :eof

REM Subroutine to filter unwanted characters
:filter_chars
set "input=%~1"
set "output="

:filter_loop
if "%input%"=="" (
    set "%2=%output%"
    goto :eof
)
set "char=%input:~0,1%"
set "input=%input:~1%"
if not "!allowed_chars:%char%=!"=="!allowed_chars!" set "output=!output!!char!"
goto :filter_loop