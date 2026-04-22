Füge ein neues Tool zu PenKit hinzu: $ARGUMENTS

Anforderungen:
- Erstelle die Python-Datei unter tools/<kategorie>/<name>.py
- Echte Implementierung mit subprocess/CommandRunner — kein Dummy-Code
- AsyncGenerator[str, None] für alle öffentlichen Funktionen die Output erzeugen
- stop()-Methode als normaler async coroutine (KEIN yield)
- shutil.which() Check für externe Binaries mit Install-Hinweis
- Trage das Tool in tools/<kategorie>/__init__.py ein
- Füge einen Menü-Eintrag in classic_menu.py hinzu
- git add + commit + push
