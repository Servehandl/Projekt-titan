# GIANTS-Editor-Integration: Recherche

Stand: 16. November 2026

## Offizielle Schnittstellen, die dokumentiert sind

- Die GIANTS-Editor-Dokumentation beschreibt ein Script-Fenster, in dem Lua-Snippets mit **Shift+Enter** ausgeführt werden können. Als Beispiel wird eine Änderung der Nebeleinstellungen gezeigt.
- Die offizielle GIANTS-Erweiterung für Visual Studio Code kann sich mit einem laufenden GIANTS Editor verbinden. Laut GDN wird im Editor **Scripts > Connect to Studio** gewählt; die Erweiterung stellt dann einen Debug-Listener sowie Debugger-Funktionen wie Variablenansicht und Script-Konsole bereit.
- GIANTS weist darauf hin, dass GIANTS Studio nicht mehr gepflegt wird und empfiehlt die VS-Code-Erweiterung für Skriptentwicklung und Debugging.

## Schlussfolgerung

In den geprüften offiziellen Unterlagen ist keine allgemeine externe API beschrieben, über die ein eigener Prozess beliebige Editor-Aktionen ausführen kann. Das ist eine Aussage über die geprüften Dokumente, kein Beweis, dass es keine undokumentierten oder versionsspezifischen Wege gibt.

Darum beginnt PROJECT TITAN mit einem lokalen, schreibgeschützten MCP-Server für Projektdateien. Eine Live-Verbindung zum Editor bleibt offen, bis sich ein stabiler und unterstützter Weg belegen lässt.

## Erster Prototyp

- MCP-Transport: lokales **stdio**
- Laufzeit: Python 3.11+
- Umfang: `.i3d`-Dateien im ausdrücklich konfigurierten Projektordner finden und deren XML-Struktur auslesen
- Schreibzugriffe und Editor-Steuerung: zunächst nicht enthalten
- Sicherheitsgrenze: angefragte Dateien müssen innerhalb von `TITAN_PROJECT_ROOT` liegen

## Quellen

- [GIANTS Editor documentation](https://gdn.giants-software.com/editor.php) — Script-Fenster und Editor-Funktionen
- [GIANTS Farming Simulator IDE Support for VS Code](https://gdn.giants-software.com/vscode.php) — Verbindung des Editors und Debugger-Funktionen
- [GIANTS Developer Network downloads](https://gdn.giants-software.com/downloads.php/index.php) — Editor-Versionen für Windows
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — Python SDK, MCPServer und stdio
