# manage_users_gui.py
import customtkinter as ctk
import json
import sys
from tkinter import messagebox  # Per messaggi di popup standard

# Importa configurazioni e helpers
try:
    import config
    from utils.helpers import WERKZEUG_AVAILABLE, generate_password_hash, check_password_hash, load_users
except ImportError as e:
    print(f"Errore: Impossibile importare moduli necessari ({e}).")
    print("Assicurati che config.py e utils/helpers.py esistano e siano accessibili.")
    # Mostra un popup di errore se Tkinter è disponibile
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw() # Nascondi finestra principale Tkinter
        messagebox.showerror("Errore Importazione Moduli", f"Impossibile avviare gestione utenti:\n{e}\n\nControlla la console.")
        root.destroy()
    except ImportError:
        pass # Non possiamo mostrare popup se Tkinter manca
    sys.exit(1)

# --- Tema CustomTkinter ---
ctk.set_appearance_mode("System")  # System, Dark, Light
ctk.set_default_color_theme("blue") # blue, green, dark-blue

# --- Funzione Salva Utenti (uguale a prima ma usa messagebox per errori) ---
def save_users(users_dict):
    """Salva il dizionario utenti nel file JSON."""
    try:
        sorted_users = dict(sorted(users_dict.items()))
        with open(config.USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted_users, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        messagebox.showerror("Errore Salvataggio", f"Impossibile salvare il file utenti:\n{e}")
        return False

# --- Classe Principale dell'Applicazione GUI ---
class UserManagementApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"Gestione Utenti - {config.APP_TITLE}")
        self.geometry("600x550") # Dimensioni finestra

        self.users_data = load_users() # Carica utenti all'avvio

        # Configura griglia layout (1 colonna, 3 righe principali)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Riga Aggiungi/Modifica
        self.grid_rowconfigure(1, weight=1) # Riga Lista Utenti
        self.grid_rowconfigure(2, weight=0) # Riga Feedback/Status

        # --- Frame Superiore: Aggiungi/Modifica Utente ---
        self.form_frame = ctk.CTkFrame(self, corner_radius=10)
        self.form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.form_frame.grid_columnconfigure((1, 3), weight=1) # Colonne per input

        # Etichette e Campi Input
        ctk.CTkLabel(self.form_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.username_entry = ctk.CTkEntry(self.form_frame, placeholder_text="username")
        self.username_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self.form_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.password_entry = ctk.CTkEntry(self.form_frame, placeholder_text="lascia vuoto per non cambiare", show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self.form_frame, text="Livello:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.level_var = ctk.StringVar(value="1") # Default a Livello 1
        self.level_menu = ctk.CTkOptionMenu(self.form_frame, variable=self.level_var, values=["1", "2"])
        self.level_menu.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(self.form_frame, text="Reparto:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.reparto_entry = ctk.CTkEntry(self.form_frame, placeholder_text="nome reparto/servizio")
        self.reparto_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # Bottoni Azione Form
        self.add_button = ctk.CTkButton(self.form_frame, text="Aggiungi/Modifica Utente", command=self.add_or_update_user)
        self.add_button.grid(row=2, column=0, columnspan=4, padx=5, pady=10)
        self.clear_button = ctk.CTkButton(self.form_frame, text="Pulisci Campi", command=self.clear_form, fg_color="grey")
        self.clear_button.grid(row=3, column=0, columnspan=4, padx=5, pady=5)


        # --- Frame Centrale: Lista Utenti ---
        self.list_frame = ctk.CTkFrame(self, corner_radius=0)
        self.list_frame.grid(row=1, column=0, padx=10, pady=0, sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.list_frame.grid_rowconfigure(0, weight=1)

        self.user_listbox = ctk.CTkScrollableFrame(self.list_frame, label_text="Utenti Registrati")
        self.user_listbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.user_listbox.grid_columnconfigure(0, weight=1) # Configura colonna interna

        # --- Frame Inferiore: Status Bar ---
        self.status_label = ctk.CTkLabel(self, text="Pronto.", anchor="w")
        self.status_label.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        # Popola lista iniziale
        self.refresh_user_list()

        # Mostra warning se Werkzeug non è disponibile
        if not WERKZEUG_AVAILABLE:
             self.status_label.configure(text="ATTENZIONE: Werkzeug non trovato! Password non sicure.", text_color="orange")
             messagebox.showwarning("Sicurezza Password", "La libreria 'Werkzeug' non è installata.\nLe password NON verranno salvate in modo sicuro!")

    def refresh_user_list(self):
        """Pulisce e ripopola la lista utenti nella GUI."""
        # Pulisci la lista precedente
        for widget in self.user_listbox.winfo_children():
            widget.destroy()

        self.users_data = load_users() # Ricarica i dati
        if not self.users_data:
             ctk.CTkLabel(self.user_listbox, text="Nessun utente definito.").grid(row=0, column=0, padx=5, pady=5)
             return

        # Aggiungi righe per ogni utente
        row_index = 0
        for username, data in self.users_data.items():
            level = data.get('level', '?')
            reparto = data.get('nome_reparto', username)
            user_info = f"{username} (Liv: {level}, Rep: {reparto})"

            # Frame per la riga utente
            row_frame = ctk.CTkFrame(self.user_listbox, fg_color="transparent")
            row_frame.grid(row=row_index, column=0, pady=(0, 2), sticky="ew")
            row_frame.grid_columnconfigure(0, weight=1) # Label occupa spazio

            # Label con info utente
            label = ctk.CTkLabel(row_frame, text=user_info, anchor="w")
            label.grid(row=0, column=0, padx=5, sticky="ew")
            # Associa evento click alla label per popolare il form
            label.bind("<Button-1>", lambda event, u=username, d=data: self.populate_form(u, d))
            label.bind("<Enter>", lambda event, l=label: l.configure(font=ctk.CTkFont(weight="bold"))) # Evidenzia al passaggio del mouse
            label.bind("<Leave>", lambda event, l=label: l.configure(font=ctk.CTkFont()))

            # Bottone Elimina
            delete_button = ctk.CTkButton(
                row_frame, text="Elimina", width=60, fg_color="red", hover_color="darkred",
                command=lambda u=username: self.delete_user_confirm(u)
            )
            delete_button.grid(row=0, column=1, padx=5)

            row_index += 1

    def populate_form(self, username, data):
        """Popola i campi del form con i dati dell'utente selezionato."""
        self.clear_form(clear_status=False) # Pulisci prima
        self.username_entry.insert(0, username)
        self.level_var.set(str(data.get('level', '1'))) # Imposta il menu a tendina
        self.reparto_entry.insert(0, data.get('nome_reparto', username))
        self.password_entry.configure(placeholder_text="Lascia vuoto per non cambiare")
        self.username_entry.configure(state="disabled") # Non permettere modifica username
        self.status_label.configure(text=f"Modifica dati per: {username}")

    def clear_form(self, clear_status=True):
        """Pulisce i campi del form."""
        self.username_entry.configure(state="normal") # Riabilita modifica username
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.password_entry.configure(placeholder_text="Inserire password")
        self.level_var.set("1")
        self.reparto_entry.delete(0, "end")
        if clear_status:
            self.status_label.configure(text="Pronto.")

    def add_or_update_user(self):
        """Aggiunge un nuovo utente o aggiorna uno esistente."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get() # Non fare strip della password!
        level = int(self.level_var.get())
        reparto = self.reparto_entry.get().strip()
        if not reparto: # Usa username come default se vuoto
            reparto = username

        if not username:
            messagebox.showerror("Errore", "Username obbligatorio.")
            return

        is_update = username in self.users_data

        if is_update: # Aggiornamento
            # Password opzionale per aggiornamento
            if password:
                if not self.confirm_password(password): return # Chiedi conferma solo se inserita
                hashed_password = generate_password_hash(password)
                self.users_data[username]['hashed_password'] = hashed_password
                pw_changed_msg = " Password aggiornata."
            else:
                 pw_changed_msg = " Password non modificata."

            self.users_data[username]['level'] = level
            self.users_data[username]['nome_reparto'] = reparto

            if save_users(self.users_data):
                messagebox.showinfo("Successo", f"Utente '{username}' aggiornato.{pw_changed_msg}")
                self.clear_form()
                self.refresh_user_list()
            else:
                messagebox.showerror("Errore", "Salvataggio fallito.")

        else: # Aggiunta nuovo utente
            if not password:
                messagebox.showerror("Errore", "Password obbligatoria per i nuovi utenti.")
                return

            if not self.confirm_password(password): return # Chiedi sempre conferma per nuovo utente

            hashed_password = generate_password_hash(password)
            self.users_data[username] = {
                "hashed_password": hashed_password,
                "level": level,
                "nome_reparto": reparto
            }
            if save_users(self.users_data):
                messagebox.showinfo("Successo", f"Utente '{username}' aggiunto.")
                self.clear_form()
                self.refresh_user_list()
            else:
                # Rimuovi utente aggiunto in memoria se salvataggio fallisce
                if username in self.users_data: del self.users_data[username]
                messagebox.showerror("Errore", "Salvataggio fallito.")

    def confirm_password(self, first_password):
        """Chiede una seconda volta la password per conferma in un popup."""
        confirmed_password = ctk.CTkInputDialog(text="Conferma Password:", title="Conferma", entry_show_char="*").get_input()
        if confirmed_password == first_password:
            return True
        else:
            messagebox.showerror("Errore", "Le password non coincidono.")
            return False

    def delete_user_confirm(self, username):
        """Chiede conferma prima di eliminare l'utente."""
        if messagebox.askyesno("Conferma Eliminazione", f"Sei sicuro di voler eliminare l'utente '{username}'?\nL'operazione è irreversibile."):
            if username in self.users_data:
                del self.users_data[username]
                if save_users(self.users_data):
                    messagebox.showinfo("Successo", f"Utente '{username}' eliminato.")
                    self.refresh_user_list()
                    self.clear_form() # Pulisci form se l'utente eliminato era selezionato
                else:
                    # Ricarica i dati per annullare l'eliminazione in memoria
                    self.users_data = load_users()
                    messagebox.showerror("Errore", "Eliminazione fallita.")
            else:
                 messagebox.showerror("Errore", f"Utente '{username}' non trovato (potrebbe essere già stato eliminato).")
                 self.refresh_user_list() # Aggiorna la lista


# --- Avvio Applicazione GUI ---
if __name__ == "__main__":
    # Verifica file utenti e crea se necessario?
    if not config.USERS_FILE.exists():
         if messagebox.askyesno("File Utenti Mancante", f"Il file '{config.USERS_FILE.name}' non esiste.\nVuoi crearlo ora (vuoto)?"):
             save_users({})
         else:
             print("Avvio annullato. File utenti necessario.")
             sys.exit(0)

    app = UserManagementApp()
    app.mainloop()