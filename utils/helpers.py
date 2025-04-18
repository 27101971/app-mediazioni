# utils/helpers.py
import json
import traceback
import datetime
import webbrowser
import config # Importa costanti
from pathlib import Path
import dash_bootstrap_components as dbc
import re

# --- Password Hashing Logic ---
try:
    from werkzeug.security import generate_password_hash, check_password_hash
    WERKZEUG_AVAILABLE = True
    print("INFO HELPER: Werkzeug (per hashing password) caricato correttamente.")
except ImportError:
    print("\n" + "="*60); print("ERRORE CRITICO HELPER: 'Werkzeug' non trovata!"); print("Esegui: pip install Werkzeug"); print("="*60 + "\n")
    WERKZEUG_AVAILABLE = False
    def generate_password_hash(p): return f"insicuro_{p}"
    def check_password_hash(hashed, p): return hashed == f"insicuro_{p}"

# --- PDF Generation Dependencies & Function Definition ---
try:
    from reportlab.lib.pagesizes import A4; from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.units import cm; from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT; from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
    print("INFO HELPER: ReportLab caricato.")

    def generate_mediation_request_pdf(data):
        """Genera il PDF della richiesta di mediazione."""
        if not isinstance(data, dict): return None
        print(f"DEBUG PDF: Start ID {data.get('id', 'N/A')}")
        try:
            request_date_str = data.get('data_richiesta', datetime.date.today().isoformat())
            try: folder_date_obj = datetime.date.fromisoformat(request_date_str) if request_date_str else datetime.date.today()
            except: folder_date_obj = datetime.date.today()
            day_folder_str = folder_date_obj.strftime("%Y-%m-%d"); day_folder_path = config.PDF_SAVE_DIR_BASE / day_folder_str
            day_folder_path.mkdir(parents=True, exist_ok=True)
            sanitized_service = re.sub(r'[\\/*?:"<>|]', "", str(data.get("servizio_richiedente", "s"))); req_id = data.get('id', 'X'); ts = datetime.datetime.now().strftime("%H%M%S")
            filename = f"Richiesta_{req_id}_{sanitized_service}_{ts}.pdf"; filepath = day_folder_path / filename; counter=1
            while filepath.exists(): filename = f"Richiesta_{req_id}_{sanitized_service}_{ts}_{counter}.pdf"; filepath = day_folder_path / filename; counter+=1
            doc = SimpleDocTemplate(str(filepath), pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm, leftMargin=2*cm, rightMargin=2*cm)
            styles = getSampleStyleSheet(); story = []; styles['Normal'].fontSize=9; styles['h1'].fontSize=14; styles['h2'].fontSize=10; styles['Italic'].fontSize=8
            styles.add(ParagraphStyle(name='HeaderNormal', parent=styles['Normal'], spaceAfter=2, leading=11))
            styles.add(ParagraphStyle(name='OxfamInfo', parent=styles['Normal'], fontSize=7.5, leading=9, spaceAfter=1, leftIndent=3, rightIndent=3))
            styles.add(ParagraphStyle(name='TableCellValue', parent=styles['Normal'], alignment=TA_LEFT, fontName='Helvetica-Bold'))
            def create_field_row(label, value, label_width, value_width, styles_dict):
                 label_p = Paragraph(label, styles_dict['Normal']); value_str = str(value) if value is not None else ''
                 value_p = Paragraph(value_str.replace('\n', '<br/>'), styles_dict['TableCellValue'])
                 return Table([[label_p, value_p]], colWidths=[label_width, value_width], style=TableStyle([('BOX', (1, 0), (1, 0), 0.5, colors.black),('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),('LEFTPADDING', (0, 0), (-1, -1), 3),('RIGHTPADDING', (0, 0), (-1, -1), 3),('BOTTOMPADDING', (0, 0), (-1, -1), 3),('TOPPADDING', (0, 0), (-1, -1), 3)]))
            header_txt = [Paragraph("Azienda Sanitaria Toscana Sud Est", styles['h2']), Paragraph("via Curtatone, 54 - 52100 Arezzo", styles['HeaderNormal']), Paragraph("P.I. e C.F. 02236310518 – tel. 0575 2551 - www.uslsudest.toscana.it", styles['HeaderNormal']), Paragraph("email: ausltoscanasudest@postacert.toscana.it", styles['HeaderNormal'])]
            logo_w = config.LOGO_WIDTH_CM * cm; logo_h = float(config.LOGO_HEIGHT_CM) * cm if config.LOGO_HEIGHT_CM else None; logo_cont = []
            logo_path = config.LOGO_PATH
            if logo_path.exists():
                 try: img = Image(str(logo_path), width=logo_w, height=logo_h); img.hAlign = 'RIGHT'; logo_cont.append(img)
                 except Exception as e: print(f"Err logo: {e}"); logo_cont.append(Paragraph("(Logo err)", styles['Italic']))
            else: logo_cont.append(Paragraph("(Logo mancante)", styles['Italic']))
            total_w = A4[0] - 4*cm; logo_col_w = logo_w + 0.5*cm; text_col_w = total_w - logo_col_w
            header_tbl = Table([[header_txt, logo_cont]], colWidths=[text_col_w, logo_col_w], style=TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0)]))
            story.append(header_tbl); story.append(Spacer(1, 0.7*cm))
            main_title = Paragraph("<b>Richiesta di MEDIAZIONE LINGUISTICO CULTURALE</b>", styles['h1'])
            oxfam_info_content = [Paragraph(t, styles['OxfamInfo']) for t in ["<b>A: Oxfam Italia Intercultura</b>", "Mail: servizi.mediazione@oxfam.it (Arezzo)", "Lun – Ven 8.00 – 17.00 Tel 0575 907826 388 6422820", "Lun – Ven 17.00 – 20.00 Tel. 344 2031681", "Prefestivi / festivi 8.00 – 20.00"]]
            oxfam_w = total_w * 0.38; title_w = total_w - oxfam_w
            title_tbl = Table([[main_title, oxfam_info_content]], colWidths=[title_w, oxfam_w], style=TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (0,0), (0,0), 'CENTER'), ('BOX', (1,0), (1,0), 0.5, colors.grey), ('LEFTPADDING', (1,0), (1,0), 4), ('RIGHTPADDING', (1,0), (1,0), 4), ('TOPPADDING', (1,0), (1,0), 4), ('BOTTOMPADDING', (1,0), (1,0), 4)]))
            story.append(title_tbl); story.append(Spacer(1, 0.5*cm))
            lbl_w = 4.5 * cm; val_w = total_w - lbl_w
            story.append(create_field_row("data richiesta", format_date_italian(data.get('data_richiesta', '')), lbl_w, val_w, styles)); story.append(Spacer(1, 0.1*cm))
            rich_usr = f"({data.get('richiedente_username', 'N/D')})" if data.get('richiedente_username') else ""
            srv_fields = [("Servizio richiedente", data.get('servizio_richiedente')), ("indirizzo", data.get('indirizzo_servizio')), ("operatore richiedente", f"{data.get('nome_operatore_richiedente','')} {rich_usr}".strip())]
            for lbl, val in srv_fields: story.append(create_field_row(lbl, val, lbl_w, val_w, styles)); story.append(Spacer(1, 0.1*cm))
            lbl_sm, val_sm, lbl_ln = 3.5*cm, 4.5*cm, 1.5*cm; val_ln = total_w - lbl_sm - val_sm - lbl_ln
            gg_pdf = format_date_italian(data.get('giorno_concordato', '')); ora = str(data.get('orario_concordato', '') or ''); gg_ora = f"{gg_pdf} ore {ora}" if gg_pdf or ora else ""; lingua = str(data.get('lingua_richiesta', '') or '')
            dtl_tbl = Table([[Paragraph("giorno/orario", styles['Normal']), Paragraph(gg_ora, styles['TableCellValue']), Paragraph("lingua", styles['Normal']), Paragraph(lingua, styles['TableCellValue'])]], colWidths=[lbl_sm, val_sm, lbl_ln, val_ln], style=TableStyle([('BOX', (1,0), (1,0), 0.5, colors.black), ('BOX', (3,0), (3,0), 0.5, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (2,0), (2,0), 'RIGHT'), ('LEFTPADDING', (0,0), (-1,-1), 3), ('RIGHTPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3), ('TOPPADDING', (0,0), (-1,-1), 3)]))
            story.append(dtl_tbl); story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph("<b>ATTESTAZIONE PRESTAZIONE AVVENUTA</b>", styles['h2'])); story.append(Spacer(1, 0.3*cm))
            att_l_w, att_g_w = 1.5*cm, 0.5*cm; att_b_w = (total_w - (att_l_w * 3) - (att_g_w * 2)) / 3
            att_data_t = [[Paragraph("In data", styles['Normal']), Spacer(0,0), Paragraph("dalle ore", styles['Normal']), Spacer(0,0), Paragraph("alle ore", styles['Normal']), Spacer(0,0)]]
            table_att_t = Table(att_data_t, colWidths=[att_l_w, att_b_w, att_g_w+att_l_w, att_b_w, att_g_w+att_l_w, att_b_w], style=TableStyle([('BOX', (1,0), (1,0), 0.5, colors.black), ('BOX', (3,0), (3,0), 0.5, colors.black), ('BOX', (5,0), (5,0), 0.5, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (2,0), (2,0), 'RIGHT'), ('ALIGN', (4,0), (4,0), 'RIGHT'), ('BOTTOMPADDING', (0,0), (-1,-1), 4), ('TOPPADDING', (0,0), (-1,-1), 4)]))
            story.append(table_att_t); story.append(Spacer(1, 0.2*cm)); story.append(Paragraph("Note (compilazione manuale)", styles['Normal']))
            table_att_n = Table([[Paragraph("", styles['Normal'])]], colWidths=[total_w], rowHeights=[1.5*cm], style=TableStyle([('BOX', (0,0), (0,0), 0.5, colors.black), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
            story.append(table_att_n); story.append(Spacer(1, 0.2*cm))
            pat_lbl_w = lbl_w + 1*cm; pat_val_w = total_w - pat_lbl_w
            pat_fields = {"Nazionalità": data.get('nazionalita_paziente'), "Età": data.get('eta_paziente')}
            for lbl, val in pat_fields.items(): story.append(create_field_row(f"{lbl} paziente", val, pat_lbl_w, pat_val_w, styles)); story.append(Spacer(1, 0.1*cm))
            sesso = data.get('sesso_paziente', 'ND'); chk = "[X]"; unchk = "[ ]"; sesso_m = f"{chk if sesso=='M' else unchk} M"; sesso_f = f"{chk if sesso=='F' else unchk} F"; sesso_nd = f"{chk if sesso not in ['M', 'F'] else unchk} ND"; sesso_txt = f"{sesso_m} {sesso_f} {sesso_nd}"
            sex_tbl = Table([[Paragraph("Sesso:", styles['Normal']), Paragraph(sesso_txt, styles['Normal'])]], colWidths=[pat_lbl_w, pat_val_w], style=TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 4), ('TOPPADDING', (0,0), (-1,-1), 4)]))
            story.append(sex_tbl); story.append(Spacer(1, 0.1*cm))
            notes_r = data.get('note_richiesta', ''); story.append(Paragraph("Note (richiesta):", styles['Normal']))
            notes_c = Paragraph(notes_r.replace('\n', '<br/>') if notes_r else "<i>Nessuna.</i>", styles['Normal'])
            notes_tbl = Table([[notes_c]], colWidths=[total_w], rowHeights=[2.5*cm], style=TableStyle([('BOX', (0,0), (0,0), 0.5, colors.black), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 4), ('TOPPADDING', (0,0), (-1,-1), 4)]))
            story.append(notes_tbl); story.append(Spacer(1, 0.5*cm))
            sig_lbl_w = lbl_w + 3*cm; sig_val_w = total_w - sig_lbl_w; med_n = data.get("mediatore_assegnato", ""); current_status = data.get("stato")
            mediator_display_value = config.STATUS_PERCORSI if current_status == config.STATUS_PERCORSI else med_n
            print(f"DEBUG PDF ID {data.get('id')}: Stato '{current_status}', Mostrando mediatore: '{mediator_display_value}'")
            sig_flds = [("Mediatore prestazione", mediator_display_value), ("Operatore attestante", "")]
            for lbl, val in sig_flds: story.append(create_field_row(lbl, val, sig_lbl_w, sig_val_w, styles)); story.append(Spacer(1, 0.1*cm))
            story.append(Spacer(1, 1.5*cm)); sig_ln = "_" * 35; sig_w = (total_w - 1*cm) / 2
            sig_data = [[Paragraph("Firma Mediatore", styles['Normal']), Paragraph("Firma operatore ASL", styles['Normal'])], [Paragraph(sig_ln, styles['Normal']), Paragraph(sig_ln, styles['Normal'])]]
            sig_tbl = Table(sig_data, colWidths=[sig_w, sig_w], style=TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('TOPPADDING', (0,1), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,0), 0)]))
            story.append(sig_tbl); story.append(Spacer(1, 0.5*cm)); story.append(Paragraph("<i>N.B.: firma ASL necessaria per attestare.</i>", styles['Italic']))

            doc.build(story); rel_path = filepath.relative_to(config.PDF_SAVE_DIR_BASE).as_posix()
            print(f"DEBUG PDF: OK '{filepath}' ('{rel_path}')"); return rel_path
        except Exception as e: print(f"ERRORE PDF ID {data.get('id', 'N/A')}: {e}"); traceback.print_exc(); return None

