# callbacks/main_callbacks.py
import dash
from dash import Output, Input, State, callback_context, html, no_update
import dash_bootstrap_components as dbc
# Aggiunto create_mediatori_layout
from components.layouts import create_ricevi_form, create_gestisci_layout, create_giorno_layout, create_mediatori_layout
from utils.data_manager import load_requests
import traceback

def register_main_callbacks(app):
    @app.callback(
        [Output('col-btn-ricevi', 'style'),
         Output('col-btn-gestisci', 'style'),
         Output('col-btn-giorno', 'style'),
         Output('col-btn-mediatori', 'style'), # <-- NUOVO OUTPUT
         Output('btn-gestisci', 'children')],
        Input('login-status-store', 'data')
    )
    def toggle_nav_buttons_visibility(login_status):
         style_h={'display':'none'}; style_v={'display':'block'};
         r_sty, g_sty, d_sty, m_sty = style_h, style_h, style_h, style_h # <-- NUOVA VARIABILE STILE
         g_txt=[html.I(className="bi bi-card-list me-2"), "2. Visualizza"];
         if isinstance(login_status, dict) and 'level' in login_status:
             lvl=login_status.get('level');
             if lvl==1: r_sty,g_sty,d_sty,m_sty=style_v,style_v,style_h,style_h; g_txt=[html.I(className="bi bi-person-lines-fill me-2"), "2. Le Mie Richieste"]
             elif lvl==2: r_sty,g_sty,d_sty,m_sty=style_v,style_v,style_v,style_v; g_txt=[html.I(className="bi bi-card-checklist me-2"), "2. Gestisci Tutte"] # <-- Mostra bottone mediatori L2
         return r_sty, g_sty, d_sty, m_sty, g_txt # <-- RITORNA NUOVO STILE

    @app.callback(
        [Output("contenuto-principale", "children"),
         Output("active-view-store", "data")],
        [Input("btn-ricevi", "n_clicks"),
         Input("btn-gestisci", "n_clicks"),
         Input("btn-giorno", "n_clicks"),
         Input("btn-mediatori", "n_clicks"), # <-- NUOVO INPUT
         Input("refresh-signal-store", "data"),
         Input("edit-request-id-store", "data")],
        [State("active-view-store", "data"),
         State("login-status-store", "data")]
    )
    def display_content(n_ricevi, n_gestisci, n_giorno, n_mediatori, refresh_signal, edit_id, current_view, login_status): # <-- NUOVO PARAMETRO n_mediatori
        print(f"\n--- display_content --- Trigger: {callback_context.triggered_id}, EditID: {edit_id}, CurrView: {current_view}")
        user_lvl=login_status.get('level') if isinstance(login_status,dict) else None; user_name=login_status.get('username') if isinstance(login_status,dict) else None;
        if user_lvl is None: return html.Div(), 'gestisci'
        target_view = None; default_view = 'ricevi' if user_lvl == 1 else 'gestisci'; trig_id = callback_context.triggered_id
        edit_data_to_pass = None
        if trig_id == 'edit-request-id-store' and edit_id is not None and user_lvl == 2:
            target_view = 'ricevi'; # ... (logica caricamento dati edit invariata) ...
            try: reqs = load_requests(); edit_data_to_pass = next((r for r in reqs if isinstance(r, dict) and str(r.get('id')) == str(edit_id)), None); # ...
            except Exception as e: print(f"ERR load edit data: {e}")
        elif trig_id == 'btn-ricevi': target_view = 'ricevi'
        elif trig_id == 'btn-gestisci': target_view = 'gestisci'
        elif trig_id == 'btn-giorno': target_view = 'giorno'
        elif trig_id == 'btn-mediatori': target_view = 'mediatori' # <-- NUOVA VISTA
        elif trig_id == 'refresh-signal-store': target_view = current_view
        else: target_view = default_view

        # --- Controllo Accesso Aggiornato ---
        can_access = False
        if target_view=='ricevi' and user_lvl in [1,2]: can_access = True
        if target_view=='gestisci' and user_lvl in [1,2]: can_access = True
        if target_view=='giorno' and user_lvl==2: can_access = True
        if target_view=='mediatori' and user_lvl==2: can_access = True # <-- SOLO L2
        # --- Fine Controllo Accesso ---

        if not can_access: target_view=default_view; print(f"Access DENIED L{user_lvl} to '{trig_id or 'default'}'. Reverting to '{target_view}'.");
        if (target_view=='ricevi' and user_lvl not in [1,2]) or (target_view=='gestisci' and user_lvl not in [1,2]) or (target_view=='giorno' and user_lvl != 2) or (target_view=='mediatori' and user_lvl != 2): # <-- Aggiunto check mediatori
              print(f"ERRORE: No access to default '{target_view}'!"); return dbc.Alert("Errore permessi.", color="danger"), current_view

        print(f"display_content: Generating '{target_view}'"); content=html.Div(f"Errore layout '{target_view}'."); active_view=target_view;
        try:
            if target_view == 'ricevi': content = create_ricevi_form(user_name, user_lvl, edit_data=edit_data_to_pass)
            elif target_view == 'gestisci': content = create_gestisci_layout(user_name, user_lvl)
            elif target_view == 'giorno': content = create_giorno_layout(user_name, user_lvl)
            elif target_view == 'mediatori': content = create_mediatori_layout(user_name, user_lvl) # <-- NUOVO LAYOUT
        except Exception as e: print(f"ERR layout '{target_view}': {e}"); traceback.print_exc(); content=dbc.Alert(f"Errore '{target_view}'.", color="danger"); active_view=default_view
        return content, active_view

    # Callback store_edit_id invariato
    @app.callback( Output("edit-request-id-store", "data", allow_duplicate=True), Input({'type': 'btn-edit-request', 'index': dash.ALL}, 'n_clicks'), State("login-status-store", "data"), prevent_initial_call=True )
    def store_edit_id(n_clicks_list, login_status):
         print(f"\n--- store_edit_id ---"); trig=callback_context.triggered_id;
         if not trig or not isinstance(trig, dict) or not callback_context.triggered[0]['value']: return no_update
         user_lvl=login_status.get('level') if isinstance(login_status, dict) else None
         if user_lvl != 2: return no_update
         req_id=trig['index']; print(f"L2 storing edit ID {req_id}."); return req_id