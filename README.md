# PROJECT TITAN

MCP-Schnittstelle für die Arbeit mit GIANTS-Editor-Projekten.

## Ziel

PROJECT TITAN soll MCP-Clients wie Codex kontrollierte Werkzeuge für GIANTS-Editor-Projekte bereitstellen. Die Entwicklung und Tests mit dem Editor laufen lokal auf Windows.

## Aktueller Stand

Der erste Prototyp ist ein lokaler, schreibgeschützter MCP-Server. Er kann `.i3d`-Dateien in einem konfigurierten Projektordner finden, Scene-Knoten und Datei-Verweise zusammenfassen und häufige ID-Referenzfehler und fehlende lokale I3D-Dateiverweise melden. Für die aktuelle Auswahl gibt es zusätzlich einen manuell auszuführenden GIANTS-Editor-Snapshot. Der MCP liest die exportierte XML-Datei; eine automatische oder kontinuierliche Live-Steuerung ist nicht enthalten.

Die offizielle GIANTS-Dokumentation beschreibt ein Editor-Script-Fenster sowie Debugger-Verbindungen über die GIANTS-VS-Code-Erweiterung. Die Recherche und die offenen Integrationsfragen stehen in [docs/integration-research.md](docs/integration-research.md). Hinweise zur Verbindung mit Codex stehen in [docs/codex-setup.md](docs/codex-setup.md).

## Voraussetzungen

- Python 3.11 oder neuer
- [uv](https://docs.astral.sh/uv/)
- GIANTS-Editor-Projektdateien lokal auf Windows

## Lokal starten

Im Projektordner:

~~~powershell
uv sync
$env:TITAN_PROJECT_ROOT = "C:\Pfad\zu\deinem\GIANTS-Projekt"
uv run titan-mcp
~~~

Der Server stellt die schreibgeschützten MCP-Werkzeuge `list_i3d_files`, `inspect_i3d`, `search_i3d_nodes`, `inspect_i3d_node`, `check_i3d_integrity` und `read_editor_selection_snapshot` über stdio bereit. `search_i3d_nodes` findet Knoten projektweit anhand ihres Namens oder ihrer `nodeId`. `inspect_i3d_node` liefert zu einer `nodeId` die XML-Attribute, die rohe lokale Translation/Rotation/Scale, den Knotenpfad und direkte Kinder. `read_editor_selection_snapshot` liest den zuletzt manuell exportierten Zustand der aktuellen Editor-Auswahl. Angefragte Dateien dürfen nicht außerhalb von `TITAN_PROJECT_ROOT` liegen.
