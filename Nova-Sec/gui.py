import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import random
import string
import time

from password_manager import save_password
from security import generate_key_from_master, decrypt_password

# --------------------------
# RAM-Speicher
# --------------------------
data_store = {}  # Hier speichern wir alle Passwörter und Infos temporär im Arbeitsspeicher
audit_log = []   # Hier protokollieren wir alle Aktionen (hinzufügen, bearbeiten, löschen)

app_settings = {
    "timeout_seconds": 60  # Standard Auto-Logout nach 60 Sekunden
}

# =====================================================================
# MASTER KEY FENSTER
# =====================================================================
def start_app():
    # Erstes Fenster für den Master-Key
    root = tk.Tk()
    root.title("Nova Security")
    root.geometry("520x240")

    tk.Label(root, text="Erstelle / Gib dein Master-Key ein:").pack(pady=10)

    master_var = tk.StringVar()
    master_entry = tk.Entry(root, textvariable=master_var, width=36, show="*")
    master_entry.pack(side="left", padx=10)

    # Bilder für Eye-Icon (Passwort ein-/ausblenden) und Generate-Icon
    eye_img = PhotoImage(file="eye.png").subsample(4, 4)
    generate_img = PhotoImage(file="generate.png").subsample(4, 4)

    # Passwort ein-/ausblenden
    def toggle_master():
        master_entry.config(show="" if master_entry.cget("show") == "*" else "*")
    tk.Button(root, image=eye_img, command=toggle_master, bd=0).pack(side="left", padx=6)

    # Master-Key automatisch generieren
    def generate_master():
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = ''.join(random.choices(chars, k=16))
        # Prüfen, ob Passwort alle Bedingungen erfüllt
        while not (any(c.islower() for c in pwd) and any(c.isupper() for c in pwd)
                   and any(c.isdigit() for c in pwd) and any(c in "!@#$%^&*" for c in pwd)
                   and len(pwd) >= 12):
            pwd = ''.join(random.choices(chars, k=16))
        master_var.set(pwd)
        audit_log.append("Master-Key generiert")
        check_strength()  # Stärke prüfen und anzeigen

    tk.Button(root, image=generate_img, command=generate_master, bd=0).pack(side="left", padx=6)

    # Anzeige, ob Master-Key stark genug ist
    frame = tk.Frame(root)
    frame.pack(pady=14)
    criteria = {
        "Groß- / Kleinschreibung": tk.Label(frame, text="❌"),
        "Zahl": tk.Label(frame, text="❌"),
        "Sonderzeichen": tk.Label(frame, text="❌"),
        "Mindestlänge (12)": tk.Label(frame, text="❌")
    }
    row = 0
    for text, label in criteria.items():
        tk.Label(frame, text=text).grid(row=row, column=0, sticky="w")
        label.grid(row=row, column=1, sticky="w", padx=10)
        row += 1

    proceed_btn = tk.Button(root, text="Weiter", state="disabled")
    proceed_btn.pack(pady=6)

    # Überprüft, ob Master-Key alle Bedingungen erfüllt
    def check_strength(*args):
        pwd = master_var.get()
        checks = {
            "Groß- / Kleinschreibung": any(c.islower() for c in pwd) and any(c.isupper() for c in pwd),
            "Zahl": any(c.isdigit() for c in pwd),
            "Sonderzeichen": any(c in "!@#$%^&*" for c in pwd),
            "Mindestlänge (12)": len(pwd) >= 12
        }
        for crit, ok in checks.items():
            criteria[crit].config(text="✔️" if ok else "❌")
        proceed_btn.config(state="normal" if all(checks.values()) else "disabled")

    master_var.trace("w", check_strength)

    # Weiter zum Hauptfenster
    def proceed():
        key = generate_key_from_master(master_var.get())  # Master-Key → Fernet-Key
        root.destroy()
        show_main_window(key)

    proceed_btn.config(command=proceed)
    root.mainloop()


