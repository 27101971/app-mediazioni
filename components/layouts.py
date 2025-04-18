# components/layouts.py
import dash
from dash import html, dcc, ALL # Importato ALL
import dash_bootstrap_components as dbc
import datetime
import config # Importa costanti
from utils.helpers import format_date_italian, REPORTLAB_AVAILABLE # Importa helper
from utils.data_manager import load_requests, load_mediators # Importa funzioni dati

# --- Nuova Richiesta Form ---
def create_ricevi_form(logged_in_username=None, user_level=None, edit_data=None):
    print(f"DEBUG create_ricevi_form: User '{logged_in_username}' (L{user_level}), Edit Data Provided: {edit_data is not None}")
    today = datetime.date.today().isoformat()
    form_values = {'data_richiesta': today, 'servizio_richiedente': '', 'indirizzo_servizio': config.DEFAULT_INDIRIZZO_SERVIZIO, 'nome_operatore_richiedente': '', 'giorno_concordato': None, 'orario_concordato': '', 'lingua_richiesta': '', 'nazionalita_paziente': '', 'eta_paziente': None, 'sesso_paziente': 'ND', 'note_richiesta': ''}
    form_title = config.DEFAULT_FORM_TITLE; form_subtitle = config.DEFAULT_FORM_SUBTITLE; button_text = config.DEFAULT_SAVE_BUTTON_TEXT; local_edit_id = None

    if edit_data and isinstance(edit_data, dict) and user_level == 2:
        print(f"DEBUG create_ricevi_form: Populating form with data for ID {edit_data.get('id')}")
        local_edit_id = edit_data.get('id')
        for key, default in form_values.items(): form_values[key] = edit_data.get(key, default)
        form_title = f"Modifica Richiesta ID: {local_edit_id}"; form_subtitle = "Modifica i dettagli e salva."; button_text = "Salva Modifiche"
        print(f"DEBUG create_ricevi_form: Final values: {form_values}")
    else: print("DEBUG create_ricevi_form: Using default values for new request.")

    return dbc.Card(dbc.CardBody([
        html.H4(form_title, className="card-title", id='nr-form-title'),
        html.P(form_subtitle, id='nr-form-subtitle'),
        dcc.Store(id='edit-request-id-store-local', data=local_edit_id),
        dbc.Form([
             dbc.Row([dbc.Label("Data Richiesta*", width=2), dbc.Col(dcc.DatePickerSingle(id='nr-data-richiesta', date=form_values['data_richiesta'], display_format='DD/MM/YYYY', className="dbc w-100"), width=4)], className="mb-3"),
             dbc.Row([dbc.Label("Servizio Richiedente*", width=2), dbc.Col(dbc.Input(id="nr-servizio-richiedente", placeholder="Es. Pronto Soccorso...", value=form_values['servizio_richiedente']), width=10)], className="mb-3"),
             dbc.Row([dbc.Label("Indirizzo Servizio", width=2), dbc.Col(dbc.Input(id="nr-indirizzo-servizio", value=form_values['indirizzo_servizio']), width=10)], className="mb-3"),
             dbc.Row([dbc.Label("Operatore Richiedente*", width=2), dbc.Col(dbc.Input(id="nr-operatore-richiedente", placeholder="Nome Cognome", value=form_values['nome_operatore_richiedente']), width=10)], className="mb-3"),
             dbc.Row([dbc.Label("Giorno Concordato*", width=2), dbc.Col(dcc.DatePickerSingle(id='nr-giorno-concordato', date=form_values['giorno_concordato'], display_format='DD/MM/YYYY', className="dbc w-100"), md=3), dbc.Label("Orario*", width="auto"), dbc.Col(dbc.Input(id="nr-orario-concordato", type="time", value=form_values['orario_concordato']), md=2), dbc.Label("Lingua*", width="auto"), dbc.Col(dbc.Input(id="nr-lingua", placeholder="Es. Arabo...", value=form_values['lingua_richiesta']), md=3)], className="mb-3 align-items-center"),
             html.Hr(),
             dbc.Row([dbc.Label("Nazionalità Paziente", width=2), dbc.Col(dbc.Input(id="nr-nazionalita", value=form_values['nazionalita_paziente']), md=4), dbc.Label("Età", width="auto"), dbc.Col(dbc.Input(id="nr-eta", type="number", min=0, step=1, value=form_values['eta_paziente']), md=1), dbc.Label("Sesso", width="auto"), dbc.Col(dbc.RadioItems(id="nr-sesso", options=[{"label":l,"value":v} for l,v in [("M","M"),("F","F"),("ND","ND")]], value=form_values['sesso_paziente'], inline=True, className="dbc mt-1"), md=3)], className="mb-3 align-items-center"),
             dbc.Row([ dbc.Label("Note", width=2), dbc.Col(dbc.Textarea(id="nr-note", placeholder="Dettagli...", style={"height": "100px"}, value=form_values['note_richiesta']), width=10)], className="mb-3"),
             dbc.Row([ dbc.Col(width=2), dbc.Col(dbc.Button(button_text, id="btn-salva-richiesta", color="success", class_name="w-100"), width="auto", class_name="flex-grow-1"), dbc.Col(width=2)], className="mb-3"),
             dbc.Row(dbc.Col(html.Div(id="nuova-richiesta-feedback"), width=12))
        ]),
    ]), id="nuova-richiesta-card")


