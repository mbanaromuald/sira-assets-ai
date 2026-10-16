"""Charte graphique tirée du logo Ecobank : bleu profond #095B81, vert lime du swoosh, blanc glacé, italique humaniste."""
import base64, json, pathlib
import streamlit as st
import streamlit.components.v1 as components

BLUE, DEEP, LIME, ICE, MIST = "#095B81", "#06405C", "#A6CE39", "#E6FFFF", "#F3F8FA"
PALETTE = [BLUE, LIME, "#3C8DAD", "#6B8E23", "#7FB8CE", "#D97706"]
LOGO = pathlib.Path(__file__).resolve().parent.parent / "assets" / "logo.jpg"

def logo_b64(): return base64.b64encode(LOGO.read_bytes()).decode()

def css():
    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:ital,wght@0,400;0,600;1,700;1,900&family=Figtree:wght@400;500;700&display=swap');
html, body, [class*="css"], .stMarkdown, p, label {{ font-family: 'Figtree', 'Segoe UI', sans-serif; }}
h1, h2, h3 {{ font-family: 'Nunito Sans', 'Segoe UI', sans-serif; font-style: italic; font-weight: 900; color: {BLUE}; letter-spacing: -.5px; }}
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, {BLUE} 0%, {DEEP} 100%); border-right: 4px solid {LIME}; }}
[data-testid="stSidebar"] * {{ color: {ICE} !important; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{ padding: 8px 10px; border-radius: 10px; transition: background .2s; }}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background: rgba(166,206,57,.18); }}
.stButton > button, .stDownloadButton > button {{ background: {LIME}; color: {DEEP}; font-weight: 700; border: 0; border-radius: 999px; padding: .55rem 1.4rem; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ background: {BLUE}; color: #fff; }}
.stButton > button:focus-visible {{ outline: 3px solid {BLUE}; outline-offset: 2px; }}
[data-testid="stMetric"] {{ background: #fff; border-radius: 16px 16px 16px 4px; padding: 14px 18px; border-left: 6px solid {LIME}; box-shadow: 0 6px 18px rgba(9,91,129,.10); }}
[data-testid="stMetricValue"] {{ color: {BLUE}; font-family: 'Nunito Sans', sans-serif; font-weight: 900; }}
.adv-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 18px; margin: 10px 0 24px; }}
.adv {{ background: #fff; border-radius: 22px 22px 22px 4px; padding: 22px; border-top: 5px solid {LIME}; box-shadow: 0 8px 22px rgba(9,91,129,.10); }}
.adv .ic {{ width: 46px; height: 46px; border-radius: 50%; background: {BLUE}; display: grid; place-items: center; font-size: 22px; margin-bottom: 10px; }}
.adv h4 {{ margin: 0 0 6px; color: {BLUE}; font-family: 'Nunito Sans', sans-serif; font-style: italic; font-weight: 900; font-size: 1.15rem; }}
.adv p {{ margin: 0; color: #3b5565; font-size: .95rem; line-height: 1.5; }}
.adv .kpi {{ font-family: 'Nunito Sans', sans-serif; font-style: italic; font-weight: 900; font-size: 2rem; color: {LIME}; background: {BLUE}; display: inline-block; padding: 0 12px; border-radius: 10px; margin-bottom: 8px; }}
.badge {{ display:inline-block; padding: 3px 12px; border-radius: 999px; font-weight: 700; font-size: .8rem; }}
.b-ok {{ background: {LIME}; color: {DEEP}; }} .b-warn {{ background: #D97706; color: #fff; }} .b-ko {{ background: #B42318; color: #fff; }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>""", unsafe_allow_html=True)

HERO = """<style>
*{box-sizing:border-box;margin:0}body{font-family:'Nunito Sans','Segoe UI',sans-serif;background:transparent}
.hero{position:relative;height:250px;border-radius:26px 26px 26px 6px;overflow:hidden;background:linear-gradient(120deg,#095B81 0%,#06405C 100%);color:#fff;display:flex;align-items:center;padding:0 32px;gap:28px}
.hero svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.logo{width:150px;height:150px;border-radius:20px;flex:none;z-index:2;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.slides{position:relative;flex:1;height:170px;z-index:2}
.slide{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;opacity:0;transform:translateX(40px);transition:opacity .8s,transform .8s}
.slide.on{opacity:1;transform:none}
.tag{align-self:flex-start;background:#A6CE39;color:#06405C;font-weight:900;font-style:italic;padding:3px 14px;border-radius:999px;font-size:13px;margin-bottom:10px}
.slide h2{font-style:italic;font-weight:900;font-size:clamp(20px,3.2vw,34px);line-height:1.12;letter-spacing:-.5px}
.slide p{margin-top:8px;color:#E6FFFF;font-size:15px;max-width:640px}
.dots{position:absolute;right:26px;bottom:16px;display:flex;gap:7px;z-index:3}
.dots button{width:11px;height:11px;border-radius:50%;border:0;background:rgba(255,255,255,.4);cursor:pointer}
.dots button.on{background:#A6CE39;width:26px;border-radius:8px}
@media(max-width:640px){.logo{width:84px;height:84px}.hero{padding:0 16px;gap:14px}.slide p{font-size:13px}}
@media(prefers-reduced-motion:reduce){.slide{transition:none}}
</style>
<div class="hero"><svg viewBox="0 0 1000 250" preserveAspectRatio="none"><path d="M-20 215 C 250 90, 640 40, 1020 120" fill="none" stroke="#A6CE39" stroke-width="5" stroke-linecap="round" opacity=".9"/><path d="M-20 235 C 300 140, 700 100, 1020 170" fill="none" stroke="#E6FFFF" stroke-width="1.5" opacity=".35"/></svg>
<img class="logo" alt="Ecobank - La Banque Panafricaine" src="data:image/jpeg;base64,__LOGO__">
<div class="slides" id="s"></div><div class="dots" id="d"></div></div>
<script>
const S=__SLIDES__,s=document.getElementById('s'),d=document.getElementById('d');let i=0,t;
S.forEach((x,k)=>{s.insertAdjacentHTML('beforeend',`<div class="slide"><span class="tag">${x[0]}</span><h2>${x[1]}</h2><p>${x[2]}</p></div>`);const b=document.createElement('button');b.setAttribute('aria-label','Message '+(k+1));b.onclick=()=>{go(k);reset()};d.appendChild(b)});
function go(n){i=n;[...s.children].forEach((e,k)=>e.classList.toggle('on',k===n));[...d.children].forEach((e,k)=>e.classList.toggle('on',k===n))}
function reset(){clearInterval(t);t=setInterval(()=>go((i+1)%S.length),5200)}
go(0);reset();
</script>"""

TICKER = """<style>
*{margin:0;box-sizing:border-box}body{font-family:'Figtree','Segoe UI',sans-serif}
.bar{display:flex;align-items:center;background:#095B81;border-radius:8px 24px 8px 24px;overflow:hidden;height:46px;border-bottom:3px solid #A6CE39}
.bar img{height:46px;width:46px;flex:none}
.wrap{overflow:hidden;flex:1;white-space:nowrap}
.move{display:inline-block;padding-left:100%;animation:t 45s linear infinite}
.bar:hover .move{animation-play-state:paused}
.it{display:inline-block;padding:0 34px;color:#fff;font-size:13.5px}
.bd{padding:2px 10px;border-radius:999px;font-weight:800;margin-right:8px;font-size:11.5px;background:#A6CE39;color:#06405C}.bd.w{background:#D97706;color:#fff}
@keyframes t{to{transform:translateX(-100%)}}@media(prefers-reduced-motion:reduce){.move{animation:none;padding-left:12px}}
</style>
<div class="bar"><img alt="Ecobank" src="data:image/jpeg;base64,__LOGO__"><div class="wrap"><div class="move">__ITEMS__</div></div></div>"""

def hero(slides):
    components.html(HERO.replace("__LOGO__", logo_b64()).replace("__SLIDES__", json.dumps(slides, ensure_ascii=False)), height=270)

def ticker(items):
    html = "".join(f'<span class="it"><span class="bd {"w" if w else ""}">{tag}</span>{txt}</span>' for tag, txt, w in items)
    components.html(TICKER.replace("__LOGO__", logo_b64()).replace("__ITEMS__", html), height=56)

ADVANTAGES = [
    ("🔄", "Matching d'inventaire intelligent", "Rapprochement flou (résolution d'entités) entre libellés terrain et registre comptable. Objectif de précision : plus de 95 %.", "> 95 %"),
    ("💬", "Requêtes en français courant", "« Quel est le total des amortissements des serveurs de la zone Ouest ? » : la réponse arrive en secondes, auditable via le SQL généré.", "Text-to-SQL"),
    ("📈", "Arbitrage CapEx / OpEx", "Quand l'OpEx cumulé dépasse un seuil de la VNC, l'agent recommande formellement le renouvellement et chiffre le budget.", "Prédictif"),
    ("⏱️", "Gain de productivité", "Plus de 50 % de temps gagné sur les rapprochements : les équipes se consacrent à l'analyse plutôt qu'à la saisie.", "− 50 % de temps"),
    ("🛡️", "Conformité & traçabilité", "Calculs alignés IFRS / IAS 16, lecture seule sur la base pour l'IA, traçabilité adaptée aux exigences COBAC.", "IFRS · COBAC"),
]

def advantages_html():
    return '<div class="adv-grid">' + "".join(f'<div class="adv"><div class="ic">{i}</div><span class="kpi">{k}</span><h4>{t}</h4><p>{d}</p></div>' for i, t, d, k in ADVANTAGES) + "</div>"