# =====================================================================
# ACTIVITY TRACKER
# =====================================================================
def make_activity_tracker(main, on_timeout):
    # Trackt die letzte Aktivität des Nutzers
    last_activity = {"t": time.time()}

    def reset(event=None):
        last_activity["t"] = time.time()  # Zeit zurücksetzen bei Tastatur/Maus/Bewegung

    def check():
        # Prüfen, ob Timeout überschritten
        if time.time() - last_activity["t"] > app_settings["timeout_seconds"]:
            on_timeout()  # Auto-Logout
            return
        main.after(1000, check)  # jede Sekunde prüfen

    main.bind_all("<Any-KeyPress>", reset)
    main.bind_all("<Button>", reset)
    main.bind_all("<Motion>", reset)
    check()


# =====================================================================
# HAUPTFENSTER
# =====================================================================
def show_main_window(key):
    main = tk.Tk()
    main.title("Nova Security Passwortmanager")
    main.geometry("820x520")

    # Obere Leiste mit Audit-Log und Einstellungen
    top_frame = tk.Frame(main)
    top_frame.pack(fill="x", pady=6, padx=8)
    tk.Button(top_frame, text="Audit-Log", command=lambda: show_audit(main)).pack(side="left")
    try:
        settings_img = PhotoImage(file="settings.png").subsample(4, 4)
        tk.Button(top_frame, image=settings_img, command=lambda: open_settings(main), bd=0).pack(side="right")
    except:
        tk.Button(top_frame, text="⚙️", command=lambda: open_settings(main), bd=0).pack(side="right")

    # Suchfeld und Filter
    search_frame = tk.Frame(main)
    search_frame.pack(fill="x", padx=10, pady=6)
    search_var = tk.StringVar()
    filter_var = tk.StringVar(value="")
    tk.Label(search_frame, text="Suche:").pack(side="left")
    search_entry = tk.Entry(search_frame, textvariable=search_var)
    search_entry.pack(side="left", fill="x", expand=True, padx=(5, 5))
    filter_options = ["", "Titel", "Name", "Älteste", "Neueste"]
    ttk.OptionMenu(search_frame, filter_var, "", *filter_options[1:]).pack(side="left")

    # Tabelle für gespeicherte Passwörter
    columns = ("Titel", "Name", "Passwort", "Notizen")
    tree = ttk.Treeview(main, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=180)
    tree.pack(fill="both", expand=True, pady=8, padx=8)

    # Tabelle aktualisieren
    def refresh(filter_text=""):
        for item in tree.get_children():
            tree.delete(item)
        items = list(data_store.items())
        if filter_var.get() == "Neueste":
            items = list(reversed(items))
        for title, info in items:
            if filter_var.get() == "Titel":
                if filter_text.lower() in title.lower():
                    tree.insert("", "end", values=(title, info["Name"], "******", info["Notizen"]))
            elif filter_var.get() == "Name":
                if filter_text.lower() in info["Name"].lower():
                    tree.insert("", "end", values=(title, info["Name"], "******", info["Notizen"]))
            else:
                if filter_text.lower() in title.lower() or filter_text.lower() in info["Name"].lower():
                    tree.insert("", "end", values=(title, info["Name"], "******", info["Notizen"]))

    refresh()
    search_var.trace("w", lambda *args: refresh(search_var.get()))
    filter_var.trace("w", lambda *args: refresh(search_var.get()))

    # Bilder für Buttons
    newpass_img = PhotoImage(file="plus.png").subsample(4, 4)
    eye_img = PhotoImage(file="eye.png").subsample(4, 4)
    generate_img = PhotoImage(file="generate.png").subsample(4, 4)

    # =====================================================================
    # NEUES PASSWORT
    # =====================================================================
    def add_password():
        win = tk.Toplevel(main)
        win.title("Neues Passwort")

        # Eingabefelder
        tk.Label(win, text="Titel").grid(row=0, column=0, padx=6, pady=6)
        tk.Label(win, text="Name").grid(row=1, column=0, padx=6, pady=6)
        tk.Label(win, text="Passwort").grid(row=2, column=0, padx=6, pady=6)
        tk.Label(win, text="Notizen").grid(row=3, column=0, padx=6, pady=6)

        title_var = tk.StringVar()
        name_var = tk.StringVar()
        pwd_var = tk.StringVar()
        tk.Entry(win, textvariable=title_var).grid(row=0, column=1, padx=6, pady=6)
        tk.Entry(win, textvariable=name_var).grid(row=1, column=1, padx=6, pady=6)
        pwd_entry = tk.Entry(win, textvariable=pwd_var, show="*")
        pwd_entry.grid(row=2, column=1, padx=6, pady=6)

        # Passwort ein-/ausblenden
        def toggle():
            pwd_entry.config(show="" if pwd_entry.cget("show") == "*" else "*")
        tk.Button(win, image=eye_img, command=toggle, bd=0).grid(row=2, column=2, padx=5)

        # Passwort automatisch generieren
        def gen():
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            pwd = ''.join(random.choices(chars, k=12))
            while not (any(c.islower() for c in pwd) and any(c.isupper() for c in pwd)
                       and any(c.isdigit() for c in pwd) and any(c in "!@#$%^&*" for c in pwd)
                       and len(pwd) >= 12):
                pwd = ''.join(random.choices(chars, k=12))
            pwd_var.set(pwd)
        tk.Button(win, image=generate_img, command=gen, bd=0).grid(row=2, column=3, padx=5)

        # Notizenfeld
        notes = tk.Text(win, width=40, height=5)
        notes.grid(row=3, column=1, padx=6, pady=6)

        # Passwort speichern
        def save_pw():
            title = title_var.get().strip()
            text = notes.get("1.0", "end-1c").strip()
            if not title or not pwd_var.get():
                messagebox.showerror("Fehler", "Titel und Passwort müssen ausgefüllt sein!")
                return
            enc = save_password(title, pwd_var.get(), key)  # Verschlüsseln
            data_store[title] = {"Name": name_var.get(), "Passwort": enc, "Notizen": text}
            audit_log.append(f"Passwort '{title}' hinzugefügt")
            refresh(search_var.get())
            win.destroy()
        tk.Button(win, image=newpass_img, command=save_pw, bd=0).grid(row=4, column=1, columnspan=2, pady=10)

    tk.Button(main, image=newpass_img, command=add_password, bd=0).pack(pady=6)

    # =====================================================================
    # PASSWORT BEARBEITEN
    # =====================================================================
    def open_edit(title, info, plain):
        win = tk.Toplevel(main)
        win.title(f"Bearbeite: {title}")

        tk.Label(win, text="Titel").grid(row=0, column=0, padx=6, pady=6)
        tk.Label(win, text="Name").grid(row=1, column=0, padx=6, pady=6)
        tk.Label(win, text="Passwort").grid(row=2, column=0, padx=6, pady=6)
        tk.Label(win, text="Notizen").grid(row=3, column=0, padx=6, pady=6)

        title_var = tk.StringVar(value=title)
        name_var = tk.StringVar(value=info["Name"])
        pwd_var = tk.StringVar(value=plain)
        tk.Entry(win, textvariable=title_var).grid(row=0, column=1, padx=6, pady=6)
        tk.Entry(win, textvariable=name_var).grid(row=1, column=1, padx=6, pady=6)
        pwd_entry = tk.Entry(win, textvariable=pwd_var, show="*")
        pwd_entry.grid(row=2, column=1, padx=6, pady=6)

        # Passwort ein-/ausblenden (temporär 10 Sekunden sichtbar)
        def toggle():
            if pwd_entry.cget("show") == "*":
                pwd_entry.config(show="")
                win.after(10000, lambda: pwd_entry.config(show="*") if win.winfo_exists() else None)
            else:
                pwd_entry.config(show="*")
        tk.Button(win, image=eye_img, command=toggle, bd=0).grid(row=2, column=2, padx=5)

        notes = tk.Text(win, width=40, height=5)
        notes.insert("1.0", info["Notizen"])
        notes.grid(row=3, column=1, padx=6, pady=6)

        # Änderungen speichern
        def save_edit():
            new_title = title_var.get().strip()
            text = notes.get("1.0", "end-1c").strip()
            if not new_title or not pwd_var.get():
                messagebox.showerror("Fehler", "Titel und Passwort müssen ausgefüllt sein!")
                return
            enc = save_password(new_title, pwd_var.get(), key)
            if new_title != title:
                del data_store[title]
            data_store[new_title] = {"Name": name_var.get(), "Passwort": enc, "Notizen": text}
            audit_log.append(f"Passwort '{title}' bearbeitet → '{new_title}'")
            refresh(search_var.get())
            win.destroy()

        tk.Button(win, image=newpass_img, command=save_edit, bd=0).grid(row=4, column=1, columnspan=2, pady=10)

    # Doppelklick auf Tabelle → bearbeiten
    def edit_item(event):
        sel = tree.selection()
        if not sel:
            return
        title = tree.item(sel[0])["values"][0]
        info = data_store[title]
        try:
            plain = decrypt_password(key, info["Passwort"].encode())
        except:
            plain = ""
        open_edit(title, info, plain)
    tree.bind("<Double-1>", edit_item)

    # Rechtsklick-Menü zum Löschen
    def menu_open(event):
        sel = tree.selection()
        if not sel:
            return
        title = tree.item(sel[0])["values"][0]
        menu = tk.Menu(main, tearoff=0)

        def delete_item():
            if messagebox.askyesno("Löschen", f"'{title}' wirklich löschen?"):
                del data_store[title]
                audit_log.append(f"Passwort '{title}' gelöscht")
                refresh(search_var.get())

        menu.add_command(label="Löschen", command=delete_item)
        menu.post(event.x_root, event.y_root)

    tree.bind("<Button-3>", menu_open)

    # Timeout / Auto-Logout
    def on_timeout():
        try:
            messagebox.showinfo("Timeout", "Inaktivität erkannt – bitte erneut einloggen.")
            main.destroy()
        finally:
            start_app()

    make_activity_tracker(main, on_timeout)
    main.mainloop()


