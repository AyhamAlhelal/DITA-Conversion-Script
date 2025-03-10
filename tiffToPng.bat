@echo off
REM Converting TIFF to PNG by Inkscape

setlocal enabledelayedexpansion

set "input_folder=.\in"
set "output_folder=.\out"
set "allowed_chars=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"

if not exist "%input_folder%" (
    echo The folder "%input_folder%" does not exist.
    exit /b 1
)


REM Create the temp folder if it doesn't exist
if not exist "%output_folder%" (
    mkdir "%output_folder%"
)


for %%b in ("%input_folder%\*.tif") do (
    echo Copying "%%b" to out folder...
    copy "%%b" "%output_folder%\" >nul
)

REM Converting all TIF files in the ./in folder to PDF 
 for %%i in ("%output_folder%\*.tif") do (
    echo Converting "%%i" to PDF with
    magick "%%i"  "%%~dpni.pdf" 
 )

REM Converting all PDF files in the ./in folder to PNG
 for %%i in ("%output_folder%\*.pdf") do (
  echo Converting "%%i" to PNG at highest resolution...
  inkscape  "%%i" --export-type=png --export-dpi=300 --export-area-page --export-filename="%%~dpi%%~ni.png"
 )
 
  REM Delete all PDF files in the folder
  echo Deleting all PDF files in "%output_folder%"...
  del /q "%output_folder%\*.pdf
  
    REM Delete all TIF files in the folder
  echo Deleting all TIF files in "%output_folder%"...
  del /q "%output_folder%\*.tif

 
 for %%b in ("%input_folder%\*.pdf") do (
    echo Copying "%%b" to out folder...
    copy "%%b" "%output_folder%\" >nul
)
 
 for %%b in ("%input_folder%\*.png") do (
    echo Copying "%%b" to out folder...
    copy "%%b" "%output_folder%\" >nul
)

 REM Process all TIF files in the folder
for %%i in ("%output_folder%\*.png" "%output_folder%\*.pdf" "%output_folder%\*.svg") do (
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