# --- Tabella Gestisci Richieste ---
def create_gestisci_layout(logged_in_username=None, user_level=None):
    print(f"DEBUG create_gestisci_layout: User '{logged_in_username}' (L{user_level})")
    feedback_container = html.Div(id="gestisci-feedback-alert-container"); reqs_all = load_requests(); reqs_all = reqs_all if isinstance(reqs_all, list) else []
    reqs_disp = []; view_title = "Errore Vista"; assign=False; status=False; see_med=False; see_rich=False; is_l1=False; is_l2=False
    if user_level == 1 and logged_in_username: is_l1 = True; view_title = f"2. Le Mie Richieste ({logged_in_username})"; reqs_disp = [r for r in reqs_all if isinstance(r, dict) and r.get('richiedente_username') == logged_in_username]; see_med = True
    elif user_level == 2: is_l2 = True; view_title = "2. Gestisci Tutte"; reqs_disp = reqs_all; assign=True; status=True; see_med=True; see_rich=True
    else: return dbc.Card(dbc.CardBody([html.H4("Accesso Negato"), feedback_container, dbc.Alert("Login richiesto.", color="warning")]))

    if reqs_disp:
        try: reqs_disp.sort(key=lambda r: (r.get('data_richiesta','0') or '0', r.get('id',0) or 0), reverse=True)
        except Exception as e: print(f"ERR sort: {e}")

    if not reqs_disp:
        alert_msg="Nessuna richiesta.";
        if is_l1: alert_msg="Nessuna richiesta effettuata."
        elif is_l2: alert_msg="Nessuna richiesta nel sistema."
        return dbc.Card(dbc.CardBody([html.H4(view_title), feedback_container, dbc.Alert(alert_msg, color="info")]))

    hdr_cols = [("ID",'4%'),("Data R.",'8%'),("Giorno/Ora",'10%'),("Servizio",'15%'),("Operatore",'10%'),("Lingua",'8%'),("Stato",'8%')];
    if see_med: hdr_cols.append(("Mediatore",'10%'));
    if see_rich: hdr_cols.append(("Richiedente",'10%')); hdr_cols.append(("Azioni",'17%'))
    theader = [html.Thead(html.Tr([html.Th(h, style={'width':w}) for h,w in hdr_cols]))]
    rows = []
    for req in reqs_disp:
         if not isinstance(req, dict): continue
         req_id = req.get('id','N/A'); req_user = req.get('richiedente_username','N/D'); can_del = (user_level == 2); can_req_chg = (user_level == 1 and req_user == logged_in_username); can_edit = (user_level == 2)
         pdf_path = req.get('pdf_path'); pdf_dis = not (pdf_path and REPORTLAB_AVAILABLE)
         pdf_btn = html.A(dbc.Button("PDF", color="info", size="sm", className="me-1", title="Apri PDF", disabled=pdf_dis), href=f"/download/{pdf_path}" if not pdf_dis else "#", target="_blank", **({'disabled': True} if pdf_dis else {}))
         actions = []; chg_pend = req.get('change_request_status') == config.CHANGE_REQ_PENDING
         if can_edit: actions.append(dbc.Button("Modifica", id={'type':'btn-edit-request','index':req_id}, color="primary", size="sm", className="me-1", title="Modifica (Admin)"))
         if assign: actions.append(dbc.Button("Assegna", id={'type':'btn-assign-mediator','index':req_id}, color="warning", size="sm", className="me-1"))
         if status: actions.append(dbc.Button("Stato", id={'type':'btn-change-status','index':req_id}, color="info", size="sm", className="me-1"))
         if is_l2 and chg_pend: actions.append(dbc.Button([html.I(className="bi bi-eye-fill me-1"), "Rich."], id={'type': 'btn-review-change', 'index': req_id}, color="warning", size="sm", className="me-1", title="Vedi Richiesta Mod/Ann"))
         actions.append(pdf_btn)
         if can_req_chg: actions.append(dbc.Button("Annulla/Mod", id={'type':'btn-request-change','index':req_id}, color="secondary", size="sm", className="ms-auto", title="Richiedi Mod/Ann"))
         if can_del: del_cls = "ms-auto" if not can_req_chg and len(actions)>1 else "ms-1"; actions.append(dbc.Button("Elimina", id={'type':'btn-delete-request','index':req_id}, color="danger", size="sm", className=del_cls, title="Elimina (Admin)"))
         id_cell = [str(req_id)]
         if is_l2 and chg_pend: id_cell.append(dbc.Badge("!", color="warning", pill=True, className="ms-1", title="Richiesta Mod/Ann"))
         row_data = [html.Td(id_cell), html.Td(format_date_italian(req.get('data_richiesta'))), html.Td(f"{format_date_italian(req.get('giorno_concordato'))} {req.get('orario_concordato','') or ''}".strip()), html.Td(req.get('servizio_richiedente')), html.Td(req.get('nome_operatore_richiedente')), html.Td(req.get('lingua_richiesta')), html.Td(dbc.Badge(req.get('stato','N/D'), color=config.STATUS_COLORS.get(req.get('stato'),"light")))]
         if see_med: row_data.append(html.Td(req.get('mediatore_assegnato','---')))
         if see_rich: row_data.append(html.Td(req_user))
         row_data.append(html.Td(actions, className="text-nowrap d-flex"))
         rows.append(html.Tr(row_data, id=f"request-row-{req_id}"))
    tbody = [html.Tbody(rows, id="gestisci-tbody")]
    return dbc.Card(dbc.CardBody([html.H4(view_title), feedback_container, dbc.Alert([html.I(className="bi bi-info-circle me-2"), "Tabella ordinata."], color="light", className="d-flex align-items-center mt-2"), dbc.Table(theader + tbody, bordered=True, striped=True, hover=True, responsive=True, size="sm")]), id="gestisci-card")

