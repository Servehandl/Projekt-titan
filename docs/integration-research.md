# GIANTS-Editor-Integration: Recherche

Stand: 17. November 2026

## Offizielle Editor- und Debugger-Wege

- Die GIANTS-Editor-Dokumentation beschreibt ein Script-Fenster, in dem Lua-Snippets mit **Shift+Enter** ausgeführt werden können.
- Die offizielle Erweiterung **Farming Simulator IDE Support** verbindet sich mit einem laufenden GIANTS Editor. Im Editor wird **Scripts > Connect to Studio** gewählt. Danach kann die Erweiterung Debugger-Funktionen wie Variablenansicht und Script-Konsole anbieten.
- Der Marketplace beschreibt einen TCP-Debugger und nennt in den Einstellungen die Ports 61407 und 61408. Diese sind für die Verbindung der GIANTS-IDE-Erweiterung gedacht; die Dokumentation weist sie nicht als allgemeine API für externe MCP-Server aus.
- GIANTS weist darauf hin, dass GIANTS Studio nicht mehr gepflegt wird und empfiehlt die VS-Code-Erweiterung für Skriptentwicklung und Debugging.

## I3D-Dateiformat

Die GDN-Dokumentation beschreibt I3D als XML mit optionalen Abschnitten wie Files, Materials, Shapes und Scene. Im Scenegraph tragen Knoten eine `nodeId`; Dateiverweise werden unter `Files` über `fileId` und `filename` aufgelöst.

Der Prototyp liest deshalb die Scene-Knoten und File-Verweise direkt aus der I3D-Datei. Der Integritätscheck prüft häufige ID-Verweise. Zusätzlich prüft er Dateien, die in `Files` ausdrücklich mit `relativePath="true"` auf einen lokalen Pfad innerhalb des Projektordners verweisen. `$data`-Referenzen werden übersprungen, weil sie auf Spieldateien außerhalb des Mod-Projektordners zeigen können. Das ersetzt keine vollständige GDN-Schema-Validierung. Die Dateien werden nicht verändert.

## Schlussfolgerung

Die geprüften Quellen dokumentieren eine interaktive Lua-Script-Konsole sowie eine Debugger-Verbindung über die offizielle VS-Code-Erweiterung. Sie dokumentieren jedoch keine allgemeine externe API, über die ein eigener Prozess beliebige Aktionen im Editor ausführen kann. Das ist eine Aussage über die geprüften Dokumente, kein Beweis, dass es keine undokumentierten oder versionsspezifischen Wege gibt.

PROJECT TITAN startet daher mit lokalen, schreibgeschützten MCP-Werkzeugen für Projektdateien. Eine Live-Verbindung zum Editor bleibt offen, bis sich ein stabiler und unterstützter Integrationsweg belegen lässt.

## Prototyp

- MCP-Transport: lokales **stdio**
- Laufzeit: Python 3.11+
- Werkzeuge: I3D-Dateien finden, Scene-Knoten und Dateiverweise zusammenfassen, Scene-Knoten projektweit nach Name oder `nodeId` suchen, einzelne Knoten samt XML-Attributen und Hierarchie inspizieren sowie häufige ID-Referenzen und fehlende lokale Dateien prüfen
- Schreibzugriffe und Editor-Steuerung: zunächst nicht enthalten
- Sicherheitsgrenze: angefragte Dateien müssen innerhalb von `TITAN_PROJECT_ROOT` liegen

## Quellen

- [GIANTS Editor documentation](https://gdn.giants-software.com/editor.php) — Script-Fenster und Editor-Funktionen
- [GIANTS Farming Simulator IDE Support for VS Code](https://gdn.giants-software.com/vscode.php) — Verbindung des Editors und Debugger-Funktionen
- [GIANTS IDE Support on Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=GIANTSSoftware.farmingsimulator-ide) — Debugger-Funktionen und TCP-Einstellungen
- [GIANTS I3D format documentation](https://gdn.giants-software.com/documentation_print.php?category=121033&version=engine) — XML-Aufbau, Files und Scenegraph
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — Python SDK, MCPServer und stdio
