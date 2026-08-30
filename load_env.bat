if not exist "%~1" (
    echo [mcp-sequential-thinking] ERROR: env file "%~1" not found
    exit /b
)

:: Read each line, ignoring blank lines or comments (#).
for /f "usebackq delims== tokens=1,*" %%a in ("%~1") do (
    set "key=%%a"
	set "value=%%b"
    :: Remove any excess whitespace and load it into the system.
    if not "!key!"=="" (
        :: Check if the line is not a comment.
        echo !key! | findstr /b "#" >nul
        if errorlevel 1 (
            set "!key!=!value!"
        )
    )
)