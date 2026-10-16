"""Amortissements linéaire / dégressif, VNC, simulation d'acquisition (logique IAS 16, base mensuelle)."""
from datetime import date
import pandas as pd

COEF = {3: 1.25, 4: 1.25, 5: 1.75, 6: 1.75}  # coefficients dégressifs usuels (>6 ans : 2,25)

def coef(duree): return COEF.get(int(duree), 2.25)

def schedule(cout, duree, methode, vr=0.0):
    """VNC après chaque mois (liste de longueur duree*12 + 1)."""
    n, vnc, out = int(duree * 12), float(cout), [float(cout)]
    taux_m = 1 - (1 - coef(duree) / duree) ** (1 / 12)  # taux mensuel équivalent au taux annuel
    for m in range(n):
        lin = (vnc - vr) / (n - m)
        dot = lin if methode == "lineaire" else max(vnc * taux_m, lin)
        vnc = max(vr, vnc - dot); out.append(vnc)
    return out

def months_elapsed(acq, at):
    return max(0, (at.year - acq.year) * 12 + at.month - acq.month)

def vnc_at(r, at):
    s = schedule(r.cout_acquisition, r.duree_ans, r.methode, r.valeur_residuelle)
    return s[min(months_elapsed(pd.to_datetime(r.date_acquisition).date(), at), len(s) - 1)]

def enrich(a, as_of=None):
    at = as_of or date.today()
    a = a.copy()
    a["vnc"] = a.apply(lambda r: round(vnc_at(r, at), 0), axis=1)
    start = date(at.year - 1, 12, 31)
    prev = a.apply(lambda r: vnc_at(r, start) if pd.to_datetime(r.date_acquisition).date() <= start else r.cout_acquisition, axis=1)
    a["amort_cumule"] = a.cout_acquisition - a.vnc
    a["dotation_exercice"] = (prev - a.vnc).clip(lower=0).round(0)
    a["age_ans"] = a.date_acquisition.map(lambda d: round((at - pd.to_datetime(d).date()).days / 365, 1))
    return a

def simulate(cout, duree, methode, vr=0.0):
    """Plan d'amortissement annuel d'une acquisition envisagée."""
    s = schedule(cout, duree, methode, vr)
    return pd.DataFrame([dict(annee=y, dotation=round(s[(y - 1) * 12] - s[y * 12]), vnc_fin=round(s[y * 12]))
                         for y in range(1, int(duree) + 1)])

def kpis(v):
    return dict(nb=len(v), cout=v.cout_acquisition.sum(), vnc=v.vnc.sum(), dotation=v.dotation_exercice.sum(),
                taux_usure=(v.amort_cumule.sum() / v.cout_acquisition.sum()) if len(v) else 0)
