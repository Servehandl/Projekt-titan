from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

mcp = MCPServer("project-titan")


def _project_root() -> Path:
    configured_root = os.environ.get("TITAN_PROJECT_ROOT")
    if not configured_root:
        raise ValueError("Set TITAN_PROJECT_ROOT to the GIANTS project directory.")

    root = Path(configured_root).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("TITAN_PROJECT_ROOT must point to a directory.")

    return root


def _resolve_i3d_file(relative_path: str, root: Path) -> Path:
    requested_path = Path(relative_path)
    if requested_path.is_absolute():
        raise ValueError("Use a path relative to TITAN_PROJECT_ROOT.")

    file_path = (root / requested_path).resolve(strict=True)
    try:
        file_path.relative_to(root)
    except ValueError as error:
        raise ValueError("The requested file must stay inside TITAN_PROJECT_ROOT.") from error

    if not file_path.is_file():
        raise ValueError("The requested path is not a file.")
    if file_path.suffix.casefold() != ".i3d":
        raise ValueError("Only .i3d files can be inspected.")

    return file_path


@mcp.tool()
def list_i3d_files(limit: int = 100) -> dict[str, Any]:
    """List .i3d files under the configured project root without modifying them."""
    if limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500.")

    root = _project_root()
    matches: list[str] = []

    for candidate in root.rglob("*"):
        try:
            if candidate.suffix.casefold() != ".i3d":
                continue

            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
            if not resolved.is_file():
                continue

            matches.append(candidate.relative_to(root).as_posix())
            if len(matches) > limit:
                break
        except (OSError, ValueError):
            continue

    return {
        "project_root": str(root),
        "files": matches[:limit],
        "truncated": len(matches) > limit,
    }


@mcp.tool()
def inspect_i3d(relative_path: str, max_elements: int = 100) -> dict[str, Any]:
    """Read the XML summary of one .i3d file inside TITAN_PROJECT_ROOT."""
    if max_elements < 1 or max_elements > 500:
        raise ValueError("max_elements must be between 1 and 500.")

    root = _project_root()
    file_path = _resolve_i3d_file(relative_path, root)
    xml_root = ET.parse(file_path).getroot()
    scene = xml_root.find("Scene")

    elements: list[dict[str, str | None]] = []
    if scene is not None:
        for element in scene.iter():
            element_id = element.get("id")
            name = element.get("name")
            if element_id is None and name is None:
                continue
            elements.append(
                {
                    "tag": element.tag,
                    "name": name,
                    "id": element_id,
                }
            )

    return {
        "relative_path": file_path.relative_to(root).as_posix(),
        "i3d_version": xml_root.get("version"),
        "scene_present": scene is not None,
        "scene_element_count": len(elements),
        "elements": elements[:max_elements],
        "truncated": len(elements) > max_elements,
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
