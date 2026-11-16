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
codex mcp add project-titan --env "TITAN_PROJECT_ROOT=D:\FarmingSimulator\MyMod" --env "TITAN_EDITOR_BRIDGE_DIR=C:\Users\<Benutzer>\AppData\Local\GIANTS Editor 64bit 10.0.14\project-titan-bridge" -- uv run --project "C:\Tools\Projekt-titan" titan-mcp
```

Prüfe die Registrierung:

```powershell
codex mcp list
```

Codex CLI und Codex IDE verwenden dieselbe MCP-Konfiguration. Wenn Codex beim Registrieren bereits geöffnet war, lade es neu. Danach stehen die Dateiprüfungen und die Live-Werkzeuge bereit:

- `list_i3d_files`: I3D-Dateien im Projekt finden
- `inspect_i3d`: Scene-Knoten und Dateiverweise einer I3D-Datei zusammenfassen
- `search_i3d_nodes`: Scene-Knoten in allen I3D-Dateien nach Name oder `nodeId` suchen
- `inspect_i3d_node`: einen Knoten samt rohen XML-Attributen, Hierarchie und direkten Kindern ausgeben
- `check_i3d_integrity`: häufige ID-Fehler und fehlende lokale Dateiverweise prüfen
- `read_editor_selection_snapshot`: den letzten manuellen Auswahl-Snapshot aus dem GIANTS Editor lesen
- `get_live_editor_status`: prüfen, ob das Editor-Skript läuft und eine Szene aus dem Projekt geöffnet ist
- `read_live_editor_selection`: aktuelle Auswahl direkt aus dem laufenden Editor lesen
- `select_live_editor_i3d_node`: einen Knoten anhand seiner I3D-`nodeId` in der aktuell geöffneten Szene auswählen
- `set_live_editor_selection_transform`: Translation, Rotation (Radiant) und/oder Scale auf die bestätigte aktuelle Auswahl setzen

## Live-Bridge im GIANTS Editor starten

1. Kopiere `scripts/giants_editor/project_titan_live_bridge.lua` in den Nutzerskriptordner der passenden Editor-Version. Für Editor 10.0.14 ist das `%LOCALAPPDATA%\GIANTS Editor 64bit 10.0.14\scripts`.
2. Starte den Editor neu, damit das als `AlwaysLoaded` markierte Skript geladen wird. In der bereits laufenden Editor-Sitzung kannst du das Skript stattdessen einmal über **Skripte > Nutzerskripte > PROJECT TITAN Live Bridge** ausführen.
3. Setze `TITAN_EDITOR_BRIDGE_DIR` in der MCP-Konfiguration auf `%LOCALAPPDATA%\GIANTS Editor 64bit 10.0.14\project-titan-bridge` (ersetze `%LOCALAPPDATA%` im `codex mcp add`-Befehl durch den vollständigen Windows-Pfad).
4. Lade Codex neu und rufe `get_live_editor_status` auf. Die geöffnete Szene muss innerhalb von `TITAN_PROJECT_ROOT` liegen.

`select_live_editor_i3d_node` funktioniert nur, wenn dieselbe I3D-Datei im Editor geöffnet ist. Bei mehrdeutigen Namen bricht die Brücke ab, ohne einen Knoten auszuwählen. `set_live_editor_selection_transform` verlangt die Laufzeit-IDs aus `read_live_editor_selection` und prüft die Auswahl vor dem Schreiben erneut. Rotation wird in Radiant angegeben. Der Befehl ändert nur die geöffnete Szene im Editor; zum Speichern drücke dort **Strg+S**. Die Brücke nimmt keine beliebigen Lua-Snippets an.


## Aktuelle Auswahl aus dem GIANTS Editor übergeben

Der Editor-Snapshot ist ein manueller Einweg-Schritt. Er ändert keine I3D-Datei.

1. Öffne `scripts/giants_editor/export_selection.lua` aus dem Repository.
2. Ändere oben in `outputPath` den Beispielpfad auf `.project-titan-editor-selection.xml` direkt im Ordner, den du als `TITAN_PROJECT_ROOT` eingetragen hast.
3. Öffne das Skript im GIANTS Editor und führe es über den Script Editor aus.
4. Rufe in Codex das Werkzeug `read_editor_selection_snapshot` auf. Es liefert Name, Parent, lokale und globale Position, Rotation, Skalierung und Kinderzahl der ausgewählten Knoten.
5. Nach einer neuen Auswahl das Skript erneut ausführen, damit der Snapshot aktualisiert wird.

Das Skript exportiert höchstens 500 ausgewählte Knoten. Der Snapshot enthält GIANTS-Laufzeit-IDs; diese sind keine `nodeId`-Werte aus der I3D-Datei. Die XML-Datei bleibt innerhalb des konfigurierten Projektordners und ist in `.gitignore` eingetragen. Das ist der manuelle Fallback; für die kontinuierliche Verbindung nutze die Live-Bridge oben.

## Grenzen

Der Server schreibt keine I3D-Dateien direkt. Die Live-Bridge kann Transformationen der bestätigten aktuellen Editor-Auswahl im Arbeitsspeicher des Editors ändern; diese werden erst mit **Strg+S** gespeichert. Relative Datei-Prüfungen und Live-Änderungen bleiben auf `TITAN_PROJECT_ROOT` beschränkt; `$data`-Pfade werden ausgelassen, da sie auf Spieldateien außerhalb des Mod-Projektordners verweisen.

Eine lokale **stdio**-Verbindung startet den MCP-Server in der jeweiligen Codex-Ausführungsumgebung. Eine Cloud-Aufgabe kann daher nur auf Dateien zugreifen, die in ihrer Cloud-Umgebung vorhanden sind. Für Dateien auf deinem Windows-PC muss der Server lokal in Codex laufen.

