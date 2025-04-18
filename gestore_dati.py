# gestore_dati.py
import json
from pathlib import Path
import datetime
import config # Importa config per accedere a VALID_STATUSES etc.

DATA_FILE = "mediation_data.json" # Assicurati sia lo stesso path

# Rimuovi le definizioni delle costanti STATUS_* e VALID_STATUSES da qui
# Useremo quelle definite in config.py per coerenza
# STATUS_RICEVUTA = "Ricevuta"
# ... altre costanti STATUS_* ...
# VALID_STATUSES = [...]

def load_requests():
    file_path = Path(DATA_FILE)
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                 # Aggiungi qui eventuali controlli/pulizie sui dati letti se necessario
                 # Esempio: assicurare che tutti abbiano uno stato valido
                 # for req in data:
                 #     if isinstance(req, dict) and req.get('stato') not in config.VALID_STATUSES:
                 #          print(f"WARNING gestore_dati load: Stato non valido '{req.get('stato')}' per ID {req.get('id')}. Impostato a Ricevuta.")
                 #          req['stato'] = config.STATUS_RICEVUTA
                 return data
            else:
                print(f"WARNING in gestore_dati: Data in {DATA_FILE} is not a list.")
                return []
        except json.JSONDecodeError:
            print(f"ERROR in gestore_dati: Could not decode JSON from {DATA_FILE}.")
            return []
        except Exception as e:
            print(f"Error loading data from {DATA_FILE} in gestore_dati: {e}")
            return []
    return []

# --- MODIFICA QUI: Aggiunto force_save ---
def save_requests(data, force_save=False): # Aggiunto argomento opzionale
    """Salva i dati delle richieste su file JSON."""
    print(f"DEBUG gestore_dati save_requests: Chiamata con {len(data)} records. ForceSave={force_save}")
    if not isinstance(data, list):
        print(f"Save error in gestore_dati: Data provided is not a list ({type(data)})")
        return

    # Nota: il check 'richiedente_username' è ora gestito nel wrapper
    # o potrebbe essere fatto qui se si preferisce
    file_path = Path(DATA_FILE)
    try:
        # Assicura 'richiedente_username' qui se non usi il wrapper in data_manager
        updated_count = 0
        for req in data:
            if isinstance(req, dict) and 'richiedente_username' not in req:
                 print(f"INFO in gestore_dati (save): Adding 'richiedente_username: None' to ID {req.get('id', 'N/A')}")
                 req['richiedente_username'] = None
                 updated_count += 1
        # Qui potresti aggiungere logica per salvare solo se 'updated_count > 0 or force_save'
        # ma per ora, la logica è nel wrapper, quindi salviamo sempre se questa funzione viene chiamata.
        print(f"DEBUG gestore_dati save_requests: Procedo al salvataggio su {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"DEBUG gestore_dati save_requests: Salvataggio completato.")

    except Exception as e:
        print(f"Error saving data to {DATA_FILE} in gestore_dati: {e}")
# --- FINE MODIFICA ---

def get_next_id(requests):
    if not requests or not isinstance(requests, list): return 1
    try:
        # Filtra IDs validi prima di cercare il massimo
        ids = [int(r.get('id', 0)) for r in requests if isinstance(r, dict) and str(r.get('id', '0')).isdigit()]
        return max(ids) + 1 if ids else 1
    except ValueError as e:
        print(f"ID generation error (ValueError) in gestore_dati: {e}. Potrebbero esserci ID non numerici.")
        # Fallback più robusto se ci sono ID non numerici
        valid_ids = [int(r.get('id')) for r in requests if isinstance(r, dict) and isinstance(r.get('id'), int)]
        return max(valid_ids) + 1 if valid_ids else len(requests) + 1 # Usa lunghezza come ultima risorsa
    except Exception as e:
        print(f"ID generation error in gestore_dati: {e}")
        return len(requests) + 1