# =====================================================================
# SETTINGS (Timeout)
# =====================================================================
def open_settings(parent):
    win = tk.Toplevel(parent)
    win.title("Einstellungen")
    win.geometry("360x200")

    tk.Label(win, text="Auto-Logout Timeout", font=("Arial", 10)).pack(pady=15)

    slider_var = tk.IntVar(value=app_settings["timeout_seconds"])

    slider = tk.Scale(
        win,
        from_=30,
        to=600,
        orient="horizontal",
        resolution=30,
        variable=slider_var,
        length=260,
        showvalue=False
    )
    slider.pack(pady=10)

    # Farbige Anzeige abhängig von Timeout (Ampel-Farben)
    def pastel_gradient(val):
        v = int(val)
        percent = (v - 30) / (600 - 30)
        if percent < 0.5:
            r = int(200 + percent * 100)
            g = int(255)
            b = int(150)
        else:
            r = int(255)
            g = int(255 - (percent - 0.5) * 150)
            b = int(150)
        return f"#{r:02x}{g:02x}{b:02x}"

    # Text unter Slider
    def format_time(val):
        val = int(float(val))
        if val <= 60:
            return f"{val} Sekunden"
        else:
            minutes = ((val - 30) // 60) + 1
            return f"{minutes} Minuten"

    val_lbl = tk.Label(win, text=format_time(slider_var.get()), font=("Arial", 10))
    val_lbl.pack(pady=6)

    def on_slide(val):
        val_lbl.config(text=format_time(val))
        slider.config(bg=pastel_gradient(float(val)))

    slider.config(command=on_slide)
    slider.config(bg=pastel_gradient(slider_var.get()))

    # Buttons
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    def save_settings():
        app_settings["timeout_seconds"] = int(slider_var.get())
        win.destroy()
        messagebox.showinfo("Gespeichert",
                            f"Timeout wurde gesetzt auf: {format_time(app_settings['timeout_seconds'])}")

    tk.Button(btn_frame, text="Speichern", width=10, command=save_settings).grid(row=0, column=0, padx=10)
    tk.Button(btn_frame, text="Abbrechen", width=10, command=win.destroy).grid(row=0, column=1, padx=10)


# =====================================================================
# AUDIT LOG
# =====================================================================
def show_audit(parent):
    win = tk.Toplevel(parent)
    win.title("Audit-Log")
    listbox = tk.Listbox(win, width=120, height=20)
    listbox.pack(padx=10, pady=10)
    for entry in audit_log[-200:]:  # Zeigt die letzten 200 Aktionen
        listbox.insert("end", entry)
