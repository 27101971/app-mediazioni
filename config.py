# config.py
from pathlib import Path

# --- Path ---
BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
DATA_FILE_FALLBACK = BASE_DIR / "mediation_data.json"
# --- NUOVO FILE MEDIATORI ---
MEDIATORS_FILE = BASE_DIR / "mediators.json"
# ---
PDF_SAVE_DIR_BASE = BASE_DIR / "mediazioni_pdf"
ASSETS_DIR = BASE_DIR / "assets"
LOGO_FILENAME = "logo.png"
LOGO_PATH = ASSETS_DIR / LOGO_FILENAME

# --- App Settings ---
APP_TITLE = "Mediazioni Culturali"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8050
APP_VERSION = "2.6.0 Mediators" # Aggiorna versione

# --- Web Assets ---
LOGO_WEB_PATH = f"/{ASSETS_DIR.name}/{LOGO_FILENAME}"
LOGO_WIDTH_WEB = "150px"
LOGO_HEIGHT_WEB = "auto"

# --- PDF Settings ---
LOGO_WIDTH_CM = 3.5
LOGO_HEIGHT_CM = 2

# --- Form Defaults ---
DEFAULT_FORM_TITLE = "1. Nuova Richiesta"
DEFAULT_FORM_SUBTITLE = "Inserisci i dettagli della nuova richiesta."
DEFAULT_SAVE_BUTTON_TEXT = "Salva Richiesta e Genera PDF"
DEFAULT_INDIRIZZO_SERVIZIO = "Ospedale San Donato"

# --- Status Strings ---
STATUS_RICEVUTA = "Ricevuta"
STATUS_DA_CONFERMARE = "Da Confermare"
STATUS_CONFERMATA = "Confermata"
STATUS_ASSEGNATA = "Assegnata"
STATUS_PERCORSI = "Percorsi"
STATUS_ESEGUITA = "Eseguita"
STATUS_ANNULLATA = "Annullata"
VALID_STATUSES = [ STATUS_RICEVUTA, STATUS_DA_CONFERMARE, STATUS_CONFERMATA, STATUS_ASSEGNATA, STATUS_PERCORSI, STATUS_ESEGUITA, STATUS_ANNULLATA ]

# --- Change Request Status ---
CHANGE_REQ_PENDING = "pending"
CHANGE_REQ_CLEARED = "cleared"

# --- Status Colors (per Badge) ---
STATUS_COLORS = {
    STATUS_RICEVUTA: "secondary", STATUS_DA_CONFERMARE: "info", STATUS_CONFERMATA: "primary",
    STATUS_ASSEGNATA: "warning", STATUS_PERCORSI: "info", STATUS_ESEGUITA: "success",
    STATUS_ANNULLATA: "danger",
}

# --- Opzioni Mediatore ---
MEDIATOR_SPECIAL_OPTION = "Percorsi"
# DEFAULT_MEDIATORS non più necessario qui, verrà caricato da file
# MEDIATOR_OPTIONS non più definito qui come costante globale