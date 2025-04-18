# manage_users.py
import json
from werkzeug.security import generate_password_hash, check_password_hash
import getpass
from pathlib import Path

# --- Costanti ---
USERS_FILE = Path("users.json")
ADMIN_USERNAME_DEFAULT = "admin" # Nome utente predefinito per l'amministratore

# --- Funzioni Helper ---

def load_users():
    """Carica gli utenti dal file JSON in modo sicuro."""
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
            if not isinstance(users, dict):
                 print(f"ERRORE: Il contenuto di '{USERS_FILE}' non è un dizionario JSON valido.")
                 return {}
            # Verifica opzionale della struttura interna (es. presenza chiavi)
            # for uname, udata in users.items():
            #    if not all(k in udata for k in ('hashed_password', 'level', 'nome_reparto')):
            #       print(f"ATTENZIONE: Dati incompleti per l'utente '{uname}' in '{USERS_FILE}'.")
            return users
    except json.JSONDecodeError:
        print(f"ERRORE: Impossibile decodificare JSON da '{USERS_FILE}'.")
        return {}
    except Exception as e:
        print(f"Errore imprevisto durante il caricamento degli utenti da '{USERS_FILE}': {e}")
        return {}

def save_users(users):
    """Salva il dizionario utenti nel file JSON."""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
        # print(f"INFO: File utenti '{USERS_FILE}' salvato.") # Log opzionale
    except Exception as e:
        print(f"ERRORE durante il salvataggio degli utenti in '{USERS_FILE}': {e}")

def set_password(username):
    """Chiede e conferma una password in modo sicuro, restituendo l'hash."""
    while True:
        password = getpass.getpass(f"Inserisci la NUOVA password per '{username}': ")
        if not password:
            print("La password non può essere vuota. Riprova.")
            continue
        password_confirm = getpass.getpass("Conferma la password: ")
        if password == password_confirm:
            print("Password impostata con successo.")
            return generate_password_hash(password)
        else:
            print("Le password non coincidono. Riprova.")

def add_or_update_user(username, level, nome_reparto=None, force_password_update=False):
    """
    Aggiunge un nuovo utente o aggiorna uno esistente.
    Chiede la password se l'utente è nuovo o se force_password_update è True.
    """
    users = load_users()
    user_exists = username in users
    hashed_password = None # Inizializza

    # Determina se chiedere la password
    ask_for_password = not user_exists or force_password_update

    if ask_for_password:
        print(f"\n{'Aggiornamento' if user_exists and force_password_update else 'Impostazione'} password per '{username}'...")
        hashed_password = set_password(username) # Richiede input password
    elif user_exists: # Utente esiste, NON forziamo cambio password
        hashed_password = users[username]['hashed_password'] # Mantiene la vecchia password
        print(f"\nPassword per '{username}' non modificata (era già impostata).")

    # Se per qualche motivo hashed_password è ancora None, esci
    if hashed_password is None:
        print(f"ERRORE INTERNO: Impossibile determinare la password per '{username}'. Operazione annullata.")
        return

    # Determina il nome reparto finale
    # Se fornito, usa quello. Altrimenti, se utente esiste, usa il vecchio. Se nuovo, usa username.
    final_nome_reparto = nome_reparto if nome_reparto else users.get(username, {}).get('nome_reparto', username)

    # Aggiorna/Crea i dati dell'utente
    users[username] = {
        "hashed_password": hashed_password,
        "level": level,
        "nome_reparto": final_nome_reparto
    }
    save_users(users)
    action_msg = "aggiornato" if user_exists else "aggiunto"
    pw_msg = "(password impostata/aggiornata)" if ask_for_password else "(password non modificata)"
    print(f"Utente '{username}' (Livello {level}, Reparto: {users[username]['nome_reparto']}) {action_msg} con successo {pw_msg}.")

def delete_user(username_to_delete, admin_username_ref):
    """Elimina un utente (impedisce l'eliminazione dell'admin)."""
    if username_to_delete == admin_username_ref:
        print(f"ERRORE: L'utente amministratore '{admin_username_ref}' non può essere eliminato.")
        return

    users = load_users()
    if username_to_delete in users:
        del users[username_to_delete]
        save_users(users)
        print(f"Utente '{username_to_delete}' eliminato con successo.")
    else:
        print(f"Utente '{username_to_delete}' non trovato.")

def list_users():
     """Mostra un elenco degli utenti configurati."""
     users = load_users()
     if not users:
         print("\nNessun utente configurato.")
         return
     print("\n--- Utenti Configurati ---")
     for username, data in users.items():
         level_str = f"Livello: {data.get('level', 'N/D')}"
         reparto_str = f"Reparto: {data.get('nome_reparto', 'N/D')}"
         print(f"- {username:<15} ({level_str}, {reparto_str})") # Allineamento per leggibilità
     print("--------------------------")

# --- Esecuzione Principale dello Script ---
if __name__ == "__main__":
    print("--- Gestione Utenti Mediazioni Culturali ---")

    # --- Configurazione Admin ---
    current_admin_username = ADMIN_USERNAME_DEFAULT # Usa il default
    print(f"INFO: L'utente amministratore di riferimento è: '{current_admin_username}'")
    users_data = load_users()

    admin_needs_setup = False
    admin_record = users_data.get(current_admin_username)

    if not admin_record:
        print(f"\nATTENZIONE: Utente admin '{current_admin_username}' non trovato.")
        admin_needs_setup = True
    elif admin_record.get('level') != 2:
         print(f"\nATTENZIONE: Utente '{current_admin_username}' trovato, ma non ha Livello 2. Correggo...")
         admin_record['level'] = 2
         admin_record['nome_reparto'] = admin_record.get('nome_reparto', "Amministrazione") # Imposta reparto se manca
         save_users(users_data) # Salva la correzione
         print(f"Livello per '{current_admin_username}' impostato a 2.")
         # Non forziamo cambio password qui, l'utente può farlo dopo
    else:
        print(f"\nUtente admin '{current_admin_username}' (Livello 2) configurato correttamente.")

    if admin_needs_setup:
         print(f"\nÈ necessario creare l'utente admin '{current_admin_username}' e impostare la sua password.")
         add_or_update_user(current_admin_username, level=2, nome_reparto="Amministrazione", force_password_update=True)
         # Non serve ricaricare users_data qui, add_or_update salva già

    # --- Loop Gestione Interattiva ---
    print("\n--- Gestione Utenti Interattiva ---")
    while True:
        list_users() # Mostra utenti all'inizio di ogni ciclo
        action = input("Azioni: [a]ggiungi/aggiorna, [e]limina, [u]scire? ").lower().strip()

        if action == 'a':
            uname_input = input("Inserisci username da aggiungere/aggiornare: ").strip()
            if not uname_input:
                print("Username non valido.")
                continue

            current_users = load_users() # Ricarica stato attuale
            user_exists = uname_input in current_users
            existing_data = current_users.get(uname_input, {})
            is_target_admin = (uname_input == current_admin_username)

            # --- Determina Livello ---
            default_level = existing_data.get('level', 2 if is_target_admin else 1)
            level_input = input(f"Inserisci livello per '{uname_input}' (1=Reparto, 2=Admin) [default={default_level}]: ").strip()
            try:
                level_selected = int(level_input) if level_input else default_level
                if level_selected not in [1, 2]:
                    print("Livello non valido (deve essere 1 o 2). Riprova.")
                    continue
            except ValueError:
                print(f"Input livello non valido. Riprova.")
                continue

            # --- Determina Nome Reparto ---
            default_reparto = existing_data.get('nome_reparto', "Amministrazione" if is_target_admin else uname_input)
            reparto_input = input(f"Inserisci nome reparto per '{uname_input}' (opzionale, default='{default_reparto}'): ").strip()
            nome_reparto_selected = reparto_input or default_reparto

            # --- Gestione Password ---
            force_pw_update = False
            if not user_exists:
                # print(f"L'utente '{uname_input}' è nuovo. È necessario impostare la password.") # Già gestito in add_or_update_user
                force_pw_update = True # Password obbligatoria per nuovi utenti
            else: # Utente esistente
                change_pw = input(f"L'utente '{uname_input}' esiste già. Vuoi forzare un cambio password? [s/N]: ").lower().strip()
                if change_pw == 's':
                    force_pw_update = True

            # --- Chiama la funzione di aggiornamento ---
            add_or_update_user(uname_input, level_selected, nome_reparto_selected, force_password_update=force_pw_update)

        elif action == 'e':
            uname_to_delete = input("Inserisci username da eliminare: ").strip()
            if uname_to_delete:
                delete_user(uname_to_delete, current_admin_username) # Passa admin ref per controllo
            else:
                print("Username non valido.")

        elif action == 'u':
            print("Uscita dalla gestione utenti.")
            break
        else:
            print("Azione non riconosciuta. Opzioni: a, e, u.")