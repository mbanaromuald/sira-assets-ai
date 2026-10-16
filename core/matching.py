"""Agent d'audit : rapprochement flou inventaire terrain <-> registre comptable."""
import re, unicodedata
import pandas as pd
from rapidfuzz import fuzz, process

ALIAS = {"libelle": ["libelle", "libellé", "designation", "désignation", "description", "actif"],
         "numero_serie": ["numero_serie", "numéro de série", "n° série", "serie", "série", "serial"],
         "agence": ["agence", "localisation", "site", "emplacement"]}
SYN = {"srv": "serveur", "laptop": "ordinateur portable", "atm": "distributeur", "gab": "distributeur"}
OK, PROB, KO = "Match Parfait", "Match Probable (à valider)", "Écart Majeur"

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return " ".join(SYN.get(t, t) for t in re.sub(r"[^a-z0-9 ]", " ", s).split())

def standardize(df):
    low = {c.lower().strip(): c for c in df.columns}; out = pd.DataFrame(index=df.index)
    for k, names in ALIAS.items():
        col = next((low[n] for n in names if n in low), None)
        out[k] = df[col].fillna("").astype(str) if col else ""
    if not (out.libelle != "").any(): raise ValueError("Colonne de libellé introuvable (libelle / désignation / description).")
    return out

def run_matching(field, reg, thr_ok=90, thr_prob=70, scope=True):
    f = standardize(field).reset_index(drop=True)
    reg = reg.reset_index(drop=True); names = {i: norm(l) for i, l in reg.libelle.items()}
    by_sn = {s.strip().upper(): i for i, s in reg.numero_serie.items() if s}
    used, rows = {}, []
    for n, r in f.iterrows():
        sn, idx, score = r.numero_serie.strip().upper(), None, 0
        if sn and sn in by_sn: idx, score = by_sn[sn], 100
        else:
            same = {i: names[i] for i in reg.index if r.agence and reg.agence[i] == r.agence}
            best = process.extractOne(norm(r.libelle), same, scorer=fuzz.token_set_ratio) if same else None
            if best is None or best[1] < thr_prob:
                best = process.extractOne(norm(r.libelle), names, scorer=fuzz.token_set_ratio)
            if best: score, idx = best[1], best[2]
        anom = []
        if idx is not None and score >= thr_prob:
            if r.agence and reg.agence[idx] != r.agence: anom.append("Localisation différente")
            if not sn: anom.append("N° de série manquant")
            if idx in used: anom.append(f"Déjà apparié à la ligne {used[idx] + 1}")
            else: used[idx] = n
            statut = OK if score >= thr_ok and not any("Déjà" in a for a in anom) else PROB
        else:
            idx, statut, anom = None, KO, ["Aucun actif correspondant au registre"]
        g = (lambda col: reg[col][idx] if idx is not None else "")
        rows.append(dict(ligne=n + 1, libelle_terrain=r.libelle, serie_terrain=sn, agence_terrain=r.agence, code_actif=g("code"),
                         libelle_registre=g("libelle"), agence_registre=g("agence"), score=round(score, 1), statut=statut, anomalie=" ; ".join(anom)))
    res = pd.DataFrame(rows)
    rest = reg.loc[~reg.index.isin(used)]
    if scope:  # comptage partiel : on ne réclame que les actifs des agences réellement comptées (au moins 3 lignes)
        n = f.agence[f.agence != ""].value_counts()
        if len(n): rest = rest[rest.agence.isin(n[n >= 3].index)]
    gone = pd.DataFrame([dict(ligne=None, libelle_terrain="", serie_terrain="", agence_terrain="", code_actif=m.code, libelle_registre=m.libelle,
                              agence_registre=m.agence, score=0, statut=KO, anomalie="Au registre, absent du comptage terrain")
                         for _, m in rest.iterrows()])
    return pd.concat([res, gone], ignore_index=True)

def summary(res):
    c = res.statut.value_counts(); n_f = int(res.ligne.notna().sum())
    return dict(total=len(res), terrain=n_f, parfait=int(c.get(OK, 0)), probable=int(c.get(PROB, 0)), ecart=int(c.get(KO, 0)),
                absents=int(res.anomalie.str.startswith("Au registre").sum()),
                taux_auto=round(100 * (c.get(OK, 0) + c.get(PROB, 0)) / max(n_f, 1), 1))
