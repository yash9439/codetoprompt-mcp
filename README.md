# CodeToPrompt MCP Server

[![PyPI version](https://badge.fury.io/py/codetoprompt-mcp.svg)](https://badge.fury.io/py/codetoprompt-mcp)

**CodeToPrompt MCP Server** exposes the powerful features of the [codetoprompt](https://github.com/yash9439/codetoprompt) library through the Model Context Protocol (MCP). This allows LLM agents and other MCP-compatible clients to programmatically generate prompts, analyze codebases, and retrieve specific file contents.

---

## 🔧 Installation

Install from PyPI:

```bash
pip install codetoprompt-mcp
```

This will automatically install `codetoprompt` and the required `mcp` library.

---

## 🚀 Usage with an MCP Client

This server is designed to be used with an MCP client, such as the Claude Desktop App.

### Example: Claude Desktop Configuration

To use this server with Claude, add it to your `claude_desktop_config.json` file:

```jsonc
{
  "mcpServers": {
    "CodeToPrompt": {
      "command": "ctp-mcp"
    }
  }
}
```

Once configured, you can invoke the tools from your conversation with the LLM.

### Available Tools

*   **`ctp-get-context`**: The primary tool for generating a comprehensive prompt from a directory. It supports all of `codetoprompt`'s filtering, formatting, and compression options.
*   **`ctp-analyse-project`**: Provides a detailed statistical analysis of a codebase, including token counts, line counts, and breakdowns by file type.
*   **`ctp-get-files`**: Retrieves the content of specific files, formatted as a prompt. This is useful for targeted queries.

---

## 🤝 Contributing

We welcome contributions! Please refer to the main [codetoprompt repository](https://github.com/yash9439/codetoprompt) for contribution guidelines.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for full details.
