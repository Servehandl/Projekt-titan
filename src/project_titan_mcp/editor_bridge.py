from __future__ import annotations

import math
import os
import threading
import time
import uuid
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

_BRIDGE_LOCK = threading.Lock()
_REQUEST_TIMEOUT_SECONDS = 5.0
_POLL_INTERVAL_SECONDS = 0.05
_MAX_RESPONSE_BYTES = 1_000_000
_MAX_SELECTION = 200
_MAX_TRANSFORM_COMPONENT = 1_000_000.0
_INTERPROCESS_LOCK_TIMEOUT_SECONDS = 10.0
_STALE_LOCK_AGE_SECONDS = 60.0


def _bridge_directory() -> Path:
    configured = os.environ.get("TITAN_EDITOR_BRIDGE_DIR")
    if not configured:
        raise ValueError(
            "Set TITAN_EDITOR_BRIDGE_DIR to the GIANTS Editor bridge folder."
        )

    try:
        directory = Path(configured).expanduser().resolve(strict=True)
    except OSError as error:
        raise ValueError(
            "TITAN_EDITOR_BRIDGE_DIR must point to the existing GIANTS Editor bridge folder."
        ) from error

    if not directory.is_dir():
        raise ValueError("TITAN_EDITOR_BRIDGE_DIR must point to a directory.")
    return directory


@contextmanager
def _bridge_lock(directory: Path) -> Iterator[None]:
    lock_directory = directory / ".mcp-lock"
    deadline = time.monotonic() + _INTERPROCESS_LOCK_TIMEOUT_SECONDS

    with _BRIDGE_LOCK:
        while True:
            try:
                lock_directory.mkdir()
                break
            except FileExistsError:
                try:
                    lock_age = time.time() - lock_directory.stat().st_mtime
                    if lock_age > _STALE_LOCK_AGE_SECONDS:
                        lock_directory.rmdir()
                        continue
                except OSError:
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "Another PROJECT TITAN MCP process is using the GIANTS Editor bridge."
                    )
                time.sleep(_POLL_INTERVAL_SECONDS)

        try:
            yield
        finally:
            try:
                lock_directory.rmdir()
            except OSError:
                pass


