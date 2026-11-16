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

Codex CLI und Codex IDE verwenden dieselbe MCP-Konfiguration. Wenn Codex beim Registrieren bereits geöffnet war, lade es neu. Danach sollte der Server mit den sechs Werkzeugen unter den MCP-Werkzeugen verfügbar sein:

- `list_i3d_files`: I3D-Dateien im Projekt finden
- `inspect_i3d`: Scene-Knoten und Dateiverweise einer I3D-Datei zusammenfassen
- `search_i3d_nodes`: Scene-Knoten in allen I3D-Dateien nach Name oder `nodeId` suchen
- `inspect_i3d_node`: einen Knoten samt rohen XML-Attributen, Hierarchie und direkten Kindern ausgeben
- `check_i3d_integrity`: häufige ID-Fehler und fehlende lokale Dateiverweise prüfen
- `read_editor_selection_snapshot`: den letzten manuellen Auswahl-Snapshot aus dem GIANTS Editor lesen


## Aktuelle Auswahl aus dem GIANTS Editor übergeben

Der Editor-Snapshot ist ein manueller Einweg-Schritt. Er ändert keine I3D-Datei.

1. Öffne `scripts/giants_editor/export_selection.lua` aus dem Repository.
2. Ändere oben in `outputPath` den Beispielpfad auf `.project-titan-editor-selection.xml` direkt im Ordner, den du als `TITAN_PROJECT_ROOT` eingetragen hast.
3. Öffne das Skript im GIANTS Editor und führe es über den Script Editor aus.
4. Rufe in Codex das Werkzeug `read_editor_selection_snapshot` auf. Es liefert Name, Parent, lokale und globale Position, Rotation, Skalierung und Kinderzahl der ausgewählten Knoten.
5. Nach einer neuen Auswahl das Skript erneut ausführen, damit der Snapshot aktualisiert wird.

Das Skript exportiert höchstens 500 ausgewählte Knoten. Der Snapshot enthält GIANTS-Laufzeit-IDs; diese sind keine `nodeId`-Werte aus der I3D-Datei. Die XML-Datei bleibt innerhalb des konfigurierten Projektordners und ist in `.gitignore` eingetragen. Die Übergabe ist nicht automatisch; der Editor wird nicht per TCP fernbedient.

## Grenzen

Der Server ist derzeit schreibgeschützt. Er ändert weder I3D-Dateien noch steuert er die GIANTS-Editor-Oberfläche. Relative Datei-Prüfungen bleiben innerhalb von `TITAN_PROJECT_ROOT`; `$data`-Pfade werden ausgelassen, da sie auf Spieldateien außerhalb des Mod-Projektordners verweisen.

Eine lokale **stdio**-Verbindung startet den MCP-Server in der jeweiligen Codex-Ausführungsumgebung. Eine Cloud-Aufgabe kann daher nur auf Dateien zugreifen, die in ihrer Cloud-Umgebung vorhanden sind. Für Dateien auf deinem Windows-PC muss der Server lokal in Codex laufen.
