import os
from datetime import date
import pandas as pd, plotly.express as px, streamlit as st
from dotenv import load_dotenv
load_dotenv()
from core import agents, db, llm, ui
from core.finance import kpis, simulate
from core.maintenance import analyse
from core.matching import run_matching, summary, OK, PROB, KO
from core.reports import to_excel, to_pdf

st.set_page_config(page_title=os.getenv("APP_NAME", "Sira-Assets AI"), page_icon="assets/logo.jpg", layout="wide")
ui.css()
db.init_db()
fcfa = lambda x: f"{x:,.0f}".replace(",", " ")

@st.cache_data(show_spinner=False)
def data(stamp): return db.load("v_actifs"), db.load("maintenance")
if "stamp" not in st.session_state: st.session_state.stamp = 0
V, M = data(st.session_state.stamp)
st.session_state.setdefault("seuil", 0.6)
reco = analyse(V, M, st.session_state.seuil)
nb_rempl, nb_surv = (reco.recommandation == "Remplacer (CapEx)").sum(), (reco.recommandation == "Surveiller").sum()

st.sidebar.image("assets/logo.jpg", width="stretch")
st.sidebar.markdown("### Sira-Assets AI")
page = st.sidebar.radio("Modules", ["🏠 Accueil", "📊 Tableau de bord", "🔄 Matching & Rapprochement", "💰 CapEx / OpEx", "🤖 Copilote IA", "📋 Rapports", "⚙️ Paramètres"], label_visibility="collapsed")
st.sidebar.caption(("🟢 LLM Groq actif" if llm.available() else "🟠 Mode hors-ligne (règles) — ajoutez GROQ_API_KEY"))

ui.ticker([("OPTIMISATION", f"{nb_rempl} actifs dépassent le seuil OpEx : budget CapEx à arbitrer.", False),
           ("PATRIMOINE", f"{len(V)} immobilisations suivies · VNC totale {fcfa(V.vnc.sum())} FCFA.", False),
           ("ALERTE", f"{nb_surv} équipements à surveiller avant fin de vie.", True),
           ("AUTOMATION", "Rapprochement automatique : l'inventaire terrain contre le grand livre en quelques minutes.", False),
           ("CONFORMITÉ", "Calculs alignés IFRS / IAS 16 — traçabilité COBAC.", False)])

if page.startswith("🏠"):
    ui.hero([("Rapprochement", "Des semaines de pointage réduites à quelques minutes", "Chargez le comptage terrain : l'Agent d'Audit apparie chaque ligne au grand livre et isole les écarts."),
             ("Pilotage", "Interrogez votre patrimoine comme vous parleriez à un collègue", "Posez vos questions en français : amortissements, VNC, coûts de réparation — réponse chiffrée et vérifiable."),
             ("CapEx / OpEx", "Renouveler au bon moment, ni trop tôt ni trop tard", "Dès que la maintenance coûte plus que l'actif ne vaut, Sira-Assets AI recommande le remplacement."),
             ("Conformité", "IFRS / IAS 16 et COBAC, dans chaque chiffre", "Des états prêts pour le comité d'audit, en PDF institutionnel et Excel."),
             ("Panafricain", "Une gestion d'actifs à la hauteur de la banque panafricaine", "Plus de 95 % de précision visée, plus de 50 % de temps gagné sur le rapprochement.")])
    st.markdown("# Les avantages de l'agent IA")
    st.markdown(ui.advantages_html(), unsafe_allow_html=True)
    st.markdown("### Avant / Après")
    st.table(pd.DataFrame({"Sujet": ["Rapprochement", "Interrogation des données", "Renouvellement des équipements", "Reporting", "Calcul des amortissements"],
                           "Avant (Excel + PGI)": ["Pointage manuel, plusieurs semaines", "Extractions et filtres manuels", "Réactif, OpEx imprévu", "Tableaux statiques, clôtures tardives", "Modèles Excel fragiles"],
                           "Avec Sira-Assets AI": ["Matching flou automatique + validation", "Question en français → réponse + SQL", "Seuil OpEx/VNC et budget CapEx chiffré", "PDF & Excel en un clic", "Moteur linéaire/dégressif testé"]}).set_index("Sujet"))

