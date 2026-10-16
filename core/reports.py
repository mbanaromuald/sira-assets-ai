"""Rapports comité : Excel multi-feuilles et PDF institutionnel."""
import io
from datetime import date
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from core.finance import kpis

BLUE, LIME = colors.HexColor("#095B81"), colors.HexColor("#A6CE39")
fmt = lambda x: f"{x:,.0f}".replace(",", " ")

def to_excel(v, reco, matching=None):
    b = io.BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as w:
        pd.DataFrame([kpis(v)]).to_excel(w, sheet_name="Synthese", index=False)
        v.to_excel(w, sheet_name="Registre_VNC", index=False)
        reco.to_excel(w, sheet_name="CapEx_OpEx", index=False)
        if matching is not None: matching.to_excel(w, sheet_name="Rapprochement", index=False)
        for ws in w.book.worksheets:
            for col in ws.columns: ws.column_dimensions[col[0].column_letter].width = min(40, max(len(str(c.value or "")) for c in col[:50]) + 2)
    return b.getvalue()

def to_pdf(v, reco, msum=None, logo="assets/logo.jpg"):
    b, st = io.BytesIO(), getSampleStyleSheet()
    doc = SimpleDocTemplate(b, pagesize=A4, leftMargin=1.6*cm, rightMargin=1.6*cm, topMargin=1.4*cm, bottomMargin=1.4*cm)
    h = st["Heading2"]; h.textColor = BLUE
    head = Table([[Image(logo, 2.6*cm, 2.6*cm), Paragraph(f"<font color='white' size=16><b>Rapport synthétique des immobilisations</b></font><br/><font color='#A6CE39' size=10>Ecobank Cameroun — arrêté au {date.today():%d/%m/%Y}</font>", st["Normal"])]],
                 colWidths=[3*cm, 14*cm])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BLUE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 0), (-1, -1), 3, LIME)]))
    k, el = kpis(v), [head, Spacer(1, 14), Paragraph("Indicateurs clés (FCFA)", h)]
    def tbl(rows, widths=None):
        t = Table(rows, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BLUE), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), 8),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF4F8")]), ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#B8D4E0"))]))
        return t
    el.append(tbl([["Actifs", "Coût d'acquisition", "VNC", "Dotation exercice", "Taux d'usure"],
                   [k["nb"], fmt(k["cout"]), fmt(k["vnc"]), fmt(k["dotation"]), f"{k['taux_usure']:.0%}"]]))
    g = v.groupby("categorie").agg(nb=("id", "size"), cout=("cout_acquisition", "sum"), vnc=("vnc", "sum")).reset_index()
    el += [Spacer(1, 10), Paragraph("VNC par catégorie", h), tbl([["Catégorie", "Nb", "Coût", "VNC"]] + [[r.categorie, r.nb, fmt(r.cout), fmt(r.vnc)] for r in g.itertuples()])]
    rep = reco[reco.recommandation == "Remplacer (CapEx)"].head(15)
    el += [Spacer(1, 10), Paragraph(f"Renouvellements recommandés (CapEx) — {len(reco[reco.recommandation == 'Remplacer (CapEx)'])} actifs", h),
           tbl([["Code", "Libellé", "Agence", "VNC", "OpEx cumulé", "Ratio"]] + [[r.code, r.libelle[:34], r.agence, fmt(r.vnc), fmt(r.opex_cumule), f"{r.ratio_opex:.0%}"] for r in rep.itertuples()])]
    if msum:
        el += [Spacer(1, 10), Paragraph("Rapprochement d'inventaire", h),
               tbl([["Lignes terrain", "Match parfait", "À valider", "Écarts majeurs", "Taux auto"], [msum["terrain"], msum["parfait"], msum["probable"], msum["ecart"], f"{msum['taux_auto']}%"]])]
    el += [Spacer(1, 12), Paragraph("<font size=7 color='#666666'>Document généré par Sira-Assets AI — calculs conformes à la logique IAS 16 ; à valider par la Direction Financière.</font>", st["Normal"])]
    doc.build(el)
    return b.getvalue()
