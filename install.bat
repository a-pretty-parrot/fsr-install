@echo off
setlocal enabledelayedexpansion

REM Initialize vars
set "PYTHON_x64=dependencies\python-3.12.4-embed-amd64.zip 8db759b337ac4f6966f52b3662c05dd7"
set "PYTHON_x86=dependencies\python-3.12.4-embed-win32.zip 19691145551a41114b32a556bb2bcb89"
set "NODEJS_x64=dependencies\node-v16.20.2-win-x64.zip f8298627b66ace3d72a2e244373b5fcc"
set "NODEJS_x86=dependencies\node-v16.20.2-win-x86.zip 88ae0baf9d940a3cf9e13773040025af"
set "ARCH="
set "PYTHON_FILE="
set "NODEJS_FILE="
set "PYTHON_MD5_EXPECTED="
set "NODEJS_MD5_EXPECTED="

REM Check and set architecture
echo Checking system architecture...
if "%PROCESSOR_ARCHITECTURE%"=="x86" (
    set "ARCH=x86"
) else if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set "ARCH=x64"
) else (
    echo Error: System must be x86 or x64! Found %PROCESSOR_ARCHITECTURE%. Aborting.
    exit /b 1
)
echo Found architecture: %ARCH%

REM Set variables based on architecture
echo Setting variables based on architecture...
for /f "tokens=1,2 delims= " %%a in ("!PYTHON_%ARCH%!") do (
    set "PYTHON_FILE=%%a"
    set "PYTHON_MD5_EXPECTED=%%b"
)
for /f "tokens=1,2 delims= " %%a in ("!NODEJS_%ARCH%!") do (
    set "NODEJS_FILE=%%a"
    set "NODEJS_MD5_EXPECTED=%%b"
)

REM Print debug information
REM echo PYTHON_FILE=%PYTHON_FILE%
REM echo PYTHON_MD5_EXPECTED=%PYTHON_MD5_EXPECTED%
REM echo NODEJS_FILE=%NODEJS_FILE%
REM echo NODEJS_MD5_EXPECTED=%NODEJS_MD5_EXPECTED%

REM Get MD5 checksums of the zip files
echo Calculating MD5 checksums...
for /f "delims=" %%I in ('powershell -command "Get-FileHash -Path \"%PYTHON_FILE%\" -Algorithm MD5 | ForEach-Object { $_.Hash }"') do set "PYTHON_MD5=%%I"
for /f "delims=" %%I in ('powershell -command "Get-FileHash -Path \"%NODEJS_FILE%\" -Algorithm MD5 | ForEach-Object { $_.Hash }"') do set "NODEJS_MD5=%%I"

REM Check MD5 checksums
echo Checking MD5 checksums...
if /i "!PYTHON_MD5!" neq "!PYTHON_MD5_EXPECTED!" (
    echo Python MD5 checksum does not match. Aborting.
    exit /b 1
)
if /i "!NODEJS_MD5!" neq "!NODEJS_MD5_EXPECTED!" (
    echo NodeJS MD5 checksum does not match. Aborting.
    exit /b 1
)

REM Create directories
echo Creating directories...
mkdir python
mkdir nodejs

REM Unzip files
echo Installing Python...
powershell -command "Expand-Archive -Path \"%PYTHON_FILE%\" -DestinationPath \"python\" -Force"
echo Installing NodeJS...
REM powershell -command "Expand-Archive -Path \"%NODEJS_FILE%\" -DestinationPath \"nodejs\" -Force"

REM Install pip
echo import site >> python\python312._pth
python\python.exe dependencies\get-pip.py --no-warn-script-location

REM Install python depdendencies
python\Scripts\pip.exe install --no-warn-script-location -r fsr\webui\server\requirements.txt
python\Scripts\pip.exe install --no-warn-script-location requests psutil pyserial pyshortcuts winshell

REM Execute installer
@echo off
copy dependencies\squawklib.py python\squawklib.py
@echo on
echo finished installer initialization, executing installer
python\python.exe webui.py --debug --install --arch %ARCH%
