# Wir importieren unsere grafische Benutzeroberfläche (GUI) aus der gui.py Datei
import gui

# Diese Zeilen sorgen dafür, dass unser Programm startet, 
# wenn man diese Datei direkt ausführt.
# Es ruft die Funktion 'start_app' aus gui.py auf,
# die das erste Fenster für den Master-Key öffnet.
if __name__ == "__main__":
    gui.start_app()
