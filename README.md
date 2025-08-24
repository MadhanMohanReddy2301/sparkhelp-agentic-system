# Agentic AI Base Code Framework

A comprehensive, modular framework for building intelligent agent-based systems with plugin architecture, designed for extensibility and scalability.

## 🚀 Overview

This framework provides a robust foundation for creating AI agents that can perform complex tasks through modular plugins. It features a calculator agent as a reference implementation, demonstrating the plugin architecture and agent orchestration capabilities.

## 🏗️ Architecture

The framework is built on a modular architecture with the following key components:

### Core Components

- **Agent Verse**: Central orchestration system for managing AI agents
- **Plugin System**: Extensible architecture for adding new capabilities
- **AI Model Factory**: Unified interface for different LLM providers
- **Configuration Management**: Centralized configuration for credentials and settings
- **Utilities**: Logging, metrics, and shared functionality

### Directory Structure

```
AgenticAI-Base-Code/
├── agent_verse/              # Core agent orchestration
│   ├── calculator_agent/     # Reference agent implementation
│   │   ├── agent.py         # Main agent logic
│   │   ├── prompt/          # Agent prompts and templates
│   │   └── logs/            # Agent execution logs
│   └── __init__.py
├── agent_plugins_verse/      # Plugin system
│   └── agent_plugin_calculator/  # Calculator plugin
│       ├── server.py        # Plugin server implementation
│       └── requirements.txt
├── ai_model/                # AI model management
│   ├── agent_llm_factory.py # LLM provider factory
│   └── __init__.py
├── config/                  # Configuration management
│   ├── credential_manager.py
│   ├── llm_config.json     # LLM configuration
│   └── plugin_config.json  # Plugin configuration
├── utils/                   # Shared utilities
│   ├── logger.py           # Logging utilities
│   ├── metrics.py          # Metrics collection
│   └── __init__.py
├── process_specific_agent.py # Main application entry point
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project configuration
└── example.env            # Environment variables template
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- pip (Python package installer)
- venv (for virtual environments)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd AgenticAI-Base-Code
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Set up environment variables**
   ```bash
   cp example.env .env
   # Edit .env with your API keys and configuration
   ```

5. **Configure LLM settings**
   - Edit `config/llm_config.json` with your preferred LLM provider settings
   - Update `config/plugin_config.json` for plugin configurations

## 🎯 Usage

### Running Single Agents

To run any individual agent, navigate to the specific agent directory and execute its agent.py file:

```bash
python agent_verse/[agent_name]/agent.py
```

For example:
```bash
python agent_verse/my_custom_agent/agent.py
```

### Pre-Execution Checklist

Before running any agent:

1. **Configure Environment Variables**: Rename `example.env` to `.env` and add your configuration:
   ```bash
   cp example.env .env
   # Edit .env with your API keys and configuration
   ```

2. **Check for MCP Servers**: If your agent uses MCP (Model Context Protocol) servers, ensure they are running first:
   ```bash
   # Start any required MCP servers
   python path/to/mcp_server.py
   ```

3. **Run the Agent**: Execute the agent after confirming MCP servers are active:
   ```bash
   python agent_verse/[your_agent]/agent.py
   ```

### Running Multi-Agent Systems

For orchestrating multiple agents together, use the main multi-agent orchestrator:

```bash
python orchestration.py
```

This file coordinates multiple agents and handles complex workflows involving agent interactions.

<edit_file>
<path>README.md</path>
<content>
<<<<<<< SEARCH
### Running the Calculator Agent
=======
### Running the Calculator Agent and Single Agent


## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `example.env`:

```bash
# LLM Provider Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Application Settings
LOG_LEVEL=INFO
METRICS_ENABLED=true
```

### LLM Configuration

Edit `config/llm_config.json`:

```json
{
  "default_provider": "openai",
  "providers": {
    "openai": {
      "model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 1000
    },
    "anthropic": {
      "model": "claude-3-sonnet",
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }
}
```

### Plugin Configuration

Edit `config/plugin_config.json`:

```json
{
  "plugins": {
    "calculator": {
      "enabled": true,
      "endpoint": "http://localhost:8000"
    }
  }
}
```

## 🔌 Creating Custom Plugins

### Plugin Structure

```python
# agent_plugins_verse/your_plugin/__init__.py
from .server import YourPluginServer

__all__ = ['YourPluginServer']
```

### Plugin Server Template

```python
# agent_plugins_verse/your_plugin/server.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.post("/process")
async def process_request(request: dict):
    # Your plugin logic here
    return {"result": "processed"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

## 📊 Monitoring & Debugging

### Logs
- Agent logs: `agent_verse/calculator_agent/logs/`
- Log level can be adjusted via environment variable `LOG_LEVEL`

### Metrics
- Metrics collection is enabled by default
- Check `utils/metrics.py` for available metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints for all functions
- Include comprehensive docstrings
- Write unit tests for new features
- Update documentation for API changes

## 🐛 Troubleshooting

### Common Issues

**Import Errors**
```bash
pip install -e .  # Ensure package is installed in editable mode
```

**Permission Issues**
```bash
chmod +x orchestration.py
```

**Missing Dependencies**
```bash
pip install -r requirements.txt
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review logs in `agent_verse/*/logs/` directories
