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
    """Read the scene nodes and file references from one .i3d file."""
    if max_elements < 1 or max_elements > 500:
        raise ValueError("max_elements must be between 1 and 500.")

    root = _project_root()
    file_path = _resolve_i3d_file(relative_path, root)
    xml_root = ET.parse(file_path).getroot()
    scene = xml_root.find("Scene")
    files_section = xml_root.find("Files")

    nodes: list[dict[str, str | None]] = []

    def collect_nodes(parent: ET.Element, parent_node_id: str | None = None) -> None:
        for element in parent:
            node_id = element.get("nodeId")
            if node_id is not None:
                nodes.append(
                    {
                        "tag": element.tag,
                        "name": element.get("name"),
                        "node_id": node_id,
                        "parent_node_id": parent_node_id,
                        "shape_id": element.get("shapeId"),
                        "material_ids": element.get("materialIds"),
                    }
                )
            collect_nodes(
                element,
                node_id if node_id is not None else parent_node_id,
            )

    if scene is not None:
        collect_nodes(scene)

    file_references: list[dict[str, str | None]] = []
    if files_section is not None:
        for entry in files_section.findall("File"):
            file_references.append(
                {
                    "file_id": entry.get("fileId"),
                    "filename": entry.get("filename"),
                    "relative_path": entry.get("relativePath"),
                }
            )

    return {
        "relative_path": file_path.relative_to(root).as_posix(),
        "i3d_name": xml_root.get("name"),
        "i3d_version": xml_root.get("version"),
        "sections": [element.tag for element in xml_root],
        "scene_present": scene is not None,
        "scene_node_count": len(nodes),
        "nodes": nodes[:max_elements],
        "nodes_truncated": len(nodes) > max_elements,
        "file_reference_count": len(file_references),
        "file_references": file_references[:max_elements],
        "file_references_truncated": len(file_references) > max_elements,
    }


@mcp.tool()
def search_i3d_nodes(query: str, max_results: int = 100) -> dict[str, Any]:
    """Search node names and IDs across I3D scene graphs without modifying files."""
    search_term = query.strip()
    if not search_term:
        raise ValueError("query must not be empty.")
    if max_results < 1 or max_results > 500:
        raise ValueError("max_results must be between 1 and 500.")

    root = _project_root()
    normalized_query = search_term.casefold()
    results: list[dict[str, str | None]] = []
    match_count = 0
    scanned_file_count = 0
    parse_error_count = 0

    for candidate in root.rglob("*"):
        try:
            if candidate.suffix.casefold() != ".i3d":
                continue

            file_path = candidate.resolve(strict=True)
            file_path.relative_to(root)
            if not file_path.is_file():
                continue

            scanned_file_count += 1
            xml_root = ET.parse(file_path).getroot()
            scene = xml_root.find("Scene")
            if scene is None:
                continue

            stack: list[tuple[ET.Element, str | None]] = [(scene, None)]
            while stack:
                parent, parent_node_id = stack.pop()
                for element in reversed(list(parent)):
                    node_id = element.get("nodeId")
                    name = element.get("name")
                    searchable_values = (name or "", node_id or "")
                    if node_id is not None and any(
                        normalized_query in value.casefold()
                        for value in searchable_values
                    ):
                        match_count += 1
                        if len(results) < max_results:
                            results.append(
                                {
                                    "relative_path": file_path.relative_to(root).as_posix(),
                                    "tag": element.tag,
                                    "name": name,
                                    "node_id": node_id,
                                    "parent_node_id": parent_node_id,
                                }
                            )
                    stack.append(
                        (
                            element,
                            node_id if node_id is not None else parent_node_id,
                        )
                    )
        except ET.ParseError:
            parse_error_count += 1
        except (OSError, ValueError):
            continue

    return {
        "query": search_term,
        "project_root": str(root),
        "scanned_i3d_file_count": scanned_file_count,
        "match_count": match_count,
        "results": results,
        "results_truncated": match_count > len(results),
        "parse_error_count": parse_error_count,
    }


@mcp.tool()
def check_i3d_integrity(relative_path: str, max_issues: int = 100) -> dict[str, Any]:
    """Check common I3D ID references without changing the file or checking the full GDN schema."""
    if max_issues < 1 or max_issues > 500:
        raise ValueError("max_issues must be between 1 and 500.")

    root = _project_root()
    file_path = _resolve_i3d_file(relative_path, root)
    xml_root = ET.parse(file_path).getroot()
    scene = xml_root.find("Scene")
    files_section = xml_root.find("Files")
    shapes_section = xml_root.find("Shapes")
    materials_section = xml_root.find("Materials")

    issues: list[dict[str, str]] = []
    issue_count = 0

    def add_issue(code: str, message: str, value: str = "") -> None:
        nonlocal issue_count
        issue_count += 1
        if len(issues) < max_issues:
            issue = {"code": code, "message": message}
            if value:
                issue["value"] = value
            issues.append(issue)

    if scene is None:
        add_issue("missing_scene", "The I3D file has no Scene section.")

    node_ids: set[str] = set()
    if scene is not None:
        for element in scene.iter():
            node_id = element.get("nodeId")
            if node_id is None:
                continue
            if node_id in node_ids:
                add_issue("duplicate_node_id", "A nodeId is used more than once.", node_id)
            node_ids.add(node_id)

    file_ids: set[str] = set()
    if files_section is not None:
        for entry in files_section.findall("File"):
            file_id = entry.get("fileId")
            filename = entry.get("filename")
            if file_id is None:
                add_issue("missing_file_id", "A File entry has no fileId.")
            elif file_id in file_ids:
                add_issue("duplicate_file_id", "A fileId is defined more than once.", file_id)
            else:
                file_ids.add(file_id)
            if not filename:
                add_issue("missing_filename", "A File entry has no filename.", file_id or "")

    for element in xml_root.iter():
        file_id = element.get("fileId")
        if file_id is not None and file_id not in file_ids:
            add_issue("unresolved_file_id", "A fileId reference has no matching Files entry.", file_id)

    shape_ids = (
        {
            element.get("shapeId")
            for element in shapes_section.iter()
            if element.get("shapeId") is not None
        }
        if shapes_section is not None
        else set()
    )
    material_ids = (
        {
            element.get("materialId")
            for element in materials_section.iter()
            if element.get("materialId") is not None
        }
        if materials_section is not None
        else set()
    )

    if scene is not None:
        for element in scene.iter():
            if element.tag != "Shape":
                continue

            shape_id = element.get("shapeId")
            if shape_id is not None and shape_id not in shape_ids:
                add_issue("unresolved_shape_id", "A scene Shape has no matching Shapes entry.", shape_id)

            for material_id in (element.get("materialIds") or "").split():
                if material_id not in material_ids:
                    add_issue(
                        "unresolved_material_id",
                        "A scene Shape references a missing materialId.",
                        material_id,
                    )

    return {
        "relative_path": file_path.relative_to(root).as_posix(),
        "valid": issue_count == 0,
        "issue_count": issue_count,
        "issues": issues,
        "issues_truncated": issue_count > len(issues),
        "checks": [
            "scene presence",
            "unique scene nodeId values",
            "Files fileId definitions and references",
            "scene Shape shapeId references",
            "scene Shape materialIds references",
        ],
        "note": "This is a limited integrity check, not full I3D schema validation.",
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