def _write_request(
    directory: Path,
    operation: str,
    session_id: str | None = None,
    expected_runtime_ids: list[int] | None = None,
    expected_scene_filename: str | None = None,
    node_name_path: list[str] | None = None,
    translation: list[float] | None = None,
    rotation: list[float] | None = None,
    scale: list[float] | None = None,
) -> tuple[str, dict[str, Any]]:
    request_id = uuid.uuid4().hex
    request = ET.Element(
        "request",
        {
            "id": request_id,
            "operation": operation,
        },
    )
    if session_id is not None:
        request.set("sessionId", session_id)
    if expected_scene_filename is not None:
        request.set("expectedSceneFilename", expected_scene_filename)

    if expected_runtime_ids is not None:
        selection = ET.SubElement(
            request,
            "selection",
            {"count": str(len(expected_runtime_ids))},
        )
        for index, runtime_id in enumerate(expected_runtime_ids):
            ET.SubElement(
                selection,
                "node",
                {"index": str(index), "runtimeId": str(runtime_id)},
            )

    if node_name_path is not None:
        name_path = ET.SubElement(
            request,
            "namePath",
            {"count": str(len(node_name_path))},
        )
        for index, name in enumerate(node_name_path):
            ET.SubElement(
                name_path,
                "part",
                {"index": str(index), "name": name},
            )

    for name, vector in (
        ("translation", translation),
        ("rotation", rotation),
        ("scale", scale),
    ):
        if vector is not None:
            ET.SubElement(
                request,
                name,
                {"value": " ".join(format(component, ".17g") for component in vector)},
            )

    request_path = directory / "request.xml"
    temporary_path = directory / f".request-{request_id}.tmp"
    response_path = directory / f"response-{request_id}.xml"

    try:
        ET.ElementTree(request).write(
            temporary_path,
            encoding="utf-8",
            xml_declaration=True,
        )
        os.replace(temporary_path, request_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    deadline = time.monotonic() + _REQUEST_TIMEOUT_SECONDS
    parsed_response: ET.Element | None = None
    while time.monotonic() < deadline:
        try:
            if response_path.is_file():
                if response_path.stat().st_size > _MAX_RESPONSE_BYTES:
                    raise ValueError("The GIANTS Editor bridge response is too large.")
                candidate = ET.parse(response_path).getroot()
                if candidate.tag == "response" and candidate.get("id") == request_id:
                    parsed_response = candidate
                    break
        except ET.ParseError:
            pass
        except OSError:
            pass
        time.sleep(_POLL_INTERVAL_SECONDS)

    if parsed_response is None:
        _remove_request_if_current(request_path, request_id)
        response_path.unlink(missing_ok=True)
        raise TimeoutError(
            "No response from GIANTS Editor. Load the PROJECT TITAN Live Bridge script "
            "from the Editor's Scripts menu and try again."
        )

    response = _parse_response(parsed_response)
    response_path.unlink(missing_ok=True)
    _remove_request_if_current(request_path, request_id)
    if not response["success"]:
        raise ValueError(response.get("error") or "The GIANTS Editor bridge rejected the request.")
    return request_id, response


def _remove_request_if_current(request_path: Path, request_id: str) -> None:
    try:
        root = ET.parse(request_path).getroot()
        if root.tag == "request" and root.get("id") == request_id:
            request_path.unlink(missing_ok=True)
    except (ET.ParseError, OSError):
        return


def _parse_vector(value: str | None) -> list[float] | None:
    if value is None or not value.strip():
        return None
    try:
        result = [float(component) for component in value.split()]
    except ValueError as error:
        raise ValueError("The GIANTS Editor bridge returned an invalid vector.") from error
    if len(result) != 3 or any(not math.isfinite(component) for component in result):
        raise ValueError("The GIANTS Editor bridge returned an invalid vector.")
    return result


def _parse_response(root: ET.Element) -> dict[str, Any]:
    success = root.get("success") == "1"
    nodes: list[dict[str, Any]] = []
    for node in root.findall("node"):
        try:
            runtime_id = int(node.get("runtimeId", "0"))
            parent_runtime_id = int(node.get("parentRuntimeId", "0"))
            child_count = int(node.get("childCount", "0"))
        except ValueError as error:
            raise ValueError("The GIANTS Editor bridge returned invalid node identifiers.") from error

        nodes.append(
            {
                "runtime_id": runtime_id,
                "name": node.get("name", ""),
                "parent_runtime_id": parent_runtime_id,
                "parent_name": node.get("parentName", ""),
                "local_translation": _parse_vector(node.get("localTranslation")),
                "world_translation": _parse_vector(node.get("worldTranslation")),
                "rotation_radians": _parse_vector(node.get("rotation")),
                "scale": _parse_vector(node.get("scale")),
                "child_count": child_count,
            }
        )

    try:
        selected_count = int(root.get("selectedCount", "0"))
        modified_count = int(root.get("modifiedCount", "0"))
    except ValueError as error:
        raise ValueError("The GIANTS Editor bridge returned invalid counts.") from error

    return {
        "success": success,
        "error": root.get("error", ""),
        "session_id": root.get("sessionId", ""),
        "scene_filename": root.get("sceneFilename", ""),
        "scene_root_name": root.get("sceneRootName", ""),
        "selected_count": selected_count,
        "selection_truncated": root.get("selectionTruncated") == "1",
        "modified_count": modified_count,
        "nodes": nodes,
    }


def _send_editor_request(
    directory: Path,
    operation: str,
    session_id: str | None = None,
    expected_runtime_ids: list[int] | None = None,
    expected_scene_filename: str | None = None,
    node_name_path: list[str] | None = None,
    translation: list[float] | None = None,
    rotation: list[float] | None = None,
    scale: list[float] | None = None,
) -> dict[str, Any]:
    _, response = _write_request(
        directory=directory,
        operation=operation,
        session_id=session_id,
        expected_runtime_ids=expected_runtime_ids,
        expected_scene_filename=expected_scene_filename,
        node_name_path=node_name_path,
        translation=translation,
        rotation=rotation,
        scale=scale,
    )
    return response


def _read_selection(directory: Path) -> tuple[str, dict[str, Any]]:
    hello = _send_editor_request(directory, "hello")
    session_id = hello["session_id"]
    if not session_id:
        raise ValueError("The GIANTS Editor bridge did not provide a session identifier.")
    response = _send_editor_request(directory, "selection", session_id=session_id)
    return session_id, response


def _scene_is_in_project(scene_filename: str, project_root: Path) -> bool:
    if not scene_filename:
        return False
    try:
        scene = Path(scene_filename).expanduser().resolve(strict=True)
        scene.relative_to(project_root)
        return scene.is_file()
    except (OSError, ValueError):
        return False


def get_editor_status(project_root: Path) -> dict[str, Any]:
    directory = _bridge_directory()
    with _bridge_lock(directory):
        _, response = _read_selection(directory)

    in_project = _scene_is_in_project(response["scene_filename"], project_root)
    return {
        "connected": True,
        "scene_loaded": bool(response["scene_filename"]),
        "scene_in_project": in_project,
        "scene_filename": response["scene_filename"] if in_project else None,
        "scene_root_name": response["scene_root_name"],
        "selected_count": response["selected_count"],
        "selection_truncated": response["selection_truncated"],
    }


def read_live_editor_selection(project_root: Path) -> dict[str, Any]:
    directory = _bridge_directory()
    with _bridge_lock(directory):
        _, response = _read_selection(directory)

    if not _scene_is_in_project(response["scene_filename"], project_root):
        raise ValueError(
            "Open an I3D scene inside TITAN_PROJECT_ROOT before reading the live Editor selection."
        )

    return {
        "scene_filename": response["scene_filename"],
        "scene_root_name": response["scene_root_name"],
        "selected_count": response["selected_count"],
        "exported_count": len(response["nodes"]),
        "truncated": response["selection_truncated"],
        "nodes": response["nodes"],
    }


def select_live_editor_i3d_node(
    project_root: Path,
    i3d_file: Path,
    node_name_path: list[str],
) -> dict[str, Any]:
    if not node_name_path or len(node_name_path) > 256:
        raise ValueError("The I3D node path must contain between 1 and 256 named nodes.")

    directory = _bridge_directory()
    with _bridge_lock(directory):
        session_id, selection = _read_selection(directory)
        scene_filename = selection["scene_filename"]
        if not _scene_is_in_project(scene_filename, project_root):
            raise ValueError(
                "Open an I3D scene inside TITAN_PROJECT_ROOT before selecting an Editor node."
            )
        if Path(scene_filename).resolve(strict=True) != i3d_file.resolve(strict=True):
            raise ValueError(
                "The requested I3D file is not the scene currently open in GIANTS Editor."
            )

        response = _send_editor_request(
            directory,
            "selectNode",
            session_id=session_id,
            expected_scene_filename=scene_filename,
            node_name_path=node_name_path,
        )

    return {
        "scene_filename": response["scene_filename"],
        "selected_count": response["selected_count"],
        "selected_nodes": response["nodes"],
    }


def set_live_editor_selection_transform(
    project_root: Path,
    expected_runtime_ids: list[int],
    translation: list[float] | None = None,
    rotation: list[float] | None = None,
    scale: list[float] | None = None,
) -> dict[str, Any]:
    if not any(vector is not None for vector in (translation, rotation, scale)):
        raise ValueError("Provide translation, rotation, scale, or a combination of them.")
    if not expected_runtime_ids or len(expected_runtime_ids) > _MAX_SELECTION:
        raise ValueError(f"expected_runtime_ids must contain between 1 and {_MAX_SELECTION} values.")
    if any(type(runtime_id) is not int or runtime_id <= 0 for runtime_id in expected_runtime_ids):
        raise ValueError("expected_runtime_ids must contain positive integer runtime IDs.")
    if len(set(expected_runtime_ids)) != len(expected_runtime_ids):
        raise ValueError("expected_runtime_ids must not contain duplicates.")

    for vector in (translation, rotation, scale):
        if vector is None:
            continue
        if len(vector) != 3 or any(
            not math.isfinite(component)
            or abs(component) > _MAX_TRANSFORM_COMPONENT
            for component in vector
        ):
            raise ValueError(
                "Transform vectors must contain three finite values with absolute values at most 1,000,000."
            )

    directory = _bridge_directory()
    with _bridge_lock(directory):
        session_id, selection = _read_selection(directory)
        if not _scene_is_in_project(selection["scene_filename"], project_root):
            raise ValueError(
                "Open an I3D scene inside TITAN_PROJECT_ROOT before changing Editor nodes."
            )
        if selection["selection_truncated"]:
            raise ValueError(
                f"The Editor has more than {_MAX_SELECTION} selected nodes; reduce the selection first."
            )
        current_ids = [node["runtime_id"] for node in selection["nodes"]]
        if current_ids != expected_runtime_ids:
            raise ValueError(
                "The Editor selection changed. Read the live selection again before applying a transform."
            )

        response = _send_editor_request(
            directory,
            "setTransform",
            session_id=session_id,
            expected_runtime_ids=expected_runtime_ids,
            expected_scene_filename=selection["scene_filename"],
            translation=translation,
            rotation=rotation,
            scale=scale,
        )

    if not _scene_is_in_project(response["scene_filename"], project_root):
        raise ValueError("The Editor scene changed outside TITAN_PROJECT_ROOT; no result was accepted.")

    return {
        "scene_filename": response["scene_filename"],
        "modified_count": response["modified_count"],
        "nodes": response["nodes"],
        "saved": False,
        "save_instruction": "The changes are in the Editor session. Press Ctrl+S in GIANTS Editor to save the I3D.",
    }

