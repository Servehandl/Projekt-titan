# Codex lokal anbinden

Der PROJECT-TITAN-Server läuft über **stdio** als lokaler Prozess. Er liest GIANTS-Editor-Projektdateien auf demselben Windows-Rechner, auf dem er gestartet wird.

## Voraussetzungen

- Windows 10 oder 11
- Python 3.11 oder neuer
- [uv](https://docs.astral.sh/uv/)
- Codex CLI installiert und im PowerShell-Pfad verfügbar
- Ein lokaler GIANTS-Editor-Projektordner

## Repository holen und vorbereiten

Wähle einen Ordner, in dem das Repository liegen soll. Beispiel:

```powershell
git clone https://github.com/Servehandl/Projekt-titan.git "C:\Tools\Projekt-titan"
Set-Location "C:\Tools\Projekt-titan"
uv sync
```

## MCP-Server in Codex registrieren

Ersetze den Beispielpfad durch den Ordner deines GIANTS-Projekts:

```powershell
codex mcp add project-titan --env "TITAN_PROJECT_ROOT=D:\FarmingSimulator\MyMod" -- uv run --project "C:\Tools\Projekt-titan" titan-mcp
```

Prüfe die Registrierung:

```powershell
codex mcp list
```

Codex CLI und Codex IDE verwenden dieselbe MCP-Konfiguration. Wenn Codex beim Registrieren bereits geöffnet war, lade es neu. Danach sollte der Server mit den fünf Werkzeugen unter den MCP-Werkzeugen verfügbar sein:

- `list_i3d_files`: I3D-Dateien im Projekt finden
- `inspect_i3d`: Scene-Knoten und Dateiverweise einer I3D-Datei zusammenfassen
- `search_i3d_nodes`: Scene-Knoten in allen I3D-Dateien nach Name oder `nodeId` suchen
- `inspect_i3d_node`: einen Knoten samt rohen XML-Attributen, Hierarchie und direkten Kindern ausgeben
- `check_i3d_integrity`: häufige ID-Fehler und fehlende lokale Dateiverweise prüfen

## Grenzen

Der Server ist derzeit schreibgeschützt. Er ändert weder I3D-Dateien noch steuert er die GIANTS-Editor-Oberfläche. Relative Datei-Prüfungen bleiben innerhalb von `TITAN_PROJECT_ROOT`; `$data`-Pfade werden ausgelassen, da sie auf Spieldateien außerhalb des Mod-Projektordners verweisen.

Eine lokale **stdio**-Verbindung startet den MCP-Server in der jeweiligen Codex-Ausführungsumgebung. Eine Cloud-Aufgabe kann daher nur auf Dateien zugreifen, die in ihrer Cloud-Umgebung vorhanden sind. Für Dateien auf deinem Windows-PC muss der Server lokal in Codex laufen.
