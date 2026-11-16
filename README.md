# PROJECT TITAN

MCP-Schnittstelle für die Arbeit mit GIANTS-Editor-Projekten.

## Ziel

PROJECT TITAN soll MCP-Clients wie Codex kontrollierte Werkzeuge für GIANTS-Editor-Projekte bereitstellen. Die Entwicklung und Tests mit dem Editor laufen lokal auf Windows.

## Aktueller Stand

PROJECT TITAN bietet lokale MCP-Werkzeuge zum Lesen von `.i3d`-Dateien sowie einen experimentellen Live-Bridge-Prototyp für den GIANTS Editor. Das Editor-Skript tauscht strukturierte XML-Nachrichten über einen Ordner in `%LOCALAPPDATA%` mit dem MCP aus. Es kann die aktuelle Auswahl lesen, einen Knoten anhand seiner I3D-`nodeId` in der geöffneten Szene auswählen und absolute lokale Translation, Rotation und Scale auf die danach bestätigte Auswahl anwenden. Das Skript führt keinen beliebigen Lua-Code aus. Änderungen bleiben zunächst in der geöffneten Editor-Szene; gespeichert wird mit **Strg+S** im Editor.

Für die Live-Verbindung muss `scripts/giants_editor/project_titan_live_bridge.lua` im Editor-Nutzerskriptordner liegen und `TITAN_EDITOR_BRIDGE_DIR` auf den passenden AppData-Unterordner zeigen. Die Einrichtung steht in [docs/codex-setup.md](docs/codex-setup.md). Grenzen und untersuchte Verbindungswege stehen in [docs/integration-research.md](docs/integration-research.md).

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

Der Server stellt über stdio Werkzeuge zum Lesen und zur kontrollierten Live-Steuerung bereit. `search_i3d_nodes` findet Knoten projektweit anhand ihres Namens oder ihrer `nodeId`. `inspect_i3d_node` liefert XML-Attribute, rohe lokale Translation/Rotation/Scale, Knotenpfad und direkte Kinder. `get_live_editor_status` und `read_live_editor_selection` fragen den laufenden Editor ab. `set_live_editor_selection_transform` ändert nur die Auswahl, deren Laufzeit-IDs unmittelbar vorher bestätigt wurden. Live-Abfragen und Änderungen sind auf Szenen innerhalb von `TITAN_PROJECT_ROOT` beschränkt. Angefragte I3D-Dateien müssen ebenfalls innerhalb dieses Projektordners liegen.

