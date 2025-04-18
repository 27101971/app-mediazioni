# app.py
import dash
import dash_bootstrap_components as dbc
from flask import send_from_directory, abort
import os
import shutil
import traceback
from pathlib import Path

# Importa configurazioni e utilities
import config
from utils.helpers import open_browser, load_users, REPORTLAB_AVAILABLE, WERKZEUG_AVAILABLE
# --- MODIFICA QUI ---
# Importa initialize_data_handling e save_requests
from utils.data_manager import initialize_data_handling, save_requests
# --- FINE MODIFICA ---

# Importa e registra i callback
from callbacks import auth_callbacks, main_callbacks, form_callbacks, modal_callbacks, mediator_callbacks
# Importa il layout DOPO aver definito app
from components.layouts import main_layout

# --- Controllo Dipendenze Critiche (Stampa Info) ---
if not REPORTLAB_AVAILABLE:
    print("WARNING: ReportLab non trovato. Funzionalità PDF disabilitate.")

# --- Inizializza gestione dati ---
# --- MODIFICA QUI ---
# Salva il path del file dati restituito dalla funzione
actual_data_file, using_external_data_manager = initialize_data_handling()
if actual_data_file is None:
    print("ERRORE CRITICO: Impossibile determinare il percorso del file dati!")
    sys.exit(1) # Esci se non possiamo determinare il file dati
# --- FINE MODIFICA ---


# --- Initialize Dash App ---
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    assets_folder=config.ASSETS_DIR.name
)
server = app.server
app.title = config.APP_TITLE

# --- Definisci il Layout ---
app.layout = main_layout()

# --- Registra i Callback ---
auth_callbacks.register_auth_callbacks(app)
main_callbacks.register_main_callbacks(app)
form_callbacks.register_form_callbacks(app)
modal_callbacks.register_modal_callbacks(app)
mediator_callbacks.register_mediator_callbacks(app)

# --- Flask Route per PDF ---
@server.route('/download/<path:filepath>')
def download_pdf(filepath):
    print(f"DEBUG PDF serve: '{filepath}'")
    safe_dir = config.PDF_SAVE_DIR_BASE.resolve()
    if '..' in filepath or filepath.startswith('/'): abort(404)
    try:
        rel = Path(filepath.replace('\\','/').strip('/'))
        full_path = (safe_dir / rel).resolve()
    except Exception as e: print(f"ERRORE risoluzione path PDF '{filepath}': {e}"); abort(500)
    try: is_safe = full_path.is_relative_to(safe_dir)
    except ValueError: is_safe = False
    if not is_safe: print(f"Forbidden PDF path attempt (outside base dir): {full_path}"); abort(403)
    if not full_path.is_file(): print(f"File PDF non trovato: {full_path}"); abort(404)
    try:
        return send_from_directory(str(full_path.parent), full_path.name, as_attachment=False)
    except Exception as send_err: print(f"ERRORE send_from_directory '{full_path.name}': {send_err}"); abort(500)


# --- Blocco Esecuzione Principale ---
if __name__ == "__main__":
    print("\n" + "="*60 + "\n--- AVVIO GESTIONE MEDIAZIONI ---\n" + "="*60)

    # --- Setup Iniziale ---
    print("\n--- Setup Iniziale ---")
    config.ASSETS_DIR.mkdir(exist_ok=True)
    print(f"Assets dir ('{config.ASSETS_DIR}') checked.")

    logo_asset_path = config.ASSETS_DIR / config.LOGO_FILENAME
    logo_root_path = config.BASE_DIR / config.LOGO_FILENAME
    if logo_root_path.exists():
        needs_copy = not logo_asset_path.exists() or logo_root_path.stat().st_mtime > logo_asset_path.stat().st_mtime
        if needs_copy:
            try:
                shutil.copy2(logo_root_path, logo_asset_path)
                print(f"INFO: Copiato/Aggiornato logo in '{config.ASSETS_DIR}'.")
            except Exception as e:
                print(f"ERRORE copia logo: {e}")
        else:
            print(f"INFO: Logo '{config.LOGO_FILENAME}' già presente e aggiornato in '{config.ASSETS_DIR}'.")
    else:
        print(f"ATTENZIONE: Logo '{logo_root_path}' non trovato.")

    config.PDF_SAVE_DIR_BASE.mkdir(parents=True, exist_ok=True)
    print(f"PDF dir ('{config.PDF_SAVE_DIR_BASE}') checked.")

    # --- Verifica File Dati e Utenti ---
    print("\n--- Verifica File Dati e Utenti ---")
    try:
        if not actual_data_file.exists():
            print(f"ATTENZIONE: File dati '{actual_data_file}' non trovato. Verrà creato al primo salvataggio.")
        else:
            print(f"File dati '{actual_data_file}' trovato.")

        if not config.MEDIATORS_FILE.exists():
            print(f"ATTENZIONE: File mediatori '{config.MEDIATORS_FILE}' non trovato. Creo file vuoto.")
            try:
                from utils.data_manager import save_mediators
                save_mediators([])
            except Exception as e_med_save:
                print(f"ERRORE creazione file mediatori: {e_med_save}")
        else:
            print(f"File mediatori '{config.MEDIATORS_FILE}' trovato.")

        if not config.USERS_FILE.exists():
            print(f"ATTENZIONE: File utenti '{config.USERS_FILE}' non trovato! Esegui 'python manage_users.py'.")
        else:
            print(f"File utenti '{config.USERS_FILE}' trovato. Carico...")
            users = load_users()
            if users:
                print(f"-> Utenti caricati: {len(users)}.")
            else:
                print("-> ATTENZIONE: Nessun utente valido caricato.")
    except Exception as e:
        print(f"ERRORE verifica file: {e}")
        sys.exit(1)

    # --- Avvio Server ---
    print("\n--- Info Avvio ---")
    print(f"Versione: {config.APP_VERSION}")
    print(f"Hashing Password: {'Werkzeug (Sicuro)' if WERKZEUG_AVAILABLE else 'Fallback (INSICURO!)'}")
    print(f"Generazione PDF: {'Abilitata (ReportLab trovato)' if REPORTLAB_AVAILABLE else 'DISABILITATA (ReportLab non trovato)'}")
    print(f"Gestione Dati: {'Esterna (gestore_dati.py)' if using_external_data_manager else 'Interna (Fallback)'}")
    print(f"File Dati: {actual_data_file.resolve()}")
    print(f"File Utenti: {config.USERS_FILE.resolve()}")
    print(f"File Mediatori: {config.MEDIATORS_FILE.resolve()}")
    print(f"Cartella PDF: {config.PDF_SAVE_DIR_BASE.resolve()}")

    print("\n" + "="*60 + "\n--- Avvio Server Dash ---")

    # 🚀 IMPOSTAZIONE PER RENDER
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)


    app.run( host=config.DEFAULT_HOST, port=config.DEFAULT_PORT, debug=debug_mode, dev_tools_ui=False, dev_tools_props_check=False )