elif page.startswith("📊"):
    st.markdown("# Tableau de bord global")
    c1, c2, c3 = st.columns(3)
    z = c1.multiselect("Zone", sorted(V.zone.unique())); cat = c2.multiselect("Catégorie", sorted(V.categorie.unique()))
    vet = c3.slider("Âge maximal (ans)", 0.0, float(V.age_ans.max()), float(V.age_ans.max()))
    f = V[(V.zone.isin(z) if z else True) & (V.categorie.isin(cat) if cat else True) & (V.age_ans <= vet)]
    k = kpis(f); a, b, c, d = st.columns(4)
    a.metric("Actifs", fcfa(k["nb"])); b.metric("Coût d'acquisition (FCFA)", fcfa(k["cout"])); c.metric("VNC (FCFA)", fcfa(k["vnc"])); d.metric("Dotation de l'exercice", fcfa(k["dotation"]))
    l, r = st.columns(2)
    g = f.groupby("categorie")[["cout_acquisition", "vnc"]].sum().reset_index().melt("categorie")
    l.plotly_chart(px.bar(g, x="categorie", y="value", color="variable", barmode="group", color_discrete_sequence=ui.PALETTE, title="Coût vs VNC par catégorie", labels={"value": "FCFA", "categorie": "", "variable": ""}), width="stretch")
    r.plotly_chart(px.pie(f.groupby("zone").vnc.sum().reset_index(), names="zone", values="vnc", hole=.55, color_discrete_sequence=ui.PALETTE, title="VNC par zone"), width="stretch")
    st.plotly_chart(px.histogram(f, x="age_ans", nbins=20, color="categorie", color_discrete_sequence=ui.PALETTE, title="Vétusté du parc (ans)"), width="stretch")
    st.dataframe(f.drop(columns=["id"]), width="stretch", hide_index=True)

elif page.startswith("🔄"):
    st.markdown("# Matching & Rapprochement")
    st.caption("Colonnes reconnues : libellé / désignation, n° de série, agence / localisation.")
    up = st.file_uploader("Glissez le fichier de comptage terrain (CSV ou Excel)", type=["csv", "xlsx"])
    use_demo = st.checkbox("Utiliser un comptage terrain de démonstration", value=up is None)
    c1, c2 = st.columns(2)
    t_ok = c1.slider("Seuil « Match Parfait »", 80, 100, 90); t_pr = c2.slider("Seuil « Match Probable »", 50, 90, 70)
    if st.button("Lancer le Matching Agentique"):
        try:
            field = (pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)) if up is not None else db.sample_inventory()
            with st.spinner("L'Agent d'Audit rapproche les lignes…"):
                st.session_state.match = run_matching(field, db.load("actifs"), t_ok, t_pr)
        except Exception as e: st.error(f"Échec du rapprochement : {e}")
    if "match" in st.session_state:
        res, s = st.session_state.match, summary(st.session_state.match)
        a, b, c, d = st.columns(4)
        a.metric("Match Parfait", s["parfait"]); b.metric("Match Probable", s["probable"]); c.metric("Écarts majeurs", s["ecart"]); d.metric("Appariement auto", f"{s['taux_auto']} %")
        sel = st.multiselect("Filtrer par statut", [OK, PROB, KO], default=[PROB, KO])
        st.dataframe(res[res.statut.isin(sel)], width="stretch", hide_index=True)
        st.download_button("Télécharger le rapprochement (CSV)", res.to_csv(index=False).encode("utf-8-sig"), "rapprochement.csv", "text/csv")

