# Codex lokal anbinden

Der PROJECT-TITAN-Server läuft über **stdio** als lokaler Prozess. Für den ersten Prototyp muss er auf dem Windows-Rechner laufen, auf dem auch der GIANTS-Projektordner liegt.

## Voraussetzungen

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Codex CLI verfügbar im Terminal
- Repository lokal geklont

## Repository vorbereiten

Im Repository-Ordner:

```powershell
uv sync
```

## MCP-Server in Codex registrieren

Ersetze die Beispielpfade durch die tatsächlichen Ordner:

```powershell
codex mcp add project-titan --env "TITAN_PROJECT_ROOT=C:\Pfad\zu\deinem\GIANTS-Projekt" -- uv run --project "C:\Pfad\zu\Projekt-titan" titan-mcp
```

Danach kannst du die Registrierung mit `codex mcp list` prüfen. Starte Codex neu und gib im Composer `/mcp` ein, um die Verbindung und die Werkzeuge zu sehen.

## Lokal und Cloud

Eine lokale **stdio**-Verbindung startet den MCP-Server in der jeweiligen Codex-Ausführungsumgebung. Eine Cloud-Aufgabe kann daher nur auf Dateien zugreifen, die in ihrer Cloud-Umgebung vorhanden sind. Für Dateien und den GIANTS Editor auf deinem Windows-PC muss der Server lokal laufen; er überbrückt nicht automatisch in eine Cloud-Aufgabe.
