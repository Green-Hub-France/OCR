# src/ui.py

import io
import base64
import zipfile
import logging

import streamlit as st
import streamlit.components.v1 as components  # nécessaire pour components.html
from PIL import Image
import pandas as pd
from .config import STREAMLIT_PAGE_TITLE, STREAMLIT_LAYOUT
from .i18n import t
from .preprocessing import preprocess
from .ocr import ocr_tess, find_best_zoom
from .textract_service import textract_parse
from .observability import record_request
from .alerting import send_alert
from .history import record_entry, update_entry, get_history
from .auth import check_credentials

logger = logging.getLogger(__name__)

@st.cache_data(show_spinner=False)
def load_pdf_page(file_bytes: bytes, page_number: int = 0) -> Image.Image:
    import fitz
    try:
        doc = fitz.open(stream=file_bytes, filetype='pdf')
        page = doc.load_page(page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        mode = 'RGB' if pix.n < 4 else 'RGBA'
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        return img.convert('RGB')
    except Exception:
        st.error(t("pdf_load_error", "fr"))
        st.stop()

def app():
    # Configuration de la page
    st.set_page_config(page_title=STREAMLIT_PAGE_TITLE, layout=STREAMLIT_LAYOUT)

        # --- AUTHENTIFICATION ---
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.title("🔒 Connexion")
        username = st.text_input("Utilisateur")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            if check_credentials(username, password):
                st.session_state["username"] = username
                st.session_state["logged_in"] = True
                # Relance l'application pour refléter l'état connecté
                try:
                    st.experimental_rerun()
                except AttributeError:
                    st.success("Connexion réussie ! Veuillez rafraîchir la page manuellement.")
                    st.stop()
            else:
                st.error("Utilisateur ou mot de passe incorrect")
        return

    # Après connexion
    st.sidebar.success(f"Connecté en tant que {st.session_state['username']}")
    if st.sidebar.button("Déconnexion"):
        for key in ["logged_in", "username"]:
            st.session_state.pop(key, None)
        st.experimental_rerun()

    # CSS pour boutons verts
    st.markdown("""
        <style>
        [data-testid="stDownloadButton"] button {
            background-color: #28a745;
            color: white;
            border: none;
        }
        </style>
    """, unsafe_allow_html=True)

    st.image("logo.png", width=150)
    st.title("OCR - Green Hub")

    # Sélecteur de langue
    ui_lang = st.sidebar.selectbox(
        "Lang / Langue", ["fr", "en"],
        format_func=lambda x: "Français" if x == "fr" else "English"
    )

    # Formulaire de configuration
    with st.sidebar.form(key="config_form"):
        st.header(t("config_header", ui_lang))
        lang = st.text_input(
            t("lang_label", ui_lang), "fra+eng",
            help=t("lang_help", ui_lang)
        )
        conf_thr = st.slider(
            t("conf_label", ui_lang), 0, 100, 30,
            help=t("conf_help", ui_lang)
        )
        psm = st.selectbox(
            t("psm_label", ui_lang), [3, 6, 11], index=1,
            help=t("psm_help", ui_lang)
        )
        auto_zoom = st.checkbox(
            t("auto_zoom_label", ui_lang), True,
            help=t("auto_zoom_help", ui_lang)
        )
        st.form_submit_button(t("validate", ui_lang))

    st.sidebar.markdown("---")

    # Création des onglets
    tab1, tab2, tab3 = st.tabs([
        t("tab_single", ui_lang),
        t("tab_batch", ui_lang),
        t("tab_history", ui_lang)
    ])

    # --- Onglet 1 : Test unique ---
    with tab1:
        file = st.file_uploader(
            t("single_uploader", ui_lang),
            type=["png", "jpg", "jpeg", "tiff", "pdf"],
            key="single"
        )
        if file:
            # Enregistrement en historique
            task_tex = f"textract-single-{file.name}"
            task_ocr = f"ocr-single-{file.name}"
            record_entry(file.name, task_tex)
            record_entry(file.name, task_ocr)

            raw = file.read()
            if file.name.lower().endswith('.pdf'):
                page_idx = st.number_input(
                    t("pdf_page", ui_lang), 1, 100, 1,
                    help=t("pdf_page_help", ui_lang)
                ) - 1
                base_img = load_pdf_page(raw, page_idx)
            else:
                base_img = Image.open(io.BytesIO(raw)).convert('RGB')
                w, h = base_img.size
                base_img = base_img.resize((w * 2, h * 2), Image.LANCZOS)

            # Textract
            if st.button(t("analyze_tex", ui_lang), key="tex1"):
                buf = io.BytesIO()
                base_img.save(buf, format='PNG')
                kv_list = record_request('textract', textract_parse, buf.getvalue())
                update_entry(task_tex, {"service": "textract", "result": kv_list})

                kv_list = [i for i in kv_list if i.get('conf', 0.0) >= conf_thr]
                df_kv = pd.DataFrame(kv_list)
                st.subheader(t("res_tex", ui_lang))
                st.dataframe(df_kv)
                if not df_kv.empty:
                    st.success(f"{len(df_kv)} champs · Conf moy : {df_kv['conf'].mean():.1f}%")
                else:
                    st.error(t("no_fields", ui_lang))

            # OCR
            if st.button(t("go_ocr", ui_lang), key="ocr1"):
                with st.spinner(t("ocr_spinner", ui_lang)):
                    if auto_zoom:
                        z, cnt, mc, df_res, proc_img, summary = record_request(
                            'ocr', find_best_zoom,
                            base_img, lang, psm, conf_thr,
                            preprocess, ocr_tess
                        )
                        st.subheader(t("zoom_summary", ui_lang))
                        st.dataframe(summary)
                    else:
                        proc_img = preprocess(base_img)
                        df_res = record_request('ocr', ocr_tess, proc_img, lang, psm, conf_thr)
                        cnt = len(df_res)
                        mc = df_res['conf'].mean() if cnt else 0.0
                        st.write(f"{t('ocr_stats', ui_lang)} {mc:.1f}% · {cnt} lignes")

                update_entry(task_ocr, {"service": "ocr", "result": df_res.to_dict('records')})

                if not df_res.empty:
                    st.subheader(t("ocr_results", ui_lang))
                    st.dataframe(df_res)
                    st.success(f"{cnt} lignes · Conf : {mc:.1f}%")

    # --- Onglet 2 : Batch Textract ---
    with tab2:
        files = st.file_uploader(
            t("batch_uploader", ui_lang),
            type=["png", "jpg", "jpeg", "tiff", "pdf"],
            accept_multiple_files=True,
            key="batch"
        )
        if files:
            summary = []
            all_kv = []
            progress = st.progress(0)
            total = len(files)
            for idx, f in enumerate(files):
                task_id = f"textract-batch-{f.name}"
                record_entry(f.name, task_id)

                raw = f.read()
                if f.name.lower().endswith('.pdf'):
                    img = load_pdf_page(raw)
                else:
                    img = Image.open(io.BytesIO(raw)).convert('RGB')

                buf = io.BytesIO()
                img.save(buf, format='PNG')
                kv_list = record_request('textract', textract_parse, buf.getvalue())
                update_entry(task_id, {"service": "batch-textract", "result": kv_list})

                kv_list = [i for i in kv_list if i.get('conf', 0.0) >= conf_thr]
                cnt = len(kv_list)
                avg = round(sum(i.get('conf', 0.0) for i in kv_list) / cnt, 1) if cnt else 0.0
                summary.append({'fichier': f.name, 'nb_champs': cnt, 'conf_moy': avg})
                all_kv.append((f.name, kv_list))
                progress.progress((idx + 1) / total)

            df_sum = pd.DataFrame(summary)
            st.subheader(t("batch_summary", ui_lang))
            st.dataframe(df_sum)
            st.success(f"{len(files)} fichiers traités")

            # Téléchargement ZIP automatique
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for fname, kv_list in all_kv:
                    df = pd.DataFrame(kv_list)
                    zipf.writestr(f"{fname.replace(' ', '_')}.csv", df.to_csv(index=False).encode('utf-8-sig'))
            b64zip = base64.b64encode(buffer.getvalue()).decode()
            components.html(
                f"<a id='dl-batch' href='data:application/zip;base64,{b64zip}' "
                f"download='batch_textract.zip'></a>"
                "<script>document.getElementById('dl-batch').click();</script>",
                height=0, width=0
            )

            st.subheader(t("details", ui_lang))
            for fname, kv_list in all_kv:
                with st.expander(fname):
                    df = pd.DataFrame(kv_list)
                    if not df.empty:
                        st.dataframe(df)
                        st.success(f"{len(df)} champs pour {fname}")
                    else:
                        st.error(t("no_fields_file", ui_lang))

    # --- Onglet 3 : Historique ---
    with tab3:
        st.subheader(t("history", ui_lang))
        history = get_history()
        if history:
            df_hist = pd.DataFrame(history)
            st.dataframe(df_hist)
            csv = df_hist.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                t("history_download", ui_lang),
                csv,
                "history.csv",
                "text/csv"
            )
            for entry in history:
                fname = entry.get("filename", "—")
                status = entry.get("status", "—")
                with st.expander(f"{fname} — {status}"):
                    st.json(entry.get("result", {}))
        else:
            st.info(t("no_history", ui_lang))
