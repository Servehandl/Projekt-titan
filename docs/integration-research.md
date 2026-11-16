# GIANTS-Editor-Integration: Recherche

Stand: 17. November 2026

## Offizielle Editor- und Debugger-Wege

- Die GIANTS-Editor-Dokumentation beschreibt ein Script-Fenster, in dem Lua-Snippets mit **Shift+Enter** ausgeführt werden können.
- Die offizielle Erweiterung **Farming Simulator IDE Support** verbindet sich mit einem laufenden GIANTS Editor. Im Editor wird **Scripts > Connect to Studio** gewählt. Danach kann die Erweiterung Debugger-Funktionen wie Variablenansicht und Script-Konsole anbieten.
- Der Marketplace beschreibt einen TCP-Debugger und nennt in den Einstellungen die Ports 61407 und 61408. Diese sind für die Verbindung der GIANTS-IDE-Erweiterung gedacht; die Dokumentation weist sie nicht als allgemeine API für externe MCP-Server aus.
- Die Debug-Konsole und Watch-Ausdrücke können Lua auswerten, aber die ältere offizielle Debugger-Dokumentation erlaubt das Ausführen neuer Skripte nur bei angehaltener Ausführung. Beim Prüfen des aktuellen offiziellen VSIX-Pakets (Version 1.1.0) sendet der DAP-`evaluate`-Handler Lua an den Editor und antwortet mit leerem Ergebnistext. Damit ist der Debugger ein brauchbarer manueller Entwicklungsweg, aber keine fertige MCP-Abfrage mit Antwortwerten.
- GIANTS weist darauf hin, dass GIANTS Studio nicht mehr gepflegt wird und empfiehlt die VS-Code-Erweiterung für Skriptentwicklung und Debugging.

## Live-Bridge über das Editor-Skript-System

Die lokale GIANTS-Editor-Installation 10.0.14 bindet `addUpdateListener`, `getSceneFilename`, Auswahl- und Transformationsfunktionen sowie XML-Lese-/Schreibfunktionen. Das Editor-Skript-System lädt Nutzerskripte aus dem AppData-Ordner `scripts`; der Prototyp ist als dauerhaft geladenes Nutzerskript markiert. Damit kann ein Skript im Editor-Update-Loop auf eine lokale XML-Anfrage warten und XML-Antworten zurückschreiben, ohne die Lua-Standard-I/O-Funktionen zu verwenden.

Der Live-Prototyp verwendet eine lokale Mailbox unter `%LOCALAPPDATA%`:

- Der MCP schreibt strukturierte Requests atomar nach `request.xml`.
- Das Lua-Skript prüft die Mailbox im Update-Loop und antwortet unter einer eindeutigen Request-ID.
- Der Server akzeptiert Live-Abfragen und Transformationen nur, wenn `getSceneFilename()` innerhalb von `TITAN_PROJECT_ROOT` liegt.
- Vor einer Transformation prüft das Lua-Skript erneut Szenenpfad und Auswahl-IDs. Die Auswahl wird also nicht durch möglicherweise veraltete Laufzeit-IDs ersetzt.
- Die erlaubten Live-Aktionen sind auf das Lesen der Auswahl, das eindeutige Auflösen eines I3D-`nodeId` zur Auswahl im geöffneten Scenegraph und lokale Translation, Rotation und Scale der bestätigten aktuellen Auswahl begrenzt. Es gibt keinen allgemeinen Lua-Eval-Befehl.
- Der Editor stellt in den geprüften Script-Bindings keinen I3D-Speicherbefehl bereit. Transformationen bleiben bis zum manuellen **Strg+S** im Editor ungespeichert.

Auf dem untersuchten Rechner lauschte der laufende Editorprozess zusätzlich auf `127.0.0.1:8086`. Eine harmlose HTTP-GET-Anfrage wurde zurückgesetzt; in den installierten Skript-Bindings und der offiziellen Dokumentation fand sich dafür kein API-Vertrag. Dieser Port wird deshalb nicht verwendet.

## I3D-Dateiformat

Die GDN-Dokumentation beschreibt I3D als XML mit optionalen Abschnitten wie Files, Materials, Shapes und Scene. Im Scenegraph tragen Knoten eine `nodeId`; Dateiverweise werden unter `Files` über `fileId` und `filename` aufgelöst.

Der Prototyp liest deshalb die Scene-Knoten und File-Verweise direkt aus der I3D-Datei. Der Integritätscheck prüft häufige ID-Verweise. Zusätzlich prüft er Dateien, die in `Files` ausdrücklich mit `relativePath="true"` auf einen lokalen Pfad innerhalb des Projektordners verweisen. `$data`-Referenzen werden übersprungen, weil sie auf Spieldateien außerhalb des Mod-Projektordners zeigen können. Das ersetzt keine vollständige GDN-Schema-Validierung. Die Dateien werden nicht verändert.

## Schlussfolgerung

In den geprüften offiziellen Quellen ist keine allgemeine externe Editor-API dokumentiert. Der gewählte Live-Prototyp nutzt daher den unterstützten Editor-Skriptmechanismus innerhalb des Editors und eine lokale Datei-Mailbox zwischen Editor und MCP. Das ist eine eigens gebaute Brücke, keine GIANTS-Netzwerk-API. Der frühere manuelle Snapshot bleibt als einfacher Einweg-Fallback verfügbar.

## Prototyp

- MCP-Transport: lokales **stdio**
- Laufzeit: Python 3.11+
- Werkzeuge: I3D-Dateien finden, Scene-Knoten und Dateiverweise zusammenfassen, Knoten nach Name oder `nodeId` suchen, Knoten inspizieren, Referenzen prüfen, Live-Editor-Status und Auswahl lesen sowie lokale Transformationen der bestätigten aktuellen Auswahl setzen
- Direkte I3D-Dateischreibzugriffe: nicht enthalten; Live-Änderungen bleiben im Editor-Speicher, bis dort manuell gespeichert wird
- Sicherheitsgrenze: angefragte Dateien müssen innerhalb von `TITAN_PROJECT_ROOT` liegen

## Quellen

- [GIANTS Editor documentation](https://gdn.giants-software.com/editor.php) — Script-Fenster und Editor-Funktionen
- [GIANTS Farming Simulator IDE Support for VS Code](https://gdn.giants-software.com/vscode.php) — Verbindung des Editors und Debugger-Funktionen
- [GIANTS IDE Support on Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=GIANTSSoftware.farmingsimulator-ide) — Debugger-Funktionen und TCP-Einstellungen
- [GIANTS Debugger/Studio documentation](https://gdn.giants-software.com/documentation_print.php?category=1&function=1&version=engine) — Einschränkung der Script-Konsole auf angehaltene Ausführung
- [GIANTS I3D format documentation](https://gdn.giants-software.com/documentation_i3d.php) — XML-Aufbau, Files und Scenegraph
- [GIANTS FS25 XML scripting documentation](https://gdn.giants-software.com/documentation_scripting_fs25.php?category=33&function=884&version=engine) — XML-Dateien mit `createXMLFile`, `setXML*` und `saveXMLFile` schreiben
- [GIANTS GDN forum: script file access](https://gdn.giants-software.com/thread.php?categoryId=3&threadId=6181) — Standard-I/O ist im GIANTS-Lua-Sandbox-Kontext eingeschränkt
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — Python SDK, MCPServer und stdio

