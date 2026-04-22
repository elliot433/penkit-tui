Prüfe die Datei $ARGUMENTS im PenKit-Repo (C:/root/Documents/penkit-tui) auf:

1. Echte subprocess/network Calls — kein Dummy-Output oder simuliertes Ergebnis
2. Fehlende Imports (asyncio, shutil, etc.)
3. Async-Generator Bugs: yield in stop()-Methoden
4. Funktionsnamen stimmen mit dem was classic_menu.py aufruft überein
5. Exception-Handling bei fehlendem Binary (shutil.which + Fehlermeldung)

Finde alle Probleme und fixe sie direkt. Dann: git add + commit + push.
