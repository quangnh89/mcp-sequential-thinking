[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/arben-adm-mcp-sequential-thinking-badge.png)](https://mseep.ai/app/arben-adm-mcp-sequential-thinking)
[![Verified on MseeP](https://mseep.ai/badge.svg)](https://mseep.ai/app/0387db2d-476b-4b3d-852a-d55b4f67d888)

# Sequential Thinking MCP Server

[![MCP Toplist](https://mcptoplist.com/badge/glama%2Farben-adm%2Fmcp-sequential-thinking.svg)](https://mcptoplist.com/server/glama%2Farben-adm%2Fmcp-sequential-thinking)

A Model Context Protocol (MCP) server that facilitates structured, progressive thinking through defined stages. This tool helps break down complex problems into sequential thoughts, track the progression of your thinking process, and generate summaries.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<a href="https://glama.ai/mcp/servers/m83dfy8feg"><img width="380" height="200" src="https://glama.ai/mcp/servers/m83dfy8feg/badge" alt="Sequential Thinking Server MCP server" /></a>

## Features

- **Structured Thinking Framework**: Organizes thoughts through standard cognitive stages (Problem Definition, Research, Analysis, Synthesis, Conclusion)
- **Revisions & Branching**: Revise earlier thoughts or fork alternative lines of reasoning, with revision- and branch-aware analysis and summaries
- **Thought Tracking**: Records and manages sequential thoughts with metadata
- **Related Thought Analysis**: Identifies connections between similar thoughts
- **Progress Monitoring**: Tracks your position in the overall thinking sequence
- **Summary Generation**: Creates concise overviews of the entire thought process
- **Session Namespaces**: One store per analysis target, resolved per request, so several agents can share one server without their chains mixing
- **Persistent Storage**: Append-only JSONL session log with thread-safety and automatic crash recovery
- **Data Import/Export**: Share and reuse thinking sessions
- **Extensible Architecture**: Easily customize and extend functionality
- **Robust Error Handling**: Graceful handling of edge cases and corrupted data
- **Type Safety**: Comprehensive type annotations and validation

## Prerequisites

- Python 3.10 or higher
- UV package manager ([Install Guide](https://github.com/astral-sh/uv))

## Key Technologies

- **Pydantic**: For data validation and serialization
- **Portalocker**: For thread-safe file access
- **FastMCP**: For Model Context Protocol integration

## Project Structure

```
mcp-sequential-thinking/
├── mcp_sequential_thinking/
│   ├── server.py       # Main server implementation and MCP tools
│   ├── models.py       # Data models with Pydantic validation
│   ├── storage.py      # Thread-safe persistence layer
│   ├── storage_utils.py # Shared utilities for storage operations
│   ├── analysis.py     # Thought analysis and pattern detection
│   ├── utils.py        # Common utilities and helper functions
│   ├── logging_conf.py # Centralized logging configuration
│   └── __init__.py     # Package initialization
├── tests/              
│   ├── test_analysis.py # Tests for analysis functionality
│   ├── test_models.py   # Tests for data models
│   ├── test_storage.py  # Tests for persistence layer
│   └── __init__.py
├── run_server.py       # Server entry point script
├── debug_mcp_connection.py # Utility for debugging connections
├── README.md           # Main documentation
├── CHANGELOG.md        # Version history and changes
├── example.md          # Customization examples
├── LICENSE             # MIT License
└── pyproject.toml      # Project configuration and dependencies
```

## Quick Start

The package is published on PyPI as [`mcp-sequential-thinking`](https://pypi.org/project/mcp-sequential-thinking/). The easiest way to run it is via `uvx` — no install step needed:

```bash
uvx mcp-sequential-thinking
```

Or install it permanently:

```bash
pip install mcp-sequential-thinking
mcp-sequential-thinking
```

### Development Setup

To work on the code, clone the repository and set it up from source:

1. **Set Up Project**
   ```bash
   # Create and activate virtual environment
   uv venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Unix

   # Install package and dependencies
   uv pip install -e .

   # For development with testing tools
   uv pip install -e ".[dev]"

   # For all optional dependencies
   uv pip install -e ".[all]"
   ```

2. **Run the Server**
   ```bash
   # Run directly
   uv run -m mcp_sequential_thinking.server

   # Or use the installed script
   mcp-sequential-thinking
   ```

3. **Run Tests**
   ```bash
   # Run all tests
   pytest

   # Run with coverage report
   pytest --cov=mcp_sequential_thinking
   ```

## Claude Desktop Integration

Add to your Claude Desktop configuration:
- **Linux**: `~/.config/Claude/claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Option 1: Using uvx with the PyPI package (recommended)

No clone, no venv, no manual updates — uvx fetches the package from PyPI and runs it:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uvx",
      "args": ["mcp-sequential-thinking"]
    }
  }
}
```

To test unreleased changes, point uvx at the repository instead:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/arben-adm/mcp-sequential-thinking",
        "mcp-sequential-thinking"
      ]
    }
  }
}
```

### Option 2: Using the installed entry point

If you've installed the package with `pip install mcp-sequential-thinking` (or `pip install -e .` from a clone):

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "mcp-sequential-thinking"
    }
  }
}
```

### Option 3: Using a local clone's virtual environment (development)

If you have set up the project with `uv venv && uv pip install -e .`, point directly to the venv Python interpreter. This avoids dependency resolution issues (e.g., on systems with Python 3.14+):

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "/path/to/mcp-sequential-thinking/.venv/bin/python",
      "args": [
        "-m",
        "mcp_sequential_thinking.server"
      ],
      "cwd": "/path/to/mcp-sequential-thinking"
    }
  }
}
```

### Option 4: Using uv run on a local clone (development)

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/mcp-sequential-thinking",
        "-m",
        "mcp_sequential_thinking.server"
      ]
    }
  }
}
```

## Editor & IDE Integration

### Cursor

Add to your Cursor MCP configuration at `.cursor/mcp.json` in your project root (or globally at `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uvx",
      "args": ["mcp-sequential-thinking"]
    }
  }
}
```

### VS Code (Copilot MCP)

VS Code supports MCP servers since version 1.99+. Add to `.vscode/mcp.json` in your workspace or to your user `settings.json`:

```json
{
  "servers": {
    "sequential-thinking": {
      "command": "uvx",
      "args": ["mcp-sequential-thinking"]
    }
  }
}
```

> **Note:** Enable MCP support in VS Code via `"chat.mcp.enabled": true` in your settings.

### Zed

Add to your Zed settings (`~/.config/zed/settings.json`):

```json
{
  "context_servers": {
    "sequential-thinking": {
      "command": {
        "path": "uvx",
        "args": ["mcp-sequential-thinking"]
      }
    }
  }
}
```

### Claude Code (CLI)

Add the server using the CLI:

```bash
claude mcp add sequential-thinking -- uvx mcp-sequential-thinking
```

Or manually create/edit `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uvx",
      "args": ["mcp-sequential-thinking"]
    }
  }
}
```

### Windsurf

Add to your Windsurf MCP configuration at `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uvx",
      "args": ["mcp-sequential-thinking"]
    }
  }
}
```

### Gemini CLI

Add to your Gemini CLI settings at `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-sequential-thinking"],
      "env": {}
    }
  }
}
```

> **Tip:** All editor configurations above run the published PyPI package via `uvx`. To run from a local clone instead (e.g. for development), use `uv run --directory /path/to/mcp-sequential-thinking -m mcp_sequential_thinking.server` or point directly to the venv Python interpreter (see [Claude Desktop Options 3 and 4](#option-3-using-a-local-clones-virtual-environment-development)).

# How It Works

The server maintains a history of thoughts and processes them through a structured workflow. Each thought is validated using Pydantic models, categorized into thinking stages, and stored with relevant metadata in a thread-safe storage system. The server automatically handles data persistence, backup creation, and provides tools for analyzing relationships between thoughts.

Sessions are persisted as an append-only JSONL log at `~/.mcp_sequential_thinking/spaces/<session>/current_session.jsonl` (override the root with the `MCP_STORAGE_DIR` environment variable; see [Sessions: one store per target](#sessions-one-store-per-target)). Each `process_thought` call appends a single fsynced line, so the file doubles as an audit trail and a truncated final line from an interrupted write is recovered automatically. Sessions from v0.5.x (`current_session.json`) are migrated losslessly on first start; the original file is kept as `current_session.json.migrated-to-v2`.

## Usage Guide

The Sequential Thinking server exposes six main tools:

### 1. `process_thought`

Records and analyzes a new thought in your sequential thinking process.

**Parameters:**

- `thought` (string): The content of your thought
- `thought_number` (integer): Position in your sequence (e.g., 1 for first thought)
- `total_thoughts` (integer): Expected total thoughts in the sequence
- `next_thought_needed` (boolean): Whether more thoughts are needed after this one
- `stage` (string): The thinking stage - must be one of:
  - "Problem Definition"
  - "Research"
  - "Analysis"
  - "Synthesis"
  - "Conclusion"
- `tags` (list of strings, optional): Keywords or categories for your thought
- `axioms_used` (list of strings, optional): Principles or axioms applied in your thought
- `assumptions_challenged` (list of strings, optional): Assumptions your thought questions or challenges
- `is_revision` (boolean, optional): Whether this thought revises an earlier one
- `revises_thought_number` (integer, optional): The number of the earlier thought being revised (required together with `is_revision`)
- `branch_from_thought` (integer, optional): The thought number to fork from when exploring an alternative path
- `branch_id` (string, optional): Identifier for the branch (letters, digits, `-`, `_`; max 64 characters; requires `branch_from_thought`)

**Example:**

```python
# First thought in a 5-thought sequence
process_thought(
    thought="The problem of climate change requires analysis of multiple factors including emissions, policy, and technology adoption.",
    thought_number=1,
    total_thoughts=5,
    next_thought_needed=True,
    stage="Problem Definition",
    tags=["climate", "global policy", "systems thinking"],
    axioms_used=["Complex problems require multifaceted solutions"],
    assumptions_challenged=["Technology alone can solve climate change"]
)

# Revise an earlier thought
process_thought(
    thought="Framing the problem purely around emissions was too narrow; adaptation matters equally.",
    thought_number=6,
    total_thoughts=6,
    next_thought_needed=True,
    stage="Problem Definition",
    is_revision=True,
    revises_thought_number=1
)

# Fork an alternative line of reasoning
process_thought(
    thought="What if we approach this from a market-incentive angle instead?",
    thought_number=7,
    total_thoughts=7,
    next_thought_needed=True,
    stage="Analysis",
    branch_from_thought=3,
    branch_id="market-incentives"
)
```

### 2. `generate_summary`

Generates a summary of your entire thinking process.

**Example output:**

```json
{
  "summary": {
    "totalThoughts": 5,
    "stages": {
      "Problem Definition": 1,
      "Research": 1,
      "Analysis": 1,
      "Synthesis": 1,
      "Conclusion": 1
    },
    "timeline": [
      {"number": 1, "stage": "Problem Definition"},
      {"number": 2, "stage": "Research"},
      {"number": 3, "stage": "Analysis"},
      {"number": 4, "stage": "Synthesis"},
      {"number": 5, "stage": "Conclusion"},
      {"number": 6, "stage": "Problem Definition", "isRevision": true},
      {"number": 7, "stage": "Analysis", "branchId": "market-incentives"}
    ],
    "branches": {
      "market-incentives": {"fromThought": 3, "thoughtCount": 1}
    },
    "revisionCount": 1
  }
}
```

### 3. `clear_history`

Resets one session by clearing its recorded thoughts. Scoped to a session, but every agent
working on that session shares the history it wipes.

### 4. `export_session`

Exports the current thinking session to a JSON file for sharing or backup.

**Parameters:**

- `file_path` (string): Path to the output JSON file. Since v0.6.0, exports are confined to the `exports/` subdirectory of the storage directory; relative paths resolve to `~/.mcp_sequential_thinking/exports/` and parent directories are created automatically.

**Example:**

```python
export_session(file_path="my-analysis.json")
# -> written to ~/.mcp_sequential_thinking/exports/my-analysis.json
```

### 5. `import_session`

Imports a previously exported thinking session from a JSON file. Exports created with v0.5.x remain importable.

**Parameters:**

- `file_path` (string): Path to the JSON file to import. Like exports, resolved inside the `exports/` subdirectory of the storage directory.

### 6. `list_sessions`

Lists the thinking sessions this server holds, with a thought count and last-updated time for
each. Use it to check that a chain landed where you meant it to: a misspelled session name
opens a new, empty store rather than failing.

## Sessions: one store per target

Every tool above takes an optional `session` argument, and each session is a separate store
under `<MCP_STORAGE_DIR>/spaces/<session>/`. This matters as soon as more than one agent
talks to the same server: without it, one agent's thoughts land in another's summary,
`revisionOf` echo and related-thought lookups, and `clear_history` / `import_session` wipe
everybody's work at once.

Which session a call uses is resolved per request, first match wins:

1. the `session` argument on the call - e.g. `session="storport"`;
2. the `X-Thinking-Session` HTTP header;
3. `?session=<name>` on the server URL (`http://host:port/mcp?session=storport`);
4. the `MCP_DEFAULT_SESSION` environment variable (mainly for stdio deployments);
5. otherwise the call is refused - unless `SESSION_REQUIRED=0`, which falls back to `default`.

(2) and (3) let an MCP client fix the session once in its config, so every agent deployed
against that config shares one chain per target; the argument in (1) overrides it when a
single run legitimately spans two targets, such as diffing two versions of one binary.

A store written by a pre-0.7.0 release, which lived directly in the storage root, is migrated
once into `spaces/default/` on first start; the original is kept as
`current_session.jsonl.migrated-to-spaces`.

## Skill: teaching an agent to use this server well

`skills/sequential-thinking/` is an agent **skill** that ships with this repository. It is
documentation, not code: it tells an agent when a thought chain is worth opening at all, what each
stage is for, the cross-field rules this server enforces, and — the part agents get wrong most
often — that one `session` is one unit of work and that several agents share the store inside it.
It does not replace or wrap the server; the server works without it.

The skill is deliberately domain-neutral: its worked examples are a web/database latency
regression, an equity price-and-volume analysis, and a novel's continuity chain. Nothing in it
assumes what you are using the server for.

```
skills/sequential-thinking/
├── SKILL.md                    when to open a chain, tools, parameters, session semantics
└── references/
    ├── patterns.md             revision, branch-and-converge, scope, concurrency, export/import
    └── examples.md             three complete chains, one per pattern
```

The skill is part of the repository checkout only — it is not in the PyPI wheel, so install it from
a clone or a submodule of this repo.

### Installing it

```bash
# into a project, for Claude Code               -> <project>/.claude/skills/sequential-thinking/
python install_skill.py --target ../my-project

# into your user-level Claude skills            -> ~/.claude/skills/sequential-thinking/
python install_skill.py --runner claude-user

# into a project, for OpenCode                  -> <project>/.opencode/skills/sequential-thinking/
python install_skill.py --target ../my-project --runner opencode
```

| Option | Meaning |
|---|---|
| `--target DIR` | Root directory of the destination project. Required unless you pass `--dest`, and ignored for `--runner claude-user`. |
| `--runner {claude,claude-user,opencode,raw}` | Selects **both** the destination path **and** the tool-name dialect. `claude` → `<target>/.claude/skills/sequential-thinking/`, tools prefixed `mcp__<server>__`. `claude-user` → `~/.claude/skills/sequential-thinking/`, same prefix. `opencode` → `<target>/.opencode/skills/sequential-thinking/`, prefix `<server>_`. `raw` → copied with bare tool names, for a host that exposes them unprefixed. Default: `claude`. |
| `--server-name NAME` | The name you registered this MCP server under in your host's config; the prefix is built from it. Default: `sequential-thinking`. Change it if your config calls the server something else, or the skill will name tools your host does not have. |
| `--dest DIR` | Write to this exact directory, ignoring the `--runner` path rule. The dialect still follows `--runner`. |
| `--force` | Overwrite an existing destination. Without it the install refuses and prints the path in the way. |
| `--dry-run` | Print the destination, the prefix and the files that would be written, then stop. |

Re-running is safe: the installed copy is byte-identical to the previous one, and a name that
already carries a prefix is never prefixed twice.

### Installing it by hand

The files in `skills/` use the **bare** tool names this server registers. Most hosts expose MCP
tools under a prefix, so after copying the directory, rewrite the six names. This is the whole
conversion — there is nothing else host-specific in the skill:

| In `skills/` | Claude Code | OpenCode |
|---|---|---|
| `process_thought` | `mcp__sequential-thinking__process_thought` | `sequential-thinking_process_thought` |
| `generate_summary` | `mcp__sequential-thinking__generate_summary` | `sequential-thinking_generate_summary` |
| `clear_history` | `mcp__sequential-thinking__clear_history` | `sequential-thinking_clear_history` |
| `export_session` | `mcp__sequential-thinking__export_session` | `sequential-thinking_export_session` |
| `import_session` | `mcp__sequential-thinking__import_session` | `sequential-thinking_import_session` |
| `list_sessions` | `mcp__sequential-thinking__list_sessions` | `sequential-thinking_list_sessions` |

Replace `sequential-thinking` in the prefix with whatever name your config registers the server
under. The same rewrite, run over the copied directory:

```bash
# bash / sed, inside the copied skill directory (Claude Code dialect)
sed -i -E 's/(^|[^_A-Za-z-])(process_thought|generate_summary|clear_history|export_session|import_session|list_sessions)/\1mcp__sequential-thinking__\2/g' SKILL.md references/*.md
```

```powershell
# PowerShell, inside the copied skill directory (Claude Code dialect)
Get-ChildItem -Recurse -Filter *.md | ForEach-Object {
  (Get-Content $_.FullName -Raw) -replace '(?<![\w-])(process_thought|generate_summary|clear_history|export_session|import_session|list_sessions)\b', 'mcp__sequential-thinking__$1' |
    Set-Content $_.FullName -Encoding utf8
}
```

Whichever way you install it, wiring the server itself into the host's MCP config is a separate
step — see the integration sections above.

## Comparison to the official sequential-thinking server

The [official MCP sequential-thinking server](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) provides the core paradigm: numbered thoughts with revisions and branching, held in memory for the duration of the process. This server implements the same paradigm and adds:

- **Persistence**: sessions survive restarts (append-only JSONL log with crash recovery and automatic migration), and can be exported, shared and re-imported as JSON.
- **Thinking stages**: thoughts are categorized into cognitive stages (Problem Definition, Research, Analysis, Synthesis, Conclusion), enabling stage-based filtering and completeness checks.
- **Analysis**: related-thought detection via stages and tags, per-thought progress, and rich summaries including branch and revision statistics.

If you only need ephemeral chain-of-thought scaffolding, the official server is a lighter choice; if you want durable, analyzable thinking sessions, this one is built for that.

## Practical Applications

- **Decision Making**: Work through important decisions methodically
- **Problem Solving**: Break complex problems into manageable components
- **Research Planning**: Structure your research approach with clear stages
- **Writing Organization**: Develop ideas progressively before writing
- **Project Analysis**: Evaluate projects through defined analytical stages


## Getting Started

With the proper MCP setup, simply use the `process_thought` tool to begin working through your thoughts in sequence. As you progress, you can get an overview with `generate_summary` and reset when needed with `clear_history`.



# Customizing the Sequential Thinking Server

For detailed examples of how to customize and extend the Sequential Thinking server, see [example.md](example.md). It includes code samples for:

- Modifying thinking stages
- Enhancing thought data structures with Pydantic
- Adding persistence with databases
- Implementing enhanced analysis with NLP
- Creating custom prompts
- Setting up advanced configurations
- Building web UI integrations
- Implementing visualization tools
- Connecting to external services
- Creating collaborative environments
- Separating test code
- Building reusable utilities




## License

MIT License