# --- Lista Mediazioni del Giorno ---
def create_giorno_layout(logged_in_username=None, user_level=None):
    print(f"DEBUG create_giorno_layout: User '{logged_in_username}' (L{user_level})")
    today_iso = datetime.date.today().isoformat(); today_fmt = datetime.date.today().strftime('%d/%m/%Y'); reqs_all = load_requests(); reqs_all=reqs_all if isinstance(reqs_all, list) else []
    today_reqs = [r for r in reqs_all if isinstance(r,dict) and r.get('giorno_concordato') == today_iso]; print(f"DEBUG Giorno: {len(today_reqs)} per oggi.")
    if today_reqs:
        try: today_reqs.sort(key=lambda r: r.get('orario_concordato','99:99') or '99:99')
        except Exception as e: print(f"Err sort Giorno: {e}")
    view_title = f"3. Mediazioni Oggi ({today_fmt})";
    if user_level == 1: view_title += " - Utente"
    elif user_level == 2: view_title += " - Admin"
    if not today_reqs: return dbc.Card(dbc.CardBody([html.H4(view_title), dbc.Alert("Nessuna mediazione oggi.", color="info")]))
    items = []
    for req in today_reqs:
         req_id = req.get('id','N/A'); pdf_path = req.get('pdf_path'); pdf_dis = not (pdf_path and REPORTLAB_AVAILABLE)
         pdf_btn = html.A(dbc.Button("PDF", color="info", size="sm", className="ms-auto", disabled=pdf_dis, title="Apri PDF"), href=f"/download/{pdf_path}" if not pdf_dis else "#", target="_blank", **({'disabled': True} if pdf_dis else {}))
         rich_tag = f" | Rich: {req.get('richiedente_username', 'N/D')}" if user_level == 2 else ""
         chg_ind = [dbc.Badge("!", color="warning", pill=True, className="ms-1", title="Richiesta Mod/Ann")] if user_level == 2 and req.get('change_request_status') == config.CHANGE_REQ_PENDING else []
         items.append(dbc.ListGroupItem([ html.Div([ html.Div([ html.H5([f"{req.get('orario_concordato','N/D')} - {req.get('servizio_richiedente','N/D')} ({req.get('lingua_richiesta','N/D')})"] + chg_ind, className="mb-1 d-flex align-items-center"), html.Div([ dbc.Badge(req.get('stato','N/D'), color=config.STATUS_COLORS.get(req.get('stato'),"light"), className="me-2"), html.Small(f"ID:{req_id} | Op: {req.get('nome_operatore_richiedente','N/A')} | Med: {req.get('mediatore_assegnato','---')}{rich_tag}") ]) ]), pdf_btn ], className="d-flex w-100 justify-content-between align-items-center"), html.P(f"Note: {req.get('note_richiesta','Nessuna')}", className="mb-1 mt-2 small text-muted w-100") ]))
    return dbc.Card(dbc.CardBody([html.H4(view_title), dbc.ListGroup(items, flush=True)]))

