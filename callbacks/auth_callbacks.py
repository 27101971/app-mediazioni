# callbacks/auth_callbacks.py
import dash
from dash import Output, Input, State, callback_context, no_update
import dash_bootstrap_components as dbc
# --- MODIFICA QUI ---
# Importa da helpers invece che da app
from utils.helpers import load_users, check_password_hash, WERKZEUG_AVAILABLE
# --- FINE MODIFICA ---

def register_auth_callbacks(app):
    @app.callback(
        [Output('login-status-store', 'data'),
         Output('login-feedback', 'children'),
         Output('username-input', 'value'),
         Output('password-input', 'value')],
        [Input('login-button', 'n_clicks'),
         Input('username-input', 'n_submit'),
         Input('password-input', 'n_submit')],
        [State('username-input', 'value'),
         State('password-input', 'value')],
        prevent_initial_call=True
    )
    def handle_login(btn_clicks, user_submit, pwd_submit, username, password):
        triggered = callback_context.triggered_id
        print(f"\n--- handle_login triggered by: {triggered} ---")
        # Usa WERKZEUG_AVAILABLE importato da helpers
        if not WERKZEUG_AVAILABLE: return None, dbc.Alert("Errore sicurezza!", color="danger"), username or "", ""
        if not triggered and not callback_context.triggered: return no_update, no_update, no_update, no_update
        is_login = (triggered == 'login-button' and btn_clicks > 0) or (triggered == 'username-input' and user_submit > 0) or (triggered == 'password-input' and pwd_submit > 0)
        if is_login:
            user = username.strip() if username else "";
            if not user or not password: return None, dbc.Alert("Inserire credenziali.", color="warning"), user, ""
            users = load_users(); # Usa la funzione da helpers
            if not users: return None, dbc.Alert("Errore utenti.", color="danger"), user, ""
            data = users.get(user)
            if data and isinstance(data, dict) and 'hashed_password' in data and 'level' in data:
                 # Usa check_password_hash importato da helpers
                 hash_ok = check_password_hash(data['hashed_password'], password)
                 if hash_ok: info = {'level': data['level'], 'username': user, 'nome_reparto': data.get('nome_reparto', user)}; return info, dbc.Alert(f"Accesso OK: {user}", color="success", duration=3000), "", ""
                 else: return None, dbc.Alert("Credenziali errate.", color="danger"), user, ""
            else: return None, dbc.Alert("Credenziali errate.", color="danger"), user, ""
        return no_update, no_update, no_update, no_update

    @app.callback(
        [Output('main-app-content', 'style'),
         Output('login-form-div', 'style')],
        Input('login-status-store', 'data')
    )
    def toggle_main_content_visibility(login_status):
         is_logged_in = isinstance(login_status, dict) and 'level' in login_status and 'username' in login_status; return ({'display': 'block'}, {'display': 'none'}) if is_logged_in else ({'display': 'none'}, {'display': 'block'})