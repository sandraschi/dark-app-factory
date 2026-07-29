# dark-app-factory (MCPB Bundle)

Software Factory scaffold for local AI models

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "dark-app-factory": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "dark_app_factory"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **dark-app-factory**: Software Factory scaffold for local AI models

## Requirements

- Python 3.12+
- uv