# --- CORREZIONE QUI ---
# Rimosso il blocco elif, il fallback è definito nel blocco except sopra
except ImportError:
    print("ERROR: 'reportlab' non trovato.")
    REPORTLAB_AVAILABLE = False
    # Definisci placeholder DENTRO except
    def generate_mediation_request_pdf(data):
        print("DEBUG: generate_mediation_request_pdf (placeholder) chiamata.")
        return None
# --- FINE CORREZIONE ---

# --- User Loading ---
def load_users():
    """Carica gli utenti dal file JSON."""
    if not config.USERS_FILE.exists(): print(f"ATTENZIONE: File utenti '{config.USERS_FILE}' non trovato."); return {}
    try:
        with open(config.USERS_FILE, 'r', encoding='utf-8') as f: users = json.load(f)
        if not isinstance(users, dict): print(f"ERRORE: '{config.USERS_FILE}' non dizionario."); return {}
        valid_users = {}; ignored_count = 0
        for username, data in users.items():
            if isinstance(data, dict) and 'hashed_password' in data and 'level' in data and data['level'] in [1, 2]:
                 data.setdefault('nome_reparto', username); valid_users[username] = data
            else: print(f"AVVISO: Dati user '{username}' non validi."); ignored_count += 1
        if ignored_count > 0: print(f"ATTENZIONE: {ignored_count} utenti ignorati.")
        print(f"DEBUG: Caricati {len(valid_users)} utenti validi."); return valid_users
    except json.JSONDecodeError: print(f"ERRORE: Decode JSON fallito '{config.USERS_FILE}'."); return {}
    except Exception as e: print(f"Errore caricamento utenti '{config.USERS_FILE}': {e}"); traceback.print_exc(); return {}

# --- Date Formatting ---
def format_date_italian(date_input):
    """Formatta una data in formato italiano DD/MM/YYYY."""
    if not date_input: return ""
    try:
        if isinstance(date_input, datetime.date): date_obj = date_input
        elif isinstance(date_input, str): date_obj = datetime.date.fromisoformat(date_input.split('T')[0])
        else: date_obj = datetime.date.fromisoformat(str(date_input).split('T')[0])
        return date_obj.strftime('%d/%m/%Y')
    except: return str(date_input) # Fallback

# --- Alert Helper ---
def create_persistent_alert(message, color):
    return dbc.Alert(message, color=color, is_open=True, duration=None, dismissable=True)

# --- Browser Opener ---
def open_browser():
     url = f"http://{config.DEFAULT_HOST}:{config.DEFAULT_PORT}"
     print(f"Attempting to open browser at: {url}")
     try: webbrowser.open(url); print("Browser open command sent.")
     except Exception as e: print(f"Could not auto-open browser: {e}")