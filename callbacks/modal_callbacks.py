# callbacks/modal_callbacks.py
import dash
from dash import Output, Input, State, html, dcc, callback_context, no_update
import dash_bootstrap_components as dbc
import datetime
from pathlib import Path
# Importa funzioni dati, helpers e config
from utils.data_manager import load_requests, save_requests, load_mediators # Aggiunto load_mediators
from utils.helpers import generate_mediation_request_pdf, create_persistent_alert, format_date_italian
import config

def register_modal_callbacks(app):
    # Callback 8: Toggle Assign Modal (Aggiorna opzioni Select)
    @app.callback(
        [Output("assign-mediator-modal", "is_open"),
         Output("assign-mediator-request-id-store", "data"),
         Output("assign-mediator-input", "value"), # Valore selezionato
         Output("assign-mediator-input", "options"), # Opzioni del Select
         Output("assign-modal-feedback", "children")],
        Input({'type': 'btn-assign-mediator', 'index': dash.ALL}, 'n_clicks'),
        [State("assign-mediator-modal", "is_open"),
         State("login-status-store", "data")],
        prevent_initial_call=True
    )
    def toggle_assign_modal(n_clicks_list, is_open, login_status):
         if not isinstance(login_status, dict) or login_status.get('level') != 2:
             return False, no_update, no_update, no_update, no_update
         triggered = callback_context.triggered_id;
         if not triggered or not isinstance(triggered, dict) or not callback_context.triggered[0]['value']:
             return no_update, no_update, no_update, no_update, no_update

         req_id = triggered['index']
         reqs = load_requests()
         req = next((r for r in reqs if isinstance(r,dict) and str(r.get('id')) == str(req_id)), None)

         current_mediators = load_mediators()
         mediator_options = [{"label": config.MEDIATOR_SPECIAL_OPTION, "value": config.MEDIATOR_SPECIAL_OPTION}] + \
                            [{"label": name, "value": name} for name in current_mediators]

         current_mediator_or_path = req.get('mediatore_assegnato') if req else None
         valid_option_values = [opt['value'] for opt in mediator_options]
         initial_select_value = current_mediator_or_path if current_mediator_or_path in valid_option_values else None

         return not is_open, req_id, initial_select_value, mediator_options, ""

    # Callback 9: Save Assign Mediator (Gestisce "Percorsi")
    @app.callback(
        [Output("assign-mediator-modal", "is_open", allow_duplicate=True),
         Output("gestisci-feedback-alert-container", "children"),
         Output('refresh-signal-store', 'data', allow_duplicate=True),
         Output("assign-modal-feedback", "children", allow_duplicate=True)],
        [Input("assign-mediator-save-btn", "n_clicks"),
         Input("assign-mediator-cancel-btn", "n_clicks")],
        [State("assign-mediator-input", "value"),
         State("assign-mediator-request-id-store", "data"),
         State('refresh-signal-store', 'data'),
         State("login-status-store", "data")],
        prevent_initial_call=True
    )
    def save_assign_mediator(save_clicks, cancel_clicks, selected_value, request_id, current_refresh_signal, login_status):
        trig_id = callback_context.triggered_id; modal_open, main_fb, ref_sig, modal_fb = True, no_update, no_update, no_update
        if trig_id == "assign-mediator-save-btn" and (not isinstance(login_status, dict) or login_status.get('level') != 2):
            return True, no_update, no_update, dbc.Alert("Non permesso.", color="danger")

        if trig_id == "assign-mediator-save-btn" and save_clicks > 0 and request_id is not None:
            if not selected_value:
                modal_fb = dbc.Alert("Selezionare un mediatore o 'Percorsi'.", color="warning")
            else:
                 reqs = load_requests(); updated=False; found=False; stat_chg=""; pdf_fb=""; pdf_col=None; idx=-1; new_status = None; mediator_to_save = selected_value
                 if selected_value == config.MEDIATOR_SPECIAL_OPTION:
                     print(f"save_assign_mediator: Opzione '{config.MEDIATOR_SPECIAL_OPTION}' selezionata per ID {request_id}.")
                     new_status = config.STATUS_PERCORSI
                 else:
                     print(f"save_assign_mediator: Mediatore '{selected_value}' selezionato per ID {request_id}.")
                     new_status = config.STATUS_ASSEGNATA

                 for i, r in enumerate(reqs):
                     if isinstance(r, dict) and str(r.get('id')) == str(request_id):
                         idx=i; found=True; original_status = r.get('stato'); original_mediator = r.get('mediatore_assegnato')
                         if original_mediator != mediator_to_save or original_status != new_status:
                              r['mediatore_assegnato'] = mediator_to_save
                              if original_status != new_status:
                                  r['stato'] = new_status
                                  stat_chg=f" Stato -> '{new_status}'."
                                  print(f"save_assign_mediator: Status changed to {new_status}.")
                              else: stat_chg=""
                              updated = True
                         else: print(f"save_assign_mediator: Nessuna modifica necessaria per ID {request_id}.")
                         break # Esci dal ciclo una volta trovato

                 if updated and found and idx != -1:
                      upd_req = reqs[idx]; pdf_path = generate_mediation_request_pdf(upd_req)
                      if pdf_path: upd_req['pdf_path'] = pdf_path; pdf_fb = f" PDF rigenerato."
                      else: pdf_fb = " Err rigener. PDF."; pdf_col="warning"
                      save_requests(reqs, force_save=True); ref_sig = (current_refresh_signal or 0) + 1; txt=f"Richiesta ID {request_id}: impostato '{mediator_to_save}'.{stat_chg}{pdf_fb}"; col=pdf_col or "success"
                      main_fb = create_persistent_alert(txt, col); modal_open, modal_fb = False, ""
                 elif found: main_fb = create_persistent_alert(f"Nessuna modifica necessaria per ID {request_id}.", "info"); modal_open, modal_fb = False, ""
                 else: main_fb = create_persistent_alert(f"Errore: ID {request_id} non trovato.", "danger"); modal_open, modal_fb = False, ""
        elif trig_id == "assign-mediator-cancel-btn" and cancel_clicks > 0: modal_open, modal_fb, main_fb = False, "", no_update
        if main_fb is no_update and trig_id != "assign-mediator-cancel-btn": main_fb = None
        return modal_open, main_fb, ref_sig, modal_fb

    # Callback 10: Toggle Change Status Modal
    @app.callback( [Output("change-status-modal", "is_open"), Output("change-status-request-id-store", "data"), Output("change-status-dropdown", "value"), Output("change-status-modal-feedback", "children")], Input({'type': 'btn-change-status', 'index': dash.ALL}, 'n_clicks'), [State("change-status-modal", "is_open"), State("login-status-store", "data")], prevent_initial_call=True )
    def toggle_status_modal(n_clicks_list, is_open, login_status):
         if not isinstance(login_status, dict) or login_status.get('level') != 2: return False, no_update, no_update, no_update
         triggered = callback_context.triggered_id;
         if not triggered or not isinstance(triggered, dict) or not callback_context.triggered[0]['value']: return no_update, no_update, no_update, no_update
         req_id = triggered['index']; reqs = load_requests(); req = next((r for r in reqs if isinstance(r,dict) and str(r.get('id')) == str(req_id)), None); curr_stat = req.get('stato', config.STATUS_RICEVUTA) if req else config.STATUS_RICEVUTA
         return not is_open, req_id, curr_stat, ""

    # Callback 11: Save Change Status (CORRETTO)
    @app.callback(
        [Output("change-status-modal", "is_open", allow_duplicate=True),
         Output("gestisci-feedback-alert-container", "children", allow_duplicate=True),
         Output('refresh-signal-store', 'data', allow_duplicate=True),
         Output("change-status-modal-feedback", "children", allow_duplicate=True)],
        [Input("change-status-save-btn", "n_clicks"),
         Input("change-status-cancel-btn", "n_clicks")],
        [State("change-status-dropdown", "value"),
         State("change-status-request-id-store", "data"),
         State('refresh-signal-store', 'data'),
         State("login-status-store", "data")],
        prevent_initial_call=True
    )
    def save_change_status(save_clicks, cancel_clicks, new_status, request_id, current_refresh_signal, login_status):
        trig_id = callback_context.triggered_id; modal_open, main_fb, ref_sig, modal_fb = True, no_update, no_update, no_update
        if trig_id == "change-status-save-btn" and (not isinstance(login_status, dict) or login_status.get('level') != 2):
            return True, no_update, no_update, dbc.Alert("Non permesso.", color="danger")
        if trig_id == "change-status-save-btn" and save_clicks > 0 and request_id is not None:
            if not new_status or new_status not in config.VALID_STATUSES:
                modal_fb = dbc.Alert("Stato non valido.", color="warning")
            else:
                reqs = load_requests(); updated=False; found=False; idx=-1
                for i, r in enumerate(reqs):
                    if isinstance(r, dict) and str(r.get('id')) == str(request_id):
                        found=True
                        idx=i
                        # --- Blocco Corretto ---
                        if r.get('stato') != new_status:
                            r['stato'] = new_status
                            updated=True
                        else:
                            print(f"save_change_status: Stato già '{new_status}'.")
                        # --- Fine Blocco ---
                        break # Esci dal ciclo dopo aver trovato
                if found:
                    if updated:
                        save_requests(reqs, force_save=True);
                        ref_sig = (current_refresh_signal or 0) + 1;
                        main_fb = create_persistent_alert(f"Stato ID {request_id} -> '{new_status}'.", "success");
                        modal_open, modal_fb = False, ""
                    else:
                        modal_fb = dbc.Alert(f"Stato già '{new_status}'.", color="info")
                else:
                    main_fb = create_persistent_alert(f"Errore: ID {request_id} non trovato.", "danger")
                    modal_open, modal_fb = False, ""
        elif trig_id == "change-status-cancel-btn" and cancel_clicks > 0:
            modal_open, modal_fb, main_fb = False, "", no_update
        if main_fb is no_update and trig_id != "change-status-cancel-btn":
            main_fb = None
        return modal_open, main_fb, ref_sig, modal_fb

    # Callback 12: Toggle Delete Modal
    @app.callback( [Output("delete-confirm-modal", "is_open"), Output("delete-request-id-store", "data"), Output("delete-confirm-details", "children"), Output("delete-modal-feedback", "children")], Input({'type': 'btn-delete-request', 'index': dash.ALL}, 'n_clicks'), [State("delete-confirm-modal", "is_open"), State("login-status-store", "data")], prevent_initial_call=True )
    def toggle_delete_modal(n_clicks_list, is_open, login_status):
         trig_id = callback_context.triggered_id; trig_val = callback_context.triggered[0]['value'] if callback_context.triggered else None;
         if not isinstance(login_status, dict) or login_status.get('level') != 2: return False, no_update, no_update, no_update # Solo L2
         if not trig_id or not isinstance(trig_id, dict) or not isinstance(trig_val, int) or trig_val <= 0: return is_open, no_update, no_update, no_update
         req_id = trig_id.get('index');
         if req_id is None: return is_open, no_update, no_update, dbc.Alert("Errore ID bottone.", color="danger")
         reqs = load_requests(); req = next((r for r in reqs if isinstance(r,dict) and str(r.get('id')) == str(req_id)), None)
         details = f"ID: {req_id} (N/D)"; open_modal = False; fb_msg = ""
         if req: details = [html.Strong(f"ID: {req_id}"), html.Br(), f"Servizio: {req.get('servizio_richiedente','N/D')}", html.Br(), f"Data App: {format_date_italian(req.get('giorno_concordato'))} {req.get('orario_concordato','')}", html.Br(), f"Richiedente: {req.get('richiedente_username','N/D')}"]; open_modal = True
         else: fb_msg = dbc.Alert(f"ID {req_id} non trovato.", color="danger", duration=4000)
         if open_modal: new_state = not is_open; return new_state, req_id, details, ""
         else: return False, no_update, no_update, fb_msg

    # Callback 13: Execute Delete Request
    @app.callback( [Output("delete-confirm-modal", "is_open", allow_duplicate=True), Output("gestisci-feedback-alert-container", "children", allow_duplicate=True), Output('refresh-signal-store', 'data', allow_duplicate=True), Output("delete-modal-feedback", "children", allow_duplicate=True)], [Input("delete-confirm-btn", "n_clicks"), Input("delete-cancel-btn", "n_clicks")], [State("delete-request-id-store", "data"), State('refresh-signal-store', 'data'), State("login-status-store", "data")], prevent_initial_call=True )
    def execute_delete_request(delete_clicks, cancel_clicks, request_id, current_refresh_signal, login_status):
        triggered_id = callback_context.triggered_id; print(f"\n--- execute_delete_request triggered by {triggered_id}. Req ID: {request_id} ---")
        modal_open, main_fb, ref_sig, modal_fb = True, no_update, no_update, no_update
        if triggered_id == "delete-confirm-btn" and (not isinstance(login_status, dict) or login_status.get('level') != 2):
            return True, no_update, no_update, dbc.Alert("Non permesso.", color="danger")
        if triggered_id == "delete-confirm-btn" and delete_clicks > 0 and request_id is not None:
            reqs = load_requests(); req_del = next((r for r in reqs if isinstance(r,dict) and str(r.get('id')) == str(request_id)), None)
            if not req_del: main_fb = create_persistent_alert(f"Errore: ID {request_id} non trovato.", "danger"); modal_open, modal_fb = False, ""; return modal_open, main_fb, no_update, modal_fb
            reqs_new = [r for r in reqs if not (isinstance(r,dict) and str(r.get('id')) == str(request_id))]; pdf_msg = ""; pdf_path_str = req_del.get('pdf_path')
            if pdf_path_str:
                try:
                    base = config.PDF_SAVE_DIR_BASE.resolve(); rel = Path(pdf_path_str.replace('\\','/').strip('/')); full = (base / rel).resolve(); print(f"DEBUG delete: Checking PDF path: {full}")
                    if full.is_file() and full.is_relative_to(base):
                        try: full.unlink(); pdf_msg = " PDF associato eliminato."; print(f"DEBUG delete: PDF deleted: {full}")
                        except Exception as e_del: pdf_msg = f" Errore eliminazione PDF: {e_del}."; print(f"ERROR deleting PDF {full}: {e_del}")
                    elif not full.exists(): pdf_msg = " File PDF associato non trovato."; print(f"DEBUG delete: PDF not found: {full}")
                    else: pdf_msg = " Errore: Percorso PDF non valido/sicuro."; print(f"ERROR delete: PDF path invalid/unsafe: {full}")
                except Exception as path_e: pdf_msg = f" Errore gestione percorso PDF: {path_e}."; print(f"ERROR processing PDF path '{pdf_path_str}': {path_e}")
            save_requests(reqs_new, force_save=True); ref_sig = (current_refresh_signal or 0) + 1; main_fb = create_persistent_alert(f"ID {request_id} eliminato.{pdf_msg}", "success"); modal_open, modal_fb = False, ""; print(f"execute_delete_request: Success. Refresh: {ref_sig}")
        elif triggered_id == "delete-cancel-btn" and cancel_clicks > 0: modal_open, modal_fb, main_fb = False, "", no_update
        if main_fb is no_update and triggered_id != "delete-cancel-btn": main_fb = None
        return modal_open, main_fb, ref_sig, modal_fb

    # Callback 14: Toggle Request Change Modal (L1)
    @app.callback( [Output("request-change-modal", "is_open"), Output("request-change-id-store", "data"), Output("request-change-reason-input", "value"), Output("request-change-modal-feedback", "children")], Input({'type': 'btn-request-change', 'index': dash.ALL}, 'n_clicks'), [State("request-change-modal", "is_open"), State("login-status-store", "data")], prevent_initial_call=True )
    def toggle_request_change_modal(n_clicks_list, is_open, login_status):
         trig_id = callback_context.triggered_id;
         if not trig_id or not isinstance(trig_id, dict) or not callback_context.triggered[0]['value']: return no_update, no_update, no_update, no_update
         user_lvl = login_status.get('level') if isinstance(login_status, dict) else None; user_name = login_status.get('username') if isinstance(login_status, dict) else None
         if user_lvl != 1 or not user_name: return False, no_update, "", dbc.Alert("Non permesso.", color="danger")
         req_id = trig_id.get('index');
         if req_id is None: return no_update, no_update, no_update, no_update
         reqs = load_requests(); req = next((r for r in reqs if isinstance(r,dict) and str(r.get('id')) == str(req_id)), None)
         if not req or req.get('richiedente_username') != user_name: return False, no_update, "", no_update
         return not is_open, req_id, "", ""

    # Callback 15: Save Change Request (L1)
    @app.callback( [Output("request-change-modal", "is_open", allow_duplicate=True), Output("gestisci-feedback-alert-container", "children", allow_duplicate=True), Output('refresh-signal-store', 'data', allow_duplicate=True), Output("request-change-modal-feedback", "children", allow_duplicate=True)], [Input("request-change-submit-btn", "n_clicks"), Input("request-change-cancel-btn", "n_clicks")], [State("request-change-reason-input", "value"), State("request-change-id-store", "data"), State('refresh-signal-store', 'data'), State("login-status-store", "data")], prevent_initial_call=True )
    def save_change_request(submit_clicks, cancel_clicks, reason, request_id, current_refresh_signal, login_status):
        triggered_id = callback_context.triggered_id; modal_open, main_fb, ref_sig, modal_fb = True, no_update, no_update, no_update
        user_lvl = login_status.get('level') if isinstance(login_status, dict) else None; user_name = login_status.get('username') if isinstance(login_status, dict) else None
        if user_lvl != 1 or not user_name: return True, no_update, no_update, dbc.Alert("Non permesso.", color="danger")
        if triggered_id == "request-change-submit-btn" and submit_clicks > 0 and request_id is not None:
            reas = reason.strip() if reason else None
            if not reas: modal_fb = dbc.Alert("Motivo obbligatorio.", color="warning")
            else:
                 reqs = load_requests(); found=False; idx=-1; owner_ok=False
                 for i, r in enumerate(reqs):
                     if isinstance(r, dict) and str(r.get('id')) == str(request_id):
                         found=True; idx=i
                         if r.get('richiedente_username') == user_name:
                              owner_ok=True; r['change_request_details'] = reas; r['change_request_status'] = config.CHANGE_REQ_PENDING; r['change_request_timestamp'] = datetime.datetime.now().isoformat(); r['change_request_user'] = user_name
                         break
                 if found and owner_ok: save_requests(reqs, force_save=True); ref_sig = (current_refresh_signal or 0) + 1; main_fb = create_persistent_alert(f"Richiesta mod/ann ID {request_id} inviata correttamente all'amministratore.", "success"); modal_open = False; modal_fb = ""
                 elif not found: main_fb = create_persistent_alert(f"Errore: ID {request_id} non trovato.", "danger"); modal_open = False; modal_fb = ""
                 elif not owner_ok: main_fb = create_persistent_alert(f"Errore: Non puoi modif. ID {request_id}.", "danger"); modal_open = False; modal_fb = ""
        elif triggered_id == "request-change-cancel-btn" and cancel_clicks > 0: modal_open = False; modal_fb = ""; main_fb = no_update
        if main_fb is no_update and triggered_id != "request-change-cancel-btn": main_fb = None
        return modal_open, main_fb, ref_sig, modal_fb

    # Callback 16: Toggle Review Change Modal (L2)
    @app.callback( [Output("review-change-request-modal", "is_open"), Output("review-change-id-store", "data"), Output("review-change-request-details", "children"), Output("review-change-modal-feedback", "children")], Input({'type': 'btn-review-change', 'index': dash.ALL}, 'n_clicks'), [State("review-change-request-modal", "is_open"), State("login-status-store", "data")], prevent_initial_call=True )
    def toggle_review_change_modal(n_clicks_list, is_open, login_status):
         trig_id = callback_context.triggered_id;
         if not trig_id or not isinstance(trig_id, dict) or not callback_context.triggered[0]['value']: return no_update, no_update, no_update, no_update
         if not isinstance(login_status, dict) or login_status.get('level') != 2: return False, no_update, "", no_update # Solo L2
         req_id = trig_id.get('index');
         if req_id is None: return no_update, no_update, no_update, no_update
         reqs = load_requests(); req = next((r for r in reqs if isinstance(r,dict) and str(r.get('id')) == str(req_id)), None)
         details = [html.P("Errore: Dettagli non trovati.")];
         if req and req.get('change_request_status') == config.CHANGE_REQ_PENDING:
              usr = req.get('change_request_user', 'N/D'); ts_str = req.get('change_request_timestamp', ''); dts = req.get('change_request_details', 'Nessuno.')
              try: ts_dt = datetime.datetime.fromisoformat(ts_str); ts_fmt = ts_dt.strftime('%d/%m/%Y %H:%M')
              except: ts_fmt = ts_str or 'N/D'
              details = [html.P([html.Strong("ID: "), str(req_id)]), html.P([html.Strong("User L1: "), usr]), html.P([html.Strong("Data: "), ts_fmt]), html.Strong("Dettagli:"), html.Blockquote(dts, className="text-muted border-start ps-3")]
         elif req: details = html.P(f"Nessuna richiesta pendente per ID {req_id}.")
         return not is_open, req_id, details, ""

    # Callback 17: Handle Review Action (Clear flag & Trigger Edit - L2)
    @app.callback( [Output("review-change-request-modal", "is_open", allow_duplicate=True), Output("gestisci-feedback-alert-container", "children", allow_duplicate=True), Output('refresh-signal-store', 'data', allow_duplicate=True), Output("review-change-modal-feedback", "children", allow_duplicate=True), Output("edit-request-id-store", "data", allow_duplicate=True)], [Input("review-clear-change-btn", "n_clicks"), Input("review-change-close-btn", "n_clicks")], [State("review-change-id-store", "data"), State('refresh-signal-store', 'data'), State("login-status-store", "data")], prevent_initial_call=True )
    def handle_review_action(clear_clicks, close_clicks, request_id, current_refresh_signal, login_status):
        triggered_id = callback_context.triggered_id; modal_open, main_fb, ref_sig, modal_fb, edit_id_to_set = True, no_update, no_update, no_update, no_update
        if not isinstance(login_status, dict) or login_status.get('level') != 2: return True, no_update, no_update, dbc.Alert("Non permesso.", color="danger"), no_update
        if triggered_id == "review-clear-change-btn" and clear_clicks > 0 and request_id is not None:
            print(f"handle_review_action: L2 clearing change flag for ID {request_id} and triggering edit.")
            reqs = load_requests(); found=False; idx=-1; updated=False
            for i, r in enumerate(reqs):
                if isinstance(r, dict) and str(r.get('id')) == str(request_id):
                    found=True; idx=i
                    if 'change_request_status' in r:
                        r.pop('change_request_status', None); r.pop('change_request_details', None); r.pop('change_request_timestamp', None); r.pop('change_request_user', None)
                        updated=True
                    break
            if found and updated: save_requests(reqs, force_save=True); ref_sig = (current_refresh_signal or 0) + 1; main_fb = create_persistent_alert(f"Segnalazione ID {request_id} cancellata. Apertura modifica...", "success"); modal_open = False; modal_fb = ""; edit_id_to_set = request_id; print(f"handle_review_action: Success, setting edit_id_store to {edit_id_to_set}")
            elif not found: main_fb = create_persistent_alert(f"Errore: ID {request_id} non trovato.", "danger"); modal_open = False; modal_fb = ""
            else: modal_fb = dbc.Alert("Nessuna segnalazione pendente da cancellare.", color="info")
        elif triggered_id == "review-change-close-btn" and close_clicks > 0: modal_open = False; modal_fb = ""; main_fb = no_update; ref_sig = no_update; edit_id_to_set = no_update
        if main_fb is no_update and triggered_id != "review-change-close-btn": main_fb = None
        return modal_open, main_fb, ref_sig, modal_fb, edit_id_to_set