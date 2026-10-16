"""Orchestration multi-agents (LangGraph) : superviseur -> données/finance | maintenance | audit."""
import re, unicodedata
from typing import TypedDict
import pandas as pd
from core import db, llm
from core.maintenance import analyse

SCHEMA = """Tables SQLite (montants en FCFA) :
v_actifs(id, code, libelle, categorie, zone, agence, date_acquisition, cout_acquisition, duree_ans, methode, valeur_residuelle, numero_serie, statut, vnc, amort_cumule, dotation_exercice, age_ans)
maintenance(id, asset_id -> v_actifs.id, date, type, cout)
categorie in: Serveurs, Matériel informatique, Monétique (ATM/TPE), Véhicules, Mobilier de bureau, Climatisation & énergie
zone in: Littoral, Centre, Ouest, Nord, Sud-Ouest ; methode in: lineaire, degressif
vnc = valeur nette comptable ; amort_cumule = amortissements cumulés ; dotation_exercice = dotation de l'exercice en cours."""
FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|attach|pragma|create|replace|vacuum)\b", re.I)

def _n(s): return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()

def safe_sql(sql):
    sql = sql.strip().rstrip(";")
    if ";" in sql or FORBIDDEN.search(sql) or not re.match(r"(?is)^\s*(select|with)\b", sql):
        raise ValueError("Seules les requêtes de lecture (SELECT) sont autorisées.")
    return sql

def run_sql(sql):
    with db.connect(readonly=True) as c:
        return pd.read_sql(safe_sql(sql), c).head(500)

def rule_sql(q):
    """Repli sans LLM : construit un SQL à partir de mots-clés (catégorie, zone, agence, indicateur)."""
    nq, where = _n(q), []
    a = db.load("v_actifs")
    for cat in a.categorie.unique():
        if _n(cat.split()[0].rstrip("s")) in nq: where.append(f"categorie = '{cat}'")
    for z in a.zone.unique():
        if _n(z) in nq: where.append(f"zone = '{z}'")
    for ag in a.agence.unique():
        if _n(ag) in nq or _n(ag.split()[-1]) in nq: where.append(f"agence = '{ag}'")
    if "vehicule" in nq: where.append("categorie = 'Véhicules'")
    w = (" WHERE " + " AND ".join(dict.fromkeys(where))) if where else ""
    if re.search(r"amort|dotation", nq): m = "SUM(amort_cumule) AS amortissements_cumules, SUM(dotation_exercice) AS dotation_exercice"
    elif re.search(r"vnc|valeur nette", nq): m = "SUM(vnc) AS vnc_totale"
    elif re.search(r"cout|valeur d.origine|acquisition", nq): m = "SUM(cout_acquisition) AS cout_total"
    else: m = "COUNT(*) AS nombre_actifs"
    grp = "categorie" if ("par categorie" in nq) else "zone" if ("par zone" in nq) else None
    if grp: return f"SELECT {grp}, {m} FROM v_actifs{w} GROUP BY {grp} ORDER BY 2 DESC"
    return f"SELECT {m} FROM v_actifs{w}"

def llm_sql(q):
    out = llm.chat("Tu es un expert SQLite. Réponds UNIQUEMENT par une requête SELECT, sans explication ni balises.\n" + SCHEMA, q, 0, 300)
    return re.sub(r"```(?:sql)?", "", out).strip()

class S(TypedDict, total=False):
    question: str; intent: str; result: dict

def supervisor(s):
    n = _n(s["question"])
    if re.search(r"repar|maintenance|remplac|capex|opex|obsolesc|fin de vie", n): i = "maintenance"
    elif re.search(r"rapproch|inventaire|matching|ecart|doublon", n): i = "audit"
    elif re.search(r"amort|vnc|valeur nette|deprec|dotation|ifrs|ias", n): i = "finance"
    else: i = "data"
    return {"intent": i}

def data_agent(s, label="Agent Données"):
    q = s["question"]
    try: sql = llm_sql(q) if llm.available() else rule_sql(q)
    except Exception: sql = rule_sql(q)
    try: df = run_sql(sql)
    except Exception as e:
        return {"result": dict(agent=label, text=f"Requête impossible : {e}. Reformulez en précisant la catégorie, la zone ou l'agence.", sql=sql, df=None)}
    text = f"{len(df)} ligne(s) retournée(s)."
    if llm.available() and len(df):
        try: text = llm.chat("Tu es Sira, copilote d'Ecobank Cameroun. Réponds en français, en 2-3 phrases, chiffres en FCFA avec séparateurs.", f"Question : {q}\nRésultat :\n{df.head(15).to_csv(index=False)}")
        except Exception: pass
    return {"result": dict(agent=label, text=text, sql=sql, df=df)}

def finance_agent(s): return data_agent(s, "Agent Analyse Financière")

def maintenance_agent(s):
    m = re.search(r"(\d{1,3})\s*%", s["question"]); seuil = int(m.group(1)) / 100 if m else 0.6
    base = "origine" if re.search(r"origine|acquisition", _n(s["question"])) else "vnc"
    d = analyse(db.load("v_actifs"), db.load("maintenance"), seuil, "vnc" if base == "vnc" else "cout")
    sel = d[d.recommandation == "Remplacer (CapEx)"]
    if re.search(r"vehicule", _n(s["question"])): sel = sel[sel.categorie == "Véhicules"]
    cols = ["code", "libelle", "agence", "age_ans", "vnc", "opex_cumule", "ratio_opex", "capex_estime"]
    txt = f"{len(sel)} actif(s) dépassent le seuil de {seuil:.0%} (OpEx cumulé / {'VNC' if base == 'vnc' else 'valeur d’origine'}) ; budget CapEx estimé : {sel.capex_estime.sum():,.0f} FCFA.".replace(",", " ")
    return {"result": dict(agent="Agent Maintenance Prédictive", text=txt, sql=None, df=sel[cols].head(100))}

def audit_agent(s):
    return {"result": dict(agent="Agent d'Audit & Matching", sql=None, df=None,
                           text="Le rapprochement se lance depuis le module « Matching & Rapprochement » : chargez le fichier de comptage (CSV/Excel) puis cliquez sur « Lancer le matching agentique ».")}

def ask(question):
    try:
        from langgraph.graph import StateGraph, END
        g = StateGraph(S)
        for k, f in dict(supervisor=supervisor, data=data_agent, finance=finance_agent, maintenance=maintenance_agent, audit=audit_agent).items(): g.add_node(k, f)
        g.set_entry_point("supervisor")
        g.add_conditional_edges("supervisor", lambda s: s["intent"], {k: k for k in ["data", "finance", "maintenance", "audit"]})
        for k in ["data", "finance", "maintenance", "audit"]: g.add_edge(k, END)
        return g.compile().invoke({"question": question})["result"]
    except ImportError:
        s = {"question": question}; i = supervisor(s)["intent"]
        return dict(data=data_agent, finance=finance_agent, maintenance=maintenance_agent, audit=audit_agent)[i](s)["result"]
