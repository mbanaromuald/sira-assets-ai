"""Agent de maintenance prédictive : OpEx cumulé / valeur de référence -> recommandation de renouvellement."""
import pandas as pd

def analyse(v, m, seuil=0.6, base="vnc", inflation=0.03):
    cum = m.groupby("asset_id").agg(opex_cumule=("cout", "sum"), nb_tickets=("cout", "size")).reset_index()
    d = v.merge(cum, left_on="id", right_on="asset_id", how="left").fillna({"opex_cumule": 0, "nb_tickets": 0})
    ref = d.vnc.clip(lower=0.05 * d.cout_acquisition) if base == "vnc" else d.cout_acquisition
    d["ratio_opex"] = (d.opex_cumule / ref).round(3)
    d["recommandation"] = "Maintenir (OpEx)"
    d.loc[(d.ratio_opex >= seuil * .7) | (d.age_ans >= d.duree_ans * .85), "recommandation"] = "Surveiller"
    d.loc[(d.ratio_opex >= seuil) | ((d.age_ans >= d.duree_ans) & (d.ratio_opex >= seuil * .5)), "recommandation"] = "Remplacer (CapEx)"
    d["capex_estime"] = (d.cout_acquisition * (1 + inflation) ** d.age_ans).round(-3).where(d.recommandation == "Remplacer (CapEx)", 0)
    return d.sort_values("ratio_opex", ascending=False)