elif page.startswith("💰"):
    st.markdown("# Analyse CapEx / OpEx")
    c1, c2 = st.columns(2)
    st.session_state.seuil = c1.slider("Seuil OpEx cumulé / VNC", 0.2, 1.5, st.session_state.seuil, 0.05)
    reco = analyse(V, M, st.session_state.seuil)
    a, b, c = st.columns(3)
    rem = reco[reco.recommandation == "Remplacer (CapEx)"]
    a.metric("À remplacer (CapEx)", len(rem)); b.metric("À surveiller", int((reco.recommandation == "Surveiller").sum())); c.metric("Budget CapEx estimé (FCFA)", fcfa(rem.capex_estime.sum()))
    st.plotly_chart(px.scatter(reco, x="vnc", y="opex_cumule", color="recommandation", hover_data=["code", "libelle"], color_discrete_map={"Remplacer (CapEx)": "#B42318", "Surveiller": "#D97706", "Maintenir (OpEx)": ui.BLUE}, title="OpEx cumulé vs VNC"), width="stretch")
    st.dataframe(rem[["code", "libelle", "agence", "age_ans", "vnc", "opex_cumule", "ratio_opex", "capex_estime"]], width="stretch", hide_index=True)
    st.markdown("### Simuler une acquisition")
    s1, s2, s3 = st.columns(3)
    cout = s1.number_input("Coût (FCFA)", 100000, 500_000_000, 15_000_000, 500_000); dur = s2.slider("Durée (ans)", 3, 10, 5); met = s3.selectbox("Méthode", ["lineaire", "degressif"])
    sim = simulate(cout, dur, met)
    st.plotly_chart(px.bar(sim, x="annee", y=["dotation", "vnc_fin"], barmode="group", color_discrete_sequence=[ui.LIME, ui.BLUE], labels={"value": "FCFA", "annee": "Année"}), width="stretch")
    st.dataframe(sim, hide_index=True)

elif page.startswith("🤖"):
    st.markdown("# Copilote IA")
    st.caption("Exemples : « Total des amortissements des serveurs de la zone Ouest » · « Véhicules dont les réparations dépassent 60 % de leur valeur d'origine » · « VNC par catégorie »")
    st.session_state.setdefault("chat", [])
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["text"])
            if m.get("sql"): st.expander("Requête SQL exécutée").code(m["sql"], language="sql")
            if m.get("df") is not None: st.dataframe(m["df"], width="stretch", hide_index=True)
    if q := st.chat_input("Posez votre question en français…"):
        st.session_state.chat.append({"role": "user", "text": q})
        with st.spinner("Le superviseur route votre demande…"):
            r = agents.ask(q)
        st.session_state.chat.append({"role": "assistant", "text": f"**{r['agent']}** — {r['text']}", "sql": r.get("sql"), "df": r.get("df")})
        st.rerun()

elif page.startswith("📋"):
    st.markdown("# Rapports pour le comité")
    ms = summary(st.session_state.match) if "match" in st.session_state else None
    st.write("Le rapport compile registre, VNC, recommandations CapEx" + (" et rapprochement d'inventaire." if ms else ". (Lancez un matching pour l'inclure.)"))
    if st.button("Générer le Rapport Synthétique"):
        st.session_state.pdf = to_pdf(V, reco, ms); st.session_state.xlsx = to_excel(V, reco, st.session_state.get("match"))
    if "pdf" in st.session_state:
        a, b = st.columns(2)
        a.download_button("Télécharger le PDF institutionnel", st.session_state.pdf, f"rapport_immobilisations_{date.today()}.pdf", "application/pdf")
        b.download_button("Télécharger l'Excel", st.session_state.xlsx, f"rapport_immobilisations_{date.today()}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.markdown("# Paramètres")
    st.write(f"**Modèle LLM** : `{os.getenv('LLM_MODEL', 'llama-3.3-70b-versatile')}` — {'clé détectée' if llm.available() else 'aucune clé : mode hors-ligne'}")
    st.write(f"**Base** : `{db.DB_PATH}` · {len(V)} actifs · {len(M)} tickets de maintenance")
    d = st.date_input("Date d'arrêté des comptes", date.today())
    if st.button("Recalculer VNC et amortissements"):
        db.refresh_views(d); st.session_state.stamp += 1; st.rerun()
    if st.button("Réinitialiser les données de démonstration"):
        db.init_db(force=True); st.session_state.stamp += 1; st.rerun()
