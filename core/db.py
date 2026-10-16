"""Base SQLite : registre des immobilisations, tickets de maintenance, données de démonstration."""
import os, random, sqlite3
from datetime import date, timedelta
import pandas as pd

DB_PATH = os.getenv("DB_PATH", "data/sira_assets.db")
# catégorie: (coût min, coût max, durée ans, méthode, préfixes de libellé)
CATS = {
    "Serveurs": (8e6, 25e6, 5, "degressif", ["Serveur Dell PowerEdge", "Serveur HP ProLiant", "Serveur Lenovo ThinkSystem"]),
    "Matériel informatique": (4e5, 1.8e6, 4, "lineaire", ["Ordinateur portable HP EliteBook", "PC fixe Dell OptiPlex", "Imprimante Xerox", "Écran Lenovo"]),
    "Monétique (ATM/TPE)": (6e6, 14e6, 7, "degressif", ["Distributeur NCR SelfServ", "Distributeur Diebold Nixdorf", "Terminal TPE Ingenico"]),
    "Véhicules": (12e6, 38e6, 5, "lineaire", ["Toyota Hilux", "Toyota Land Cruiser", "Hyundai Tucson", "Nissan Navara"]),
    "Mobilier de bureau": (8e4, 9e5, 10, "lineaire", ["Bureau direction", "Fauteuil ergonomique", "Armoire forte", "Coffre-fort"]),
    "Climatisation & énergie": (1.2e6, 7e6, 8, "lineaire", ["Groupe électrogène Perkins", "Onduleur APC", "Climatiseur Carrier"]),
}
ZONES = {
    "Littoral": ["Douala Akwa", "Douala Bonanjo", "Douala Bonabéri"],
    "Centre": ["Yaoundé Bastos", "Yaoundé Centre", "Yaoundé Mvan"],
    "Ouest": ["Bafoussam", "Dschang"],
    "Nord": ["Garoua", "Maroua"],
    "Sud-Ouest": ["Buea", "Limbe"],
}

def connect(readonly=False):
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    if readonly:
        return sqlite3.connect(f"file:{os.path.abspath(DB_PATH)}?mode=ro", uri=True)
    return sqlite3.connect(DB_PATH)

def _seed(n=320, seed=42):
    rnd = random.Random(seed)
    today, rows, tickets = date.today(), [], []
    agences = [(z, a) for z, l in ZONES.items() for a in l]
    for i in range(1, n + 1):
        cat = rnd.choice(list(CATS)); lo, hi, duree, meth, pref = CATS[cat]
        zone, ag = rnd.choice(agences)
        acq = today - timedelta(days=rnd.randint(60, int(duree * 365 * 1.25)))
        cout = round(rnd.uniform(lo, hi), -3)
        rows.append(dict(id=i, code=f"EBK-CM-{i:05d}", libelle=f"{rnd.choice(pref)} {rnd.choice(['A','B','X','Pro','2'])}{rnd.randint(10,99)}",
                         categorie=cat, zone=zone, agence=ag, date_acquisition=acq.isoformat(), cout_acquisition=cout,
                         duree_ans=duree, methode=meth, valeur_residuelle=0.0,
                         numero_serie=f"SN{rnd.randint(10**7, 10**8-1)}", statut="En service"))
        age = (today - acq).days / 365
        for _ in range(int(rnd.random() * age * 2.2)):
            tickets.append(dict(asset_id=i, date=(acq + timedelta(days=rnd.randint(30, max(31, int(age * 365))))).isoformat(),
                                type=rnd.choice(["Préventive", "Corrective", "Corrective", "Pièces"]),
                                cout=round(cout * rnd.uniform(0.01, 0.09), -2)))
    return pd.DataFrame(rows), pd.DataFrame(tickets)

def init_db(force=False):
    if force and os.path.exists(DB_PATH): os.remove(DB_PATH)
    if not os.path.exists(DB_PATH):
        a, m = _seed()
        m.insert(0, "id", range(1, len(m) + 1))
        with connect() as c:
            a.to_sql("actifs", c, index=False); m.to_sql("maintenance", c, index=False)
        refresh_views()

def refresh_views(as_of=None):
    """(Re)calcule v_actifs : registre + amortissement cumulé, VNC et dotation de l'exercice."""
    from core.finance import enrich
    with connect() as c:
        a = pd.read_sql("select * from actifs", c)
        enrich(a, as_of).to_sql("v_actifs", c, index=False, if_exists="replace")

def load(table):
    with connect() as c: return pd.read_sql(f"select * from {table}", c)

def sample_inventory(seed=7):
    """Simule un comptage terrain : libellés bruités, quelques actifs absents ou inconnus."""
    rnd, a, out = random.Random(seed), load("actifs"), []
    ags = sum(ZONES.values(), [])
    for _, r in a.iterrows():
        if rnd.random() < 0.06: continue
        lib = r.libelle
        if rnd.random() < .35: lib = lib.lower().replace("serveur", "srv").replace("ordinateur portable", "laptop")
        if rnd.random() < .15: lib = lib[:-1]
        out.append(dict(libelle=lib, numero_serie=r.numero_serie if rnd.random() < .6 else "",
                        agence=r.agence if rnd.random() > .05 else rnd.choice(ags)))
    for k in range(5): out.append(dict(libelle=f"Équipement non étiqueté {k+1}", numero_serie="", agence=rnd.choice(ags)))
    return pd.DataFrame(out)