# --- Layout Gestione Mediatori ---
def create_mediatori_layout(logged_in_username=None, user_level=None):
    print(f"DEBUG create_mediatori_layout: User '{logged_in_username}' (L{user_level})")
    if user_level != 2:
        return dbc.Card(dbc.CardBody([html.H4("Accesso Negato"), dbc.Alert("Area riservata agli amministratori.", color="danger")]))

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

    return dbc.Card(dbc.CardBody([
        html.H4("4. Gestisci Mediatori"),
        html.P("Aggiungi o rimuovi mediatori dalla lista utilizzata nel menu a tendina 'Assegna'."),
        html.Div(id="gestisci-mediatori-feedback"),
        dbc.InputGroup(
            [
                dbc.Input(id="new-mediator-input", placeholder="Nome Cognome Nuovo Mediatore", type="text", n_submit=0), # Aggiunto n_submit
                dbc.Button("Aggiungi", id="btn-add-mediator", color="success", n_clicks=0),
            ],
            className="mb-3",
        ),
        html.Hr(),
        dbc.ListGroup(id="mediators-list-group", children=list_items)
    ]))

# --- Main App Layout Definition ---
def main_layout():
    logo_exists = config.LOGO_PATH.exists()
    return dbc.Container([
        dcc.Store(id='login-status-store', storage_type='session', data=None),
        html.Div(id='login-form-div', children=[
            dbc.Row(dbc.Col(html.H1(config.APP_TITLE, className="text-center text-primary my-4"))),
            dbc.Row(dbc.Col(dbc.Card([ dbc.CardHeader("Accesso"), dbc.CardBody([dbc.Input(id="username-input", type="text", placeholder="Username", className="mb-3", n_submit=0), dbc.Input(id="password-input", type="password", placeholder="Password", className="mb-3", n_submit=0), dbc.Button("Accedi", id="login-button", color="primary", className="w-100", n_clicks=0), html.Div(id="login-feedback", className="mt-3 text-danger small")])]), width=10, md=6, lg=4), justify="center", className="mt-5"),
            dbc.Row(dbc.Col(html.Img(src=config.LOGO_WEB_PATH, style={'height': config.LOGO_HEIGHT_WEB, 'width': config.LOGO_WIDTH_WEB, 'object-fit': 'contain'}) if logo_exists else None, className="text-center"), justify="center", className="mt-4 mb-5")
        ], style={'display': 'block'}),
        html.Div(id='main-app-content', children=[
            dbc.Row([dbc.Col(html.Img(src=config.LOGO_WEB_PATH, style={'height': config.LOGO_HEIGHT_WEB, 'width': config.LOGO_WIDTH_WEB, 'object-fit': 'contain'}) if logo_exists else None, width="auto", className="d-flex align-items-center"), dbc.Col(html.H1(config.APP_TITLE, className="text-primary my-4 mb-md-0 text-center text-md-start"), width=True)], align="center", className="mb-4"),
            dbc.Row([
                dbc.Col(dbc.Button([html.I(className="bi bi-plus-circle-fill me-2"),"1. Nuova Richiesta"], id="btn-ricevi",color="primary",className="d-grid gap-2",size="lg"),md=3,className="mb-2", id="col-btn-ricevi", style={'display': 'none'}),
                dbc.Col(dbc.Button([html.I(className="bi bi-card-list me-2"),"2. Visualizza Richieste"], id="btn-gestisci",color="success",className="d-grid gap-2",size="lg"),md=3,className="mb-2", id="col-btn-gestisci", style={'display': 'none'}),
                dbc.Col(dbc.Button([html.I(className="bi bi-calendar-day me-2"),"3. Mediazioni Oggi"], id="btn-giorno",color="info",className="d-grid gap-2",size="lg"),md=3,className="mb-2", id="col-btn-giorno", style={'display': 'none'}),
                dbc.Col(dbc.Button([html.I(className="bi bi-person-badge me-2"), "4. Mediatori"], id="btn-mediatori", color="secondary", className="d-grid gap-2", size="lg"), md=3, className="mb-2", id="col-btn-mediatori", style={'display': 'none'}),
                ], className="mb-4 justify-content-center"),
            html.Hr(),
            dcc.Store(id='refresh-signal-store', data=0),
            dcc.Store(id='active-view-store', data='gestisci'),
            dcc.Store(id='edit-request-id-store', data=None),
            dbc.Row(dbc.Col(html.Div(id="contenuto-principale"))),
            # --- Modali Definite Correttamente ---
            dbc.Modal([dbc.ModalHeader(dbc.ModalTitle("Assegna Mediatore / Percorsi")),
                       dbc.ModalBody([dbc.Label("Seleziona Mediatore o 'Percorsi':"),
                                      dbc.Select(id="assign-mediator-input", options=[], value=None, placeholder="Seleziona..."), # Options caricate da callback
                                      html.Div(id="assign-modal-feedback", className="mt-2 text-danger small"),
                                      dcc.Store(id='assign-mediator-request-id-store')]),
                       dbc.ModalFooter([dbc.Button("Annulla", id="assign-mediator-cancel-btn", color="secondary"),
                                        dbc.Button("Salva Assegnazione", id="assign-mediator-save-btn", color="primary")])],
                      id="assign-mediator-modal", is_open=False),
            dbc.Modal([dbc.ModalHeader(dbc.ModalTitle("Cambia Stato")),
                       dbc.ModalBody([dbc.Label("Nuovo Stato:"),
                                      dbc.Select(id="change-status-dropdown", options=[{"label":s,"value":s} for s in config.VALID_STATUSES]),
                                      html.Div(id="change-status-modal-feedback", className="mt-2 text-danger small"),
                                      dcc.Store(id='change-status-request-id-store')]),
                       dbc.ModalFooter([dbc.Button("Annulla", id="change-status-cancel-btn", color="secondary"),
                                        dbc.Button("Salva Stato", id="change-status-save-btn", color="primary")])],
                      id="change-status-modal", is_open=False),
            dbc.Modal([dbc.ModalHeader(dbc.ModalTitle("Conferma Eliminazione")),
                       dbc.ModalBody([html.P("Eliminare questa richiesta? L'azione è irreversibile."),
                                      html.Div(id="delete-confirm-details", className="fw-bold my-2 small"),
                                      html.Div(id="delete-modal-feedback", className="mt-2 text-danger small"),
                                      dcc.Store(id='delete-request-id-store')]),
                       dbc.ModalFooter([dbc.Button("Annulla", id="delete-cancel-btn", color="secondary"),
                                        dbc.Button("Elimina Definitivamente", id="delete-confirm-btn", color="danger")])],
                      id="delete-confirm-modal", is_open=False),
            dbc.Modal([dbc.ModalHeader(dbc.ModalTitle("Richiesta Annullamento/Modifica")),
                       dbc.ModalBody([html.P("Descrivi motivo. Admin notificato."),
                                      dbc.Textarea(id="request-change-reason-input", placeholder="Es. Paziente dimesso...", required=True, style={"height": "100px"}),
                                      html.Div(id="request-change-modal-feedback", className="mt-2 text-danger small"),
                                      dcc.Store(id='request-change-id-store')]),
                       dbc.ModalFooter([dbc.Button("Annulla", id="request-change-cancel-btn", color="secondary"),
                                        dbc.Button("Invia Richiesta", id="request-change-submit-btn", color="primary")])],
                      id="request-change-modal", is_open=False),
            dbc.Modal([dbc.ModalHeader(dbc.ModalTitle("Dettagli Richiesta Mod/Ann")),
                       dbc.ModalBody([html.Div(id="review-change-request-details"),
                                      html.Hr(),
                                      html.P("Gestita la richiesta? Cancella segnalazione."),
                                      html.Div(id="review-change-modal-feedback", className="mt-2 text-danger small"),
                                      dcc.Store(id='review-change-id-store')]),
                       dbc.ModalFooter([dbc.Button("Chiudi", id="review-change-close-btn", color="secondary"),
                                        dbc.Button("Cancella Segnalazione", id="review-clear-change-btn", color="warning")])],
                      id="review-change-request-modal", is_open=False),
            # --- Fine Modali ---
            html.Footer(dbc.Container(dbc.Row(dbc.Col(html.Small(f"{config.APP_TITLE} v{config.APP_VERSION} - © {datetime.date.today().year}", className="text-muted"))), className="mt-5 py-3 text-center"))
        ], style={'display': 'none'}),
    ], fluid=True)