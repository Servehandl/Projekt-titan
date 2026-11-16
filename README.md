# PROJECT TITAN

MCP-Schnittstelle für die Arbeit mit GIANTS-Editor-Projekten.

## Ziel

PROJECT TITAN soll MCP-Clients wie Codex kontrollierte Werkzeuge für GIANTS-Editor-Projekte bereitstellen. Die Entwicklung und Tests mit dem Editor laufen lokal auf Windows.

## Aktueller Stand

Der erste Prototyp ist ein lokaler, schreibgeschützter MCP-Server. Er kann `.i3d`-Dateien in einem konfigurierten Projektordner finden und ihre XML-Struktur zusammenfassen. Eine Live-Steuerung des Editors wird erst ergänzt, wenn ein stabiler Integrationsweg feststeht.

Die offizielle GIANTS-Dokumentation beschreibt ein Editor-Script-Fenster sowie Debugger-Verbindungen über die GIANTS-VS-Code-Erweiterung. Die Recherche und die offenen Integrationsfragen stehen in [docs/integration-research.md](docs/integration-research.md). Hinweise zur Verbindung mit Codex stehen in [docs/codex-setup.md](docs/codex-setup.md).

## Voraussetzungen

- Python 3.11 oder neuer
- [uv](https://docs.astral.sh/uv/)
- GIANTS-Editor-Projektdateien lokal auf Windows

## Lokal starten

Im Projektordner:

```powershell
uv sync
$env:TITAN_PROJECT_ROOT = "C:\Pfad\zu\deinem\GIANTS-Projekt"
uv run titan-mcp
```

Der Server stellt die schreibgeschützten MCP-Werkzeuge `list_i3d_files` und `inspect_i3d` über stdio bereit. Angefragte Dateien dürfen nicht außerhalb von `TITAN_PROJECT_ROOT` liegen.
