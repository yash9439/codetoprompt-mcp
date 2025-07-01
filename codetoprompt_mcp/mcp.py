import asyncio
from importlib.metadata import version
from pathlib import Path
from typing import Any, Dict

from codetoprompt.core import CodeToPrompt
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, ErrorData, TextContent, Tool
from pydantic import ValidationError

from .mcp_tools import (
    AnalyseProjectRequest,
    GetFilesRequest,
    ProjectContextRequest,
    get_tool_definitions,
)

TOOL_DEFINITIONS = get_tool_definitions()
TOOLS = [
    Tool(name=tool["name"], description=tool["description"], inputSchema=tool["schema"])
    for tool in TOOL_DEFINITIONS
]

def format_analysis_report(data: Dict[str, Any], top_n: int) -> str:
    """Formats the dictionary from `CodeToPrompt.analyse()` into a readable string."""
    report = []
    
    overall = data.get("overall", {})
    report.append("--- Overall Project Summary ---")
    report.append(f"Total Files:  {overall.get('file_count', 0):,}")
    report.append(f"Total Lines:  {overall.get('total_lines', 0):,}")
    report.append(f"Total Tokens: {overall.get('total_tokens', 0):,}")
    report.append("")
    
    by_extension = data.get("by_extension", [])
    if by_extension:
        report.append(f"--- Analysis by File Type (Top {len(by_extension)}) ---")
        report.append(f"{'Extension':<12} | {'Files':>6} | {'Tokens':>10} | {'Lines':>8} | {'Avg Tokens/File':>15}")
        report.append(f"{'-'*12}-+-{'-'*6}-+-{'-'*10}-+-{'-'*8}-+-{'-'*15}")
        for row in by_extension:
            avg = row['tokens'] / row['file_count'] if row.get('file_count', 0) > 0 else 0
            report.append(f"{row.get('extension', ''):<12} | {row.get('file_count', 0):>6,} | {row.get('tokens', 0):>10,} | {row.get('lines', 0):>8,} | {avg:>15,.0f}")
        report.append("")

    top_files = data.get("top_files_by_tokens", [])
    if top_files:
        report.append(f"--- Largest Files by Tokens (Top {len(top_files)}) ---")
        report.append(f"{'File Path':<40} | {'Tokens':>10} | {'Lines':>8}")
        report.append(f"{'-'*40}-+-{'-'*10}-+-{'-'*8}")
        for row in top_files:
            path_str = str(row.get('path', ''))
            if len(path_str) > 38:
                path_str = "..." + path_str[-35:]
            report.append(f"{path_str:<40} | {row.get('tokens', 0):>10,} | {row.get('lines', 0):>8,}")
    
    return "\n".join(report)

async def get_context(arguments: dict) -> list[TextContent]:
    request = ProjectContextRequest(**arguments)
    ctp = CodeToPrompt(
        root_dir=str(request.root_path),
        include_patterns=request.include_patterns,
        exclude_patterns=request.exclude_patterns,
        respect_gitignore=request.respect_gitignore,
        compress=request.compress,
        output_format=request.output_format,
        tree_depth=request.tree_depth,
    )
    prompt = ctp.generate_prompt()
    return [TextContent(type="text", text=prompt)]

async def analyse_project(arguments: dict) -> list[TextContent]:
    request = AnalyseProjectRequest(**arguments)
    ctp = CodeToPrompt(
        root_dir=str(request.root_path),
        include_patterns=request.include_patterns,
        exclude_patterns=request.exclude_patterns,
        respect_gitignore=request.respect_gitignore,
    )
    analysis_data = ctp.analyse(top_n=request.top_n)
    report = format_analysis_report(analysis_data, top_n=request.top_n)
    return [TextContent(type="text", text=report)]

async def get_files(arguments: dict) -> list[TextContent]:
    request = GetFilesRequest(**arguments)
    # Convert string paths to Path objects for the `explicit_files` argument
    explicit_files = [Path(request.root_path) / p for p in request.paths]
    ctp = CodeToPrompt(
        root_dir=str(request.root_path),
        output_format=request.output_format,
        explicit_files=explicit_files,
    )
    prompt = ctp.generate_prompt()
    return [TextContent(type="text", text=prompt)]

async def serve() -> None:
    server = Server("codetoprompt-mcp", version("codetoprompt-mcp"))

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        return TOOLS

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        handlers = {
            "ctp-get-context": get_context,
            "ctp-analyse-project": analyse_project,
            "ctp-get-files": get_files,
        }
        try:
            return await handlers[name](arguments)
        except KeyError:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=f"Unknown tool: {name}"))
        except (ValidationError, TypeError) as e:
            raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
        except Exception as e:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options(), raise_exceptions=True
        )

def run_server():
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        print("Server interrupted and shut down.")