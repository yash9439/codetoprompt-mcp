from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectContextRequest(BaseModel):
    root_path: Path = Field(..., description="Root directory path of the project.")
    include_patterns: Optional[List[str]] = Field(None, description="Comma-separated glob patterns for files to include.")
    exclude_patterns: Optional[List[str]] = Field(None, description="Comma-separated glob patterns for files to exclude.")
    respect_gitignore: bool = Field(True, description="Whether to respect .gitignore rules.")
    compress: bool = Field(False, description="Use smart code compression to summarize files.")
    output_format: str = Field("default", description="Output format ('default', 'markdown', 'cxml').", pattern="^(default|markdown|cxml)$")
    tree_depth: int = Field(5, description="Maximum depth for the project structure tree.")


class AnalyseProjectRequest(BaseModel):
    root_path: Path = Field(..., description="Root directory path of the project to analyse.")
    include_patterns: Optional[List[str]] = Field(None, description="Comma-separated glob patterns for files to include.")
    exclude_patterns: Optional[List[str]] = Field(None, description="Comma-separated glob patterns for files to exclude.")
    respect_gitignore: bool = Field(True, description="Whether to respect .gitignore rules.")
    top_n: int = Field(10, description="Number of items to show in top lists.")


class GetFilesRequest(BaseModel):
    root_path: Path = Field(..., description="Root directory path of the project.")
    paths: List[str] = Field(..., description="A list of specific file paths to include, relative to the root path.")
    output_format: str = Field("default", description="Output format ('default', 'markdown', 'cxml').", pattern="^(default|markdown|cxml)$")


TOOL_METADATA = {
    "ctp-get-context": {
        "model": ProjectContextRequest,
        "description": "Generates a comprehensive, context-rich prompt from an entire codebase directory, applying filters and formatting options.",
    },
    "ctp-analyse-project": {
        "model": AnalyseProjectRequest,
        "description": "Provides a detailed statistical analysis of a codebase, including token counts, line counts, and breakdowns by file type.",
    },
    "ctp-get-files": {
        "model": GetFilesRequest,
        "description": "Retrieves the content of a specific list of files from the project, formatted into a prompt.",
    },
}


def pydantic_to_json_schema(model: type[BaseModel]) -> Dict[str, Any]:
    schema = model.model_json_schema()
    if "$defs" in schema:
        del schema["$defs"]
    if "title" in schema:
        del schema["title"]
    # Pydantic v2 adds 'format: path', which is not standard JSON schema.
    if "properties" in schema:
        for prop_def in schema["properties"].values():
            if prop_def.get("format") == "path":
                prop_def["type"] = "string"
                del prop_def["format"]
    return schema


def get_tool_definitions() -> List[Dict[str, Any]]:
    tools = []
    for tool_name, metadata in TOOL_METADATA.items():
        model = metadata["model"]
        description = metadata["description"]
        schema = pydantic_to_json_schema(model)
        tools.append(
            {"name": tool_name, "description": description, "schema": schema}
        )
    return tools