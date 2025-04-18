# callbacks/mediator_callbacks.py
import dash
from dash import Output, Input, State, html, dcc, callback_context, no_update
import dash_bootstrap_components as dbc
from utils.data_manager import load_mediators, save_mediators # Importa funzioni specifiche
from utils.helpers import create_persistent_alert
import config

def register_mediator_callbacks(app):

    # Callback per aggiornare la lista visualizzata quando serve
    # Usiamo refresh-signal-store come trigger generico
    @app.callback(
        Output("mediators-list-group", "children"),
        Input("refresh-signal-store", "data"), # Triggerato da refresh generico
        State("active-view-store", "data") # Esegui solo se la vista è 'mediatori'
    )
    def update_mediator_list_display(refresh_signal, active_view):
        if active_view != 'mediatori':
            return no_update # Non aggiornare se non siamo nella vista giusta

        print("DEBUG: update_mediator_list_display triggered")
        mediators = load_mediators()
        list_items = []
        if not mediators:
            list_items.append(dbc.ListGroupItem("Nessun mediatore definito.", color="info"))
        else:
            for med in mediators:
                list_items.append(dbc.ListGroupItem(
                    [
                        med,
                        dbc.Button(html.I(className="bi bi-trash"),
                                   id={'type': 'btn-delete-mediator', 'index': med},
                                   color="danger", size="sm", className="float-end", title=f"Elimina {med}")
                    ], className="d-flex justify-content-between align-items-center"
                ))
        return list_items

    # Callback per aggiungere un nuovo mediatore
    @app.callback(
        [Output("gestisci-mediatori-feedback", "children"),
         Output("new-mediator-input", "value"),
         Output('refresh-signal-store', 'data', allow_duplicate=True)], # Triggera aggiornamento lista
        Input("btn-add-mediator", "n_clicks"),
        [State("new-mediator-input", "value"),
         State("login-status-store", "data"),
         State('refresh-signal-store', 'data')],
        prevent_initial_call=True
    )
    def add_mediator(n_clicks, new_mediator_name, login_status, current_refresh):
        if not n_clicks or n_clicks == 0:
            return no_update, no_update, no_update

        user_lvl = login_status.get('level') if isinstance(login_status, dict) else None
        if user_lvl != 2:
            return dbc.Alert("Operazione non permessa.", color="danger"), no_update, no_update

        cleaned_name = new_mediator_name.strip() if new_mediator_name else None

        if not cleaned_name:
            return dbc.Alert("Inserire un nome valido per il mediatore.", color="warning"), cleaned_name, no_update

        if cleaned_name == config.MEDIATOR_SPECIAL_OPTION:
             return dbc.Alert(f"'{config.MEDIATOR_SPECIAL_OPTION}' è un'opzione riservata.", color="warning"), cleaned_name, no_update

        mediators = load_mediators()

        if cleaned_name in mediators:
            return dbc.Alert(f"Il mediatore '{cleaned_name}' esiste già.", color="info"), "", no_update
        else:
            mediators.append(cleaned_name)
            save_mediators(mediators) # Salva la lista aggiornata
            new_refresh = (current_refresh or 0) + 1
            feedback = create_persistent_alert(f"Mediatore '{cleaned_name}' aggiunto con successo.", "success")
            return feedback, "", new_refresh

    # Callback per eliminare un mediatore
    @app.callback(
        [Output("gestisci-mediatori-feedback", "children", allow_duplicate=True),
         Output('refresh-signal-store', 'data', allow_duplicate=True)],
        Input({'type': 'btn-delete-mediator', 'index': dash.ALL}, 'n_clicks'),
        [State("login-status-store", "data"),
         State('refresh-signal-store', 'data')],
        prevent_initial_call=True
    )
    def delete_mediator(n_clicks_list, login_status, current_refresh):
        triggered_id = callback_context.triggered_id
        if not triggered_id or not isinstance(triggered_id, dict) or not callback_context.triggered[0]['value']:
            return no_update, no_update

        user_lvl = login_status.get('level') if isinstance(login_status, dict) else None
        if user_lvl != 2:
            # Teoricamente non dovrebbe succedere, ma per sicurezza
            return create_persistent_alert("Operazione non permessa.", "danger"), no_update

        mediator_to_delete = triggered_id['index']
        print(f"Attempting to delete mediator: {mediator_to_delete}")

        mediators = load_mediators()

        if mediator_to_delete in mediators:
            mediators.remove(mediator_to_delete)
            save_mediators(mediators)
            new_refresh = (current_refresh or 0) + 1
            feedback = create_persistent_alert(f"Mediatore '{mediator_to_delete}' eliminato.", "warning")
            return feedback, new_refresh
        else:
            feedback = create_persistent_alert(f"Errore: Mediatore '{mediator_to_delete}' non trovato.", "danger")
            return feedback, no_update