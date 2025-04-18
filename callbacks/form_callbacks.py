# callbacks/form_callbacks.py
import dash
from dash import Output, Input, State, html, no_update
import dash_bootstrap_components as dbc
import datetime
from pathlib import Path
# Importa funzioni dati, pdf, helpers e config
from utils.data_manager import load_requests, save_requests, get_next_id
from utils.helpers import generate_mediation_request_pdf, format_date_italian # Assicurati sia qui
import config

def register_form_callbacks(app):
    # Callback 6 (Placeholder - può essere rimosso o usato per reset)
    @app.callback(
        [Output("nr-data-richiesta", "date", allow_duplicate=True), Output("nr-servizio-richiedente", "value", allow_duplicate=True), Output("nr-indirizzo-servizio", "value", allow_duplicate=True), Output("nr-operatore-richiedente", "value", allow_duplicate=True), Output("nr-giorno-concordato", "date", allow_duplicate=True), Output("nr-orario-concordato", "value", allow_duplicate=True), Output("nr-lingua", "value", allow_duplicate=True), Output("nr-nazionalita", "value", allow_duplicate=True), Output("nr-eta", "value", allow_duplicate=True), Output("nr-sesso", "value", allow_duplicate=True), Output("nr-note", "value", allow_duplicate=True), Output("nr-form-title", "children", allow_duplicate=True), Output("nr-form-subtitle", "children"), Output("btn-salva-richiesta", "children", allow_duplicate=True), Output("nuova-richiesta-feedback", "children", allow_duplicate=True), Output("edit-request-id-store-local", "data", allow_duplicate=True)],
        Input("edit-request-id-store", "data"),
        State("login-status-store", "data"),
        prevent_initial_call=True
    )
    def populate_form_for_edit(edit_request_id_global, login_status):
        print(f"\n--- populate_form_for_edit --- Triggered with Global ID: {edit_request_id_global} (Callback is now mostly placeholder)")
        # Potrebbe resettare il form se edit_request_id_global diventa None
        if edit_request_id_global is None:
             print("populate_form_for_edit: Resetting form state via placeholder callback.")
             today=datetime.date.today().isoformat(); def_sub="Inserisci dettagli.";
             reset_vals = [today,"","Ospedale San Donato","",None,"","", "",None,"ND","", config.DEFAULT_FORM_TITLE, def_sub, config.DEFAULT_SAVE_BUTTON_TEXT, "", None]
             return reset_vals
        return [no_update] * 16

    # Callback 7 (Save Request)
    @app.callback(
        [Output("nuova-richiesta-feedback", "children", allow_duplicate=True), Output('refresh-signal-store', 'data', allow_duplicate=True), Output("edit-request-id-store", "data", allow_duplicate=True), Output("nr-data-richiesta", "date", allow_duplicate=True), Output("nr-servizio-richiedente", "value", allow_duplicate=True), Output("nr-indirizzo-servizio", "value", allow_duplicate=True), Output("nr-operatore-richiedente", "value", allow_duplicate=True), Output("nr-giorno-concordato", "date", allow_duplicate=True), Output("nr-orario-concordato", "value", allow_duplicate=True), Output("nr-lingua", "value", allow_duplicate=True), Output("nr-nazionalita", "value", allow_duplicate=True), Output("nr-eta", "value", allow_duplicate=True), Output("nr-sesso", "value", allow_duplicate=True), Output("nr-note", "value", allow_duplicate=True), Output("edit-request-id-store-local", "data", allow_duplicate=True), Output("nr-form-title", "children", allow_duplicate=True), Output("nr-form-subtitle", "children", allow_duplicate=True), Output("btn-salva-richiesta", "children", allow_duplicate=True)],
        Input("btn-salva-richiesta", "n_clicks"),
        [State("nr-data-richiesta", "date"), State("nr-servizio-richiedente", "value"), State("nr-indirizzo-servizio", "value"), State("nr-operatore-richiedente", "value"), State("nr-giorno-concordato", "date"), State("nr-orario-concordato", "value"), State("nr-lingua", "value"), State("nr-nazionalita", "value"), State("nr-eta", "value"), State("nr-sesso", "value"), State("nr-note", "value"), State('edit-request-id-store-local', 'data'), State('refresh-signal-store', 'data'), State("login-status-store", "data")],
        prevent_initial_call=True
    )
    def save_request(n_clicks, data_richiesta, servizio, indirizzo, operatore, giorno_conc, orario_conc, lingua, nazionalita, eta, sesso, note, edit_id_local, current_refresh_signal, login_status):
        # ... (Codice callback save_request invariato, usa force_save=True) ...
        print(f"\n--- save_request --- Clicks:{n_clicks}, EditID_Local:{edit_id_local}"); today=datetime.date.today().isoformat(); def_sub="Inserisci dettagli."; reset_form=[today,"",config.DEFAULT_INDIRIZZO_SERVIZIO,"",None,"","", "",None,"ND","", None, config.DEFAULT_FORM_TITLE, def_sub, config.DEFAULT_SAVE_BUTTON_TEXT]; num_form_reset=len(reset_form); init_out=[no_update, no_update, no_update] + [no_update]*num_form_reset
        if not n_clicks or n_clicks == 0: return init_out
        user_lvl=login_status.get('level') if isinstance(login_status, dict) else None; user_name=login_status.get('username') if isinstance(login_status, dict) else None
        if user_lvl is None or not user_name: alert=dbc.Alert("Errore: Sessione non valida.", color="danger", duration=5000); return alert, no_update, None, *([no_update]*num_form_reset)
        print(f"save_request: User '{user_name}' (L{user_lvl}) saving...")
        req_fields={"Data R.": data_richiesta, "Servizio": servizio, "Operatore": operatore, "Giorno": giorno_conc, "Orario": orario_conc, "Lingua": lingua}; missing=[k for k,v in req_fields.items() if not v]
        if missing: alert=dbc.Alert(f"Errore: Campi mancanti: {', '.join(missing)} (*)", color="danger", dismissable=True); return alert, no_update, no_update, *([no_update]*num_form_reset)
        form_data={"data_richiesta":data_richiesta, "servizio_richiedente":servizio.strip() if servizio else None, "indirizzo_servizio":indirizzo.strip() if indirizzo else config.DEFAULT_INDIRIZZO_SERVIZIO, "nome_operatore_richiedente":operatore.strip() if operatore else None, "giorno_concordato":giorno_conc, "orario_concordato":orario_conc.strip() if orario_conc else None, "lingua_richiesta":lingua.strip() if lingua else None, "nazionalita_paziente":nazionalita.strip() if nazionalita else None, "eta_paziente":int(eta) if eta is not None and str(eta).isdigit() else None, "sesso_paziente":sesso, "note_richiesta":note.strip() if note else None}
        reqs=load_requests(); is_update = edit_id_local is not None; fb_parts=[]; pdf_fb=""; pdf_col=None; new_ref=no_update
        if is_update:
             print(f"Processing UPDATE ID {edit_id_local}")
             if user_lvl != 2: alert=dbc.Alert("Errore: Solo admin possono modificare.", color="danger", dismissable=True); return alert, no_update, no_update, *([no_update]*num_form_reset)
             updated=False; idx=-1; existing=None
             for i,r in enumerate(reqs):
                  if isinstance(r,dict) and str(r.get('id'))==str(edit_id_local): idx=i; existing=r; break
             if not existing: err=dbc.Alert(f"Errore: ID {edit_id_local} non trovato.", color="danger", duration=5000); return err, no_update, None, *reset_form
             form_data['id']=edit_id_local; form_data['stato']=existing.get('stato',config.STATUS_RICEVUTA); form_data['mediatore_assegnato']=existing.get('mediatore_assegnato'); form_data['timestamp_creazione']=existing.get('timestamp_creazione'); form_data['richiedente_username']=existing.get('richiedente_username'); form_data['pdf_path']=existing.get('pdf_path')
             for k in ['change_request_details','change_request_status','change_request_timestamp','change_request_user']:
                 if k in existing: form_data[k] = existing[k]
             pdf_path=generate_mediation_request_pdf(form_data)
             if pdf_path: form_data['pdf_path']=pdf_path; pdf_fb=[" PDF aggiornato: ", html.Code(Path(pdf_path).name)]
             else: pdf_fb=html.Strong(" Attenzione: Errore aggiorn. PDF."); pdf_col="warning"
             reqs[idx]=form_data; updated=True
             if updated: save_requests(reqs, force_save=True); fb_parts.append(f"Richiesta (ID: {edit_id_local}) aggiornata!"); (fb_parts.extend(pdf_fb) if isinstance(pdf_fb, list) else fb_parts.append(pdf_fb)); new_ref=(current_refresh_signal or 0)+1; print(f"L2 Update success ID {edit_id_local}. Refresh: {new_ref}"); fb_alert=dbc.Alert(fb_parts, color=(pdf_col or "success"), duration=6000); return fb_alert, new_ref, None, *reset_form
        else: # Nuova Richiesta
             print(f"Processing NEW request by '{user_name}'"); next_id=get_next_id(reqs); form_data['id']=next_id; form_data['stato']=config.STATUS_RICEVUTA; form_data['mediatore_assegnato']=None; form_data['timestamp_creazione']=datetime.datetime.now().isoformat(); form_data['pdf_path']=None; form_data['richiedente_username']=user_name; form_data['change_request_details']=None; form_data['change_request_status']=None; form_data['change_request_timestamp']=None; form_data['change_request_user']=None
             pdf_path=generate_mediation_request_pdf(form_data)
             if pdf_path: form_data['pdf_path']=pdf_path; pdf_fb=[" PDF generato: ", html.Code(Path(pdf_path).name)]
             else: pdf_fb=html.Strong(" Attenzione: Errore generaz. PDF."); pdf_col="warning"
             reqs.append(form_data); save_requests(reqs, force_save=True); fb_parts.append(f"Nuova richiesta (ID: {next_id}) salvata!"); (fb_parts.extend(pdf_fb) if isinstance(pdf_fb, list) else fb_parts.append(pdf_fb)); new_ref=(current_refresh_signal or 0)+1; print(f"New request ID {next_id} saved. Refresh: {new_ref}"); fb_alert=dbc.Alert(fb_parts, color=(pdf_col or "success"), duration=6000); return fb_alert, new_ref, None, *reset_form