# manage_users.py
import json
import sys
from pathlib import Path
import getpass  # Per nascondere l'input della password

# Importa librerie per UI migliorata
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt

# Importa configurazioni e helpers
try:
    import config
    from utils.helpers import WERKZEUG_AVAILABLE, generate_password_hash, check_password_hash, load_users
except ImportError as e:
    print(f"Errore: Impossibile importare moduli necessari ({e}).")
    print("Assicurati che config.py e utils/helpers.py esistano e siano accessibili.")
    sys.exit(1)

# Inizializza console Rich
console = Console()

# --- Funzioni Helper Specifiche per questo Script ---

def save_users(users_dict):
    """Salva il dizionario utenti nel file JSON specificato in config."""
    try:
        # Ordina per username prima di salvare per leggibilità
        sorted_users = dict(sorted(users_dict.items()))
        with open(config.USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted_users, f, indent=4, ensure_ascii=False)
        return True
    except IOError as e:
        console.print(f"[bold red]Errore durante il salvataggio del file utenti {config.USERS_FILE}: {e}[/]")
        return False
    except Exception as e:
        console.print(f"[bold red]Errore imprevisto durante il salvataggio: {e}[/]")
        return False

def get_password_from_user(prompt_message="Inserisci password: "):
    """Chiede la password due volte e verifica che coincidano."""
    while True:
        try:
            password = getpass.getpass(prompt_message)
            if not password:
                console.print("[yellow]La password non può essere vuota.[/]")
                continue
            password_confirm = getpass.getpass("Conferma password: ")
            if password == password_confirm:
                return password
            else:
                console.print("[bold red]Le password non coincidono. Riprova.[/]")
        except EOFError: # Gestisce interruzione input (es. Ctrl+D)
             console.print("\n[yellow]Input interrotto.[/]")
             return None
        except KeyboardInterrupt: # Gestisce Ctrl+C
             console.print("\n[yellow]Operazione annullata dall'utente.[/]")
             return None


# --- Funzioni Principali del Manager ---

def add_user():
    """Aggiunge un nuovo utente (Admin o Utente)."""
    console.print(Panel("[bold cyan]Aggiungi Nuovo Utente[/]", expand=False))
    users = load_users()

    while True:
        username = Prompt.ask("Username").strip()
        if not username:
            console.print("[yellow]Username non può essere vuoto.[/]")
            continue
        if username in users:
            console.print(f"[yellow]Username '{username}' esiste già.[/]")
        else:
            break # Username valido e non esistente

    level = IntPrompt.ask("Livello utente", choices=["1", "2"], default=1, show_default=True)

    # Chiede il nome reparto, default all'username
    nome_reparto_default = username
    nome_reparto = Prompt.ask(f"Nome reparto/servizio (default: '{nome_reparto_default}')", default=nome_reparto_default).strip()
    if not nome_reparto: # Se l'utente preme invio senza scrivere nulla, usa il default
        nome_reparto = nome_reparto_default

    console.print(f"Inserisci la password per [cyan]{username}[/]")
    password = get_password_from_user()
    if password is None: # Operazione annullata
        return

    hashed_password = generate_password_hash(password)

    users[username] = {
        "hashed_password": hashed_password,
        "level": level,
        "nome_reparto": nome_reparto
    }

    if save_users(users):
        console.print(f"[bold green]Utente '{username}' (Livello {level}, Reparto '{nome_reparto}') aggiunto con successo![/]")
    else:
        console.print("[bold red]Errore durante il salvataggio dell'utente.[/]")


def list_users():
    """Mostra una tabella degli utenti esistenti."""
    console.print(Panel("[bold cyan]Elenco Utenti Registrati[/]", expand=False))
    users = load_users()

    if not users:
        console.print("[yellow]Nessun utente trovato.[/]")
        return

    table = Table(title="Utenti", show_header=True, header_style="bold magenta")
    table.add_column("Username", style="dim", width=20)
    table.add_column("Livello", justify="center")
    table.add_column("Reparto/Servizio")

    for username, data in users.items():
        level = str(data.get('level', '?'))
        reparto = data.get('nome_reparto', username) # Default a username se manca
        table.add_row(username, level, reparto)

    console.print(table)

def change_password():
    """Cambia la password di un utente esistente."""
    console.print(Panel("[bold cyan]Cambia Password Utente[/]", expand=False))
    users = load_users()
    if not users:
        console.print("[yellow]Nessun utente definito.[/]")
        return

    list_users() # Mostra lista per facilitare scelta
    username = Prompt.ask("\nUsername dell'utente da modificare").strip()

    if username not in users:
        console.print(f"[bold red]Errore: Utente '{username}' non trovato.[/]")
        return

    console.print(f"Inserisci la NUOVA password per [cyan]{username}[/]")
    new_password = get_password_from_user("Nuova password: ")
    if new_password is None: # Operazione annullata
        return

    new_hashed_password = generate_password_hash(new_password)
    users[username]['hashed_password'] = new_hashed_password

    if save_users(users):
        console.print(f"[bold green]Password per l'utente '{username}' cambiata con successo![/]")
    else:
        console.print("[bold red]Errore durante il salvataggio della nuova password.[/]")

def delete_user():
    """Elimina un utente esistente."""
    console.print(Panel("[bold red]Elimina Utente[/]", expand=False))
    users = load_users()
    if not users:
        console.print("[yellow]Nessun utente definito.[/]")
        return

    list_users()
    username = Prompt.ask("\nUsername dell'utente da eliminare").strip()

    if username not in users:
        console.print(f"[bold red]Errore: Utente '{username}' non trovato.[/]")
        return

    if Confirm.ask(f"Sei [bold red]sicuro[/] di voler eliminare l'utente '{username}'? L'operazione è irreversibile.", default=False):
        del users[username]
        if save_users(users):
            console.print(f"[bold green]Utente '{username}' eliminato con successo![/]")
        else:
            console.print("[bold red]Errore durante il salvataggio dopo l'eliminazione.[/]")
    else:
        console.print("[yellow]Eliminazione annullata.[/]")


# --- Menu Principale ---

def show_menu():
    """Mostra il menu principale e gestisce la scelta dell'utente."""
    title = f"Gestione Utenti - {config.APP_TITLE}"
    console.print(Panel(title, style="bold blue", expand=False, title_align="center"))
    if not WERKZEUG_AVAILABLE:
         console.print(Panel("[bold yellow]ATTENZIONE: Libreria 'Werkzeug' non trovata. Le password NON saranno salvate in modo sicuro![/]", border_style="red"))

    while True:
        console.print("\n[bold]Menu:[/]")
        console.print("  [1] Aggiungi utente")
        console.print("  [2] Elenca utenti")
        console.print("  [3] Cambia password utente")
        console.print("  [4] Elimina utente")
        console.print("  [0] Esci")

        choice = Prompt.ask("Scegli un'opzione", choices=["1", "2", "3", "4", "0"], default="0")

        if choice == '1':
            add_user()
        elif choice == '2':
            list_users()
        elif choice == '3':
            change_password()
        elif choice == '4':
            delete_user()
        elif choice == '0':
            console.print("[bold blue]Arrivederci![/]")
            break
        else:
            console.print("[red]Scelta non valida.[/]")

# --- Blocco Esecuzione ---
if __name__ == "__main__":
    # Verifica esistenza file utenti e crea se necessario?
    # load_users() gestisce già il file non trovato, ma potremmo volerlo creare vuoto.
    if not config.USERS_FILE.exists():
        console.print(f"[yellow]File utenti '{config.USERS_FILE}' non trovato. Verrà creato se aggiungi un utente.[/]")
        # Oppure crea un file vuoto subito:
        # console.print(f"Creazione file utenti vuoto: '{config.USERS_FILE}'")
        # save_users({})

    show_menu()
    sys.exit(0)