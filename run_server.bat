@echo off

setlocal enabledelayedexpansion

:: ===========================================================================
:: run_server.bat - launch the sequential-thinking MCP server.
::
:: ALL machine-specific config lives in .env (VENV_PATH, TRANSPORT_TYPE,
:: MCP_HOST, MCP_PORT). Edit that file, not this script. See .env.example.
:: ===========================================================================

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

:: fixed python output settings (constants, not user config)
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"

:: --- load config from .env -------------------------------------------------
if not exist "load_env.bat" (
    echo [mcp-sequential-thinking] ERROR: load_env.bat not found next to this script.
    set "RC=1"
    goto :end
)
if not exist ".env" (
    echo [mcp-sequential-thinking] ERROR: .env not found - copy .env.example and edit it.
    set "RC=1"
    goto :end
)
call load_env.bat .env

if not defined TRANSPORT_TYPE set "TRANSPORT_TYPE=stdio"
if not defined MCP_HOST set "MCP_HOST=127.0.0.1"
if not defined MCP_PORT set "MCP_PORT=8804"

if not defined VENV_PATH (
    echo [mcp-sequential-thinking] ERROR: VENV_PATH not set in .env.
    set "RC=1"
    goto :end
)
if not exist "%VENV_PATH%\Scripts\python.exe" (
    echo [mcp-sequential-thinking] ERROR: venv not found at "%VENV_PATH%".
    echo   Fix VENV_PATH in .env.
    set "RC=1"
    goto :end
)

:: --- launch ----------------------------------------------------------------
:: TRANSPORT_TYPE=stdio spawns per client (no network); sse / streamable-http bind
:: MCP_HOST:MCP_PORT and must run as a standalone process (start-network-mcp-servers.ps1
:: starts those). The package is installed into the shared venv by setup, so plain
:: `python -m` is enough - no uv at runtime.
if /I not "%TRANSPORT_TYPE%"=="stdio" echo Starting mcp-sequential-thinking (%TRANSPORT_TYPE%) on %MCP_HOST%:%MCP_PORT% ...

"%VENV_PATH%\Scripts\python.exe" -m mcp_sequential_thinking.server

set "RC=%ERRORLEVEL%"

:end
popd
endlocal & exit /b %RC%
