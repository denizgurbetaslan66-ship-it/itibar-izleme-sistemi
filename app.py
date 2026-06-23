"""
Erken İtibar Krizi Tespit ve Karar Destek Sistemi
TÜBİTAK 1002 Proje Prototipi
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import random
import hashlib
import json
import os
from pathlib import Path

# ─── SAYFA KONFIGURASYON ────────────────────────────────────────────────────
st.set_page_config(
    page_title="İtibar İzleme Sistemi",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── GLOBAL STILLER ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

  /* GLOBAL */
  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  .stApp {
    background: #0a0e1a;
  }

  /* ── SIDEBAR ── */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1220 0%, #111827 100%);
    border-right: 1px solid #1e2a3a;
  }

  section[data-testid="stSidebar"] .stRadio label,
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] p {
    color: #94a3b8 !important;
  }

  /* ── KARTlar ── */
  .metric-card {
    background: linear-gradient(135deg, #111827 0%, #1a2234 100%);
    border: 1px solid #1e2a3a;
    border-radius: 16px;
    padding: 24px;
    position: relative;
    overflow: hidden;
  }

  .metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent, linear-gradient(90deg, #3b82f6, #8b5cf6));
  }

  .metric-card .label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 8px;
  }

  .metric-card .value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 36px;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1;
    margin-bottom: 6px;
  }

  .metric-card .delta {
    font-size: 12px;
    color: #64748b;
  }

  .delta-up { color: #22c55e !important; }
  .delta-down { color: #ef4444 !important; }

  /* ── KRIZ BADGE ── */
  .badge-low    { background: rgba(34,197,94,.12);  color: #22c55e; border: 1px solid rgba(34,197,94,.25); }
  .badge-medium { background: rgba(234,179,8,.12);  color: #eab308; border: 1px solid rgba(234,179,8,.25); }
  .badge-high   { background: rgba(239,68,68,.12);  color: #ef4444; border: 1px solid rgba(239,68,68,.25); }
  .badge-critical { background: rgba(220,38,38,.2); color: #ff4444; border: 1px solid rgba(220,38,38,.4); animation: pulse-red 1.5s infinite; }

  .badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  @keyframes pulse-red {
    0%, 100% { box-shadow: 0 0 0 0 rgba(220,38,38,0.4); }
    50%       { box-shadow: 0 0 0 6px rgba(220,38,38,0); }
  }

  /* ── TABLO ── */
  .data-table { width: 100%; border-collapse: separate; border-spacing: 0; }
  .data-table th {
    background: #0d1220;
    color: #64748b;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 10px 16px;
    border-bottom: 1px solid #1e2a3a;
  }
  .data-table td {
    padding: 12px 16px;
    color: #cbd5e1;
    font-size: 13px;
    border-bottom: 1px solid #1a2234;
  }
  .data-table tr:hover td { background: rgba(59,130,246,0.04); }

  /* ── SEKME ── */
  .stTabs [data-baseweb="tab-list"] {
    background: transparent;
    gap: 4px;
    border-bottom: 1px solid #1e2a3a;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #64748b;
    border-radius: 8px 8px 0 0;
    font-size: 13px;
    font-weight: 500;
  }
  .stTabs [aria-selected="true"] {
    background: rgba(59,130,246,0.08) !important;
    color: #3b82f6 !important;
    border-bottom: 2px solid #3b82f6 !important;
  }

  /* ── INPUT ── */
  .stTextInput input, .stPasswordInput input, .stSelectbox select {
    background: #111827 !important;
    border: 1px solid #1e2a3a !important;
    color: #f1f5f9 !important;
    border-radius: 10px !important;
  }

  .stTextInput input:focus, .stPasswordInput input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
  }

  /* ── BUTTON ── */
  .stButton > button {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 24px !important;
    transition: all 0.2s !important;
  }
  .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(59,130,246,0.3) !important;
  }

  /* ── BAŞLIKLAR ── */
  h1, h2, h3 { color: #f1f5f9 !important; font-family: 'Space Grotesk', sans-serif !important; }
  h1 { font-size: 28px !important; font-weight: 700 !important; }
  h2 { font-size: 20px !important; font-weight: 600 !important; }
  h3 { font-size: 16px !important; font-weight: 600 !important; }
  p, li { color: #94a3b8 !important; }

  /* ── LOGO / HEADER ── */
  .brand-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px 0 24px;
    border-bottom: 1px solid #1e2a3a;
    margin-bottom: 24px;
  }
  .brand-icon {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
  }
  .brand-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 17px;
    font-weight: 700;
    color: #f1f5f9;
  }
  .brand-sub {
    font-size: 10px;
    color: #475569;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  /* ── UYARI BANNER ── */
  .alert-banner {
    background: linear-gradient(90deg, rgba(239,68,68,.12), rgba(239,68,68,.05));
    border: 1px solid rgba(239,68,68,.25);
    border-left: 3px solid #ef4444;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 16px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }

  .section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e2a3a;
  }

  /* ── SCORE RING ── */
  .score-ring-container {
    text-align: center;
    padding: 8px 0;
  }

  /* ── HİDE STREAMLIT CHROME ── */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 1.5rem 2rem; }
</style>
""", unsafe_allow_html=True)

# ─── VERİ / MODEL ────────────────────────────────────────────────────────────
DATA_FILE   = Path("data/users.json")
ALERTS_FILE = Path("data/alerts.json")
DATA_FILE.parent.mkdir(exist_ok=True)

def load_json(path, default):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ─── DEMO VERİ ÜRETİCİ ──────────────────────────────────────────────────────
def simulate_mentions(days=30, base_level=20, spike_day=None):
    """Gerçekçi yorum hacmi simülasyonu."""
    data = []
    now = datetime.now()
    np.random.seed(42)
    for i in range(days * 24):
        ts  = now - timedelta(hours=(days*24 - i))
        vol = max(0, int(np.random.poisson(base_level) + np.random.normal(0, 3)))
        if spike_day and i >= spike_day * 24 and i < (spike_day + 2) * 24:
            vol += int(np.random.exponential(80))
        data.append({"ts": ts, "volume": vol})
    return pd.DataFrame(data)

def generate_sample_content(kurum="TechMarka A.Ş.", n=40):
    """Örnek sosyal medya/forum içerikleri."""
    templates = [
        ("negative", "şikayetvar", f"{kurum} ürünü bozuk geldi, kesinlikle tavsiye etmiyorum"),
        ("negative", "ekşi sözlük", f"{kurum} hakkında müşteri hizmetleri berbat bir deneyim"),
        ("positive", "haber", f"{kurum} çevre dostu üretim süreciyle ödül aldı"),
        ("neutral",  "twitter",   f"{kurum} yeni ürünlerini tanıttı, merak ediyorum"),
        ("negative", "twitter",   f"{kurum} siparişim 2 haftadır gelmedi, dolandırıcılık mı?"),
        ("positive", "haber",     f"{kurum} bu yıl en hızlı büyüyen şirketler listesinde"),
        ("negative", "ekşi sözlük",f"{kurum} kalite düşüşü devam ediyor ne oldu bu firmaya"),
        ("positive", "instagram",  f"{kurum} müşteri memnuniyetinde sektör lideri"),
        ("neutral",  "şikayetvar", f"{kurum} fiyatları artmış ama kalite aynı kaldı"),
        ("negative", "haber",      f"{kurum} hakkında tüketici şikayetleri gündemde"),
    ]
    rows = []
    now = datetime.now()
    for i in range(n):
        t = templates[i % len(templates)]
        ts = now - timedelta(hours=random.randint(1, 72))
        rows.append({
            "zaman": ts,
            "duygu": t[0],
            "platform": t[1],
            "içerik": t[2],
            "kriz_skoru": round(random.uniform(1, 9), 1) if t[0] == "negative" else round(random.uniform(0.5, 3), 1)
        })
    return pd.DataFrame(rows).sort_values("zaman", ascending=False).reset_index(drop=True)

def compute_reputation_score(df):
    if df.empty:
        return 50
    w = {"haber": 3, "twitter": 2, "şikayetvar": 2, "ekşi sözlük": 1.5, "instagram": 1}
    score_map = {"positive": 100, "neutral": 50, "negative": 0}
    total_w, total_s = 0, 0
    now = datetime.now()
    for _, row in df.iterrows():
        age_h  = max(1, (now - row["zaman"]).total_seconds() / 3600)
        recency = np.exp(-age_h / 48)
        weight  = w.get(row["platform"], 1) * recency
        total_w += weight
        total_s += score_map[row["duygu"]] * weight
    return round(total_s / total_w) if total_w > 0 else 50

def crisis_severity(df):
    neg = df[df["duygu"] == "negative"]
    if neg.empty:
        return 0.0
    recent = neg[neg["zaman"] >= datetime.now() - timedelta(hours=24)]
    velocity   = len(recent) / max(1, len(df)) * 10
    cross_plat = len(recent["platform"].unique()) / 4 * 10
    intensity  = recent["kriz_skoru"].mean() if not recent.empty else 0
    danger_kw  = recent["içerik"].str.contains("dolandırıcılık|sağlık|kaza|sahte|tehlike", case=False).sum()
    kw_boost   = min(danger_kw * 0.5, 2)
    raw = (velocity * 0.3 + cross_plat * 0.3 + intensity * 0.3 + kw_boost * 0.1) * 1.2
    return min(round(raw, 1), 10.0)

def severity_label(score):
    if score >= 7:   return "KRİTİK", "badge-critical"
    if score >= 5:   return "YÜKSEK",  "badge-high"
    if score >= 3:   return "ORTA",    "badge-medium"
    return "DÜŞÜK", "badge-low"

def reputation_label(score):
    if score >= 75: return "İYİ",      "#22c55e"
    if score >= 50: return "NORMAL",   "#eab308"
    if score >= 30: return "RİSKLİ",   "#f97316"
    return "KRİTİK", "#ef4444"

# ─── SESSION STATE ───────────────────────────────────────────────────────────
if "logged_in"   not in st.session_state: st.session_state.logged_in   = False
if "username"    not in st.session_state: st.session_state.username    = ""
if "kurum"       not in st.session_state: st.session_state.kurum       = ""
if "alerts_sent" not in st.session_state: st.session_state.alerts_sent = []
if "refresh_key" not in st.session_state: st.session_state.refresh_key = 0

# ─── GİRİŞ / KAYIT EKRANI ────────────────────────────────────────────────────
def show_login():
    col_c, col_f, col_c2 = st.columns([1, 1.2, 1])
    with col_f:
        st.markdown("""
        <div style="text-align:center; padding: 40px 0 32px;">
          <div style="display:inline-flex; align-items:center; justify-content:center;
                      width:56px; height:56px; background:linear-gradient(135deg,#3b82f6,#8b5cf6);
                      border-radius:16px; font-size:26px; margin-bottom:16px;">🛡️</div>
          <div style="font-family:'Space Grotesk',sans-serif; font-size:22px; font-weight:700; color:#f1f5f9;">
            İtibar İzleme Sistemi
          </div>
          <div style="font-size:12px; color:#475569; margin-top:6px; letter-spacing:0.08em; text-transform:uppercase;">
            TÜBİTAK 1002 Proje Prototipi
          </div>
        </div>
        """, unsafe_allow_html=True)

        tab_giris, tab_kayit = st.tabs(["  Giriş Yap  ", "  Yeni Kayıt  "])

        with tab_giris:
            st.markdown("<br>", unsafe_allow_html=True)
            email_g = st.text_input("Kurumsal E-posta", placeholder="adi@kurum.com.tr", key="login_email")
            sifre_g = st.text_input("Şifre", type="password", key="login_pw")
            if st.button("Sisteme Giriş Yap", use_container_width=True):
                users = load_json(DATA_FILE, {})
                if email_g in users and users[email_g]["pw"] == hash_pw(sifre_g):
                    st.session_state.logged_in = True
                    st.session_state.username  = email_g
                    st.session_state.kurum     = users[email_g]["kurum"]
                    st.rerun()
                else:
                    st.error("E-posta veya şifre hatalı.")

            st.markdown("""
            <div style='margin-top:16px; padding:12px 16px; background:rgba(59,130,246,.06);
                        border:1px solid rgba(59,130,246,.15); border-radius:10px;
                        font-size:12px; color:#64748b;'>
              🔑 <b style='color:#94a3b8;'>Demo hesap:</b> demo@firma.com.tr / Demo1234
            </div>""", unsafe_allow_html=True)

            # Demo hesabı otomatik oluştur
            users = load_json(DATA_FILE, {})
            if "demo@firma.com.tr" not in users:
                users["demo@firma.com.tr"] = {
                    "pw": hash_pw("Demo1234"),
                    "kurum": "TechMarka A.Ş.",
                    "domain": "firma.com.tr",
                    "role": "admin"
                }
                save_json(DATA_FILE, users)

        with tab_kayit:
            st.markdown("<br>", unsafe_allow_html=True)
            email_k  = st.text_input("Kurumsal E-posta", placeholder="adi@sirket.com.tr", key="reg_email")
            kurum_k  = st.text_input("Kurum Adı", placeholder="ABC Şirketi A.Ş.", key="reg_kurum")
            sifre_k  = st.text_input("Şifre Belirleyin", type="password", key="reg_pw")
            sifre_k2 = st.text_input("Şifre Tekrar", type="password", key="reg_pw2")

            if st.button("Kayıt Ol ve Başla", use_container_width=True):
                free_domains = ["gmail.com","hotmail.com","outlook.com","yahoo.com","yandex.com"]
                domain = email_k.split("@")[-1] if "@" in email_k else ""
                if not email_k or "@" not in email_k:
                    st.error("Geçerli bir e-posta girin.")
                elif domain in free_domains:
                    st.error("Yalnızca kurumsal e-posta adresleri kabul edilmektedir.")
                elif len(sifre_k) < 6:
                    st.error("Şifre en az 6 karakter olmalıdır.")
                elif sifre_k != sifre_k2:
                    st.error("Şifreler eşleşmiyor.")
                elif not kurum_k:
                    st.error("Kurum adını girin.")
                else:
                    users = load_json(DATA_FILE, {})
                    if email_k in users:
                        st.error("Bu e-posta zaten kayıtlı.")
                    else:
                        users[email_k] = {
                            "pw": hash_pw(sifre_k),
                            "kurum": kurum_k,
                            "domain": domain,
                            "role": "admin"
                        }
                        save_json(DATA_FILE, users)
                        st.success("✅ Kayıt başarılı! Giriş yapabilirsiniz.")

# ─── ANA DASHBOARD ───────────────────────────────────────────────────────────
def show_dashboard():
    kurum = st.session_state.kurum

    # Veri
    df_content  = generate_sample_content(kurum=kurum, n=50)
    df_vol      = simulate_mentions(days=14, base_level=18, spike_day=10)
    rep_score   = compute_reputation_score(df_content)
    cris_score  = crisis_severity(df_content)
    sev_label, sev_cls = severity_label(cris_score)
    rep_lbl, rep_color  = reputation_label(rep_score)

    # ── SIDEBAR ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div class="brand-header">
          <div class="brand-icon">🛡️</div>
          <div>
            <div class="brand-name">İtibar İzleme</div>
            <div class="brand-sub">Erken Uyarı Sistemi</div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='padding:12px 14px; background:rgba(59,130,246,.08); border:1px solid rgba(59,130,246,.18);
                    border-radius:10px; margin-bottom:20px;'>
          <div style='font-size:10px; color:#475569; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:4px;'>Aktif Kurum</div>
          <div style='font-size:14px; font-weight:600; color:#f1f5f9;'>{kurum}</div>
          <div style='font-size:11px; color:#64748b;'>{st.session_state.username}</div>
        </div>""", unsafe_allow_html=True)

        page = st.radio(
            "Menü",
            ["📊 Ana Gösterge Paneli", "📰 İçerik Akışı", "📈 Trend Analizi", "⚙️ Ayarlar"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        if st.button("🔄  Verileri Yenile"):
            st.session_state.refresh_key += 1
            st.rerun()

        st.markdown(f"""
        <div style='padding:10px; text-align:center; margin-top:16px;'>
          <div style='font-size:10px; color:#334155;'>Son güncelleme</div>
          <div style='font-size:12px; color:#475569;'>{datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
        </div>""", unsafe_allow_html=True)

        if st.button("Çıkış Yap", key="logout"):
            st.session_state.logged_in = False
            st.rerun()

    # ── ANA İÇERİK ──────────────────────────────────────────────────────────
    p = page.split(" ", 1)[1].strip()

    if "Gösterge Paneli" in p:
        show_main_dashboard(df_content, df_vol, rep_score, cris_score,
                            sev_label, sev_cls, rep_lbl, rep_color, kurum)
    elif "İçerik Akışı" in p:
        show_content_feed(df_content)
    elif "Trend Analizi" in p:
        show_trend_analysis(df_content, df_vol)
    elif "Ayarlar" in p:
        show_settings()

# ─── ANA GÖSTERGE PANELİ ────────────────────────────────────────────────────
def show_main_dashboard(df, df_vol, rep_score, cris_score,
                         sev_label, sev_cls, rep_lbl, rep_color, kurum):
    st.markdown(f"<h1>📊 {kurum} — Anlık İtibar Durumu</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#475569; margin-top:-8px;'>{datetime.now().strftime('%d %B %Y, %H:%M')} itibarıyla</p>", unsafe_allow_html=True)

    # ── KRİZ UYARISI ────────────────────────────────────────────────────────
    if cris_score >= 5:
        alert_emoji = "🚨" if cris_score >= 7 else "⚠️"
        st.markdown(f"""
        <div class="alert-banner">
          <div style='font-size:22px;'>{alert_emoji}</div>
          <div>
            <div style='font-weight:600; color:#f87171; font-size:14px;'>
              {sev_label} KRİZ POTANSİYELİ TESPİT EDİLDİ
            </div>
            <div style='color:#94a3b8; font-size:13px; margin-top:3px;'>
              Son 24 saatte olumsuz içerik hacminde anormal artış. Kriz Şiddet Skoru: {cris_score}/10 — 
              önerilen öncelik: <b style='color:#fca5a5;'>{sev_label}</b>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── ÜST METRİKLER ───────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric-card" style="--accent: linear-gradient(90deg, {rep_color}, {rep_color}88);">
          <div class="label">İtibar Skoru</div>
          <div class="value" style="color:{rep_color};">{rep_score}</div>
          <div class="delta">Durum: <span style="color:{rep_color}; font-weight:600;">{rep_lbl}</span></div>
        </div>""", unsafe_allow_html=True)

    with c2:
        cs_color = "#ef4444" if cris_score >= 5 else "#eab308" if cris_score >= 3 else "#22c55e"
        st.markdown(f"""
        <div class="metric-card" style="--accent: linear-gradient(90deg, {cs_color}, {cs_color}88);">
          <div class="label">Kriz Şiddet Skoru</div>
          <div class="value" style="color:{cs_color};">{cris_score}<span style="font-size:16px; color:#475569;">/10</span></div>
          <div class="delta"><span class="badge {sev_cls}">{sev_label}</span></div>
        </div>""", unsafe_allow_html=True)

    neg_count = len(df[df["duygu"] == "negative"])
    with c3:
        st.markdown(f"""
        <div class="metric-card">
          <div class="label">Olumsuz Mention</div>
          <div class="value">{neg_count}</div>
          <div class="delta class='delta-down'">Son 72 saat</div>
        </div>""", unsafe_allow_html=True)

    plat_count = df["platform"].nunique()
    with c4:
        st.markdown(f"""
        <div class="metric-card">
          <div class="label">Aktif Platform</div>
          <div class="value">{plat_count}</div>
          <div class="delta">Farklı kaynak</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── ORTA SATIR ───────────────────────────────────────────────────────────
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown('<div class="section-title">İçerik Hacmi — Son 14 Gün (Saatlik)</div>', unsafe_allow_html=True)
        vol_daily = df_vol.copy()
        vol_daily["gün"] = vol_daily["ts"].dt.date
        daily_agg = vol_daily.groupby("gün")["volume"].sum().reset_index()

        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(
            x=daily_agg["gün"], y=daily_agg["volume"],
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.08)",
            line=dict(color="#3b82f6", width=2),
            mode="lines",
            name="Hacim"
        ))
        # Spike annotation
        max_idx = daily_agg["volume"].idxmax()
        fig_vol.add_annotation(
            x=daily_agg.loc[max_idx, "gün"],
            y=daily_agg.loc[max_idx, "volume"],
            text="⚠️ Anomali",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#ef4444",
            font=dict(color="#ef4444", size=11),
            bgcolor="rgba(239,68,68,0.1)",
            bordercolor="#ef4444",
            borderwidth=1,
            borderpad=4
        )
        fig_vol.update_layout(
            plot_bgcolor="transparent",
            paper_bgcolor="transparent",
            font=dict(color="#64748b", size=11),
            xaxis=dict(gridcolor="#1e2a3a", showline=False, tickformat="%d %b"),
            yaxis=dict(gridcolor="#1e2a3a", showline=False),
            showlegend=False,
            margin=dict(l=0, r=0, t=4, b=0),
            height=230
        )
        st.plotly_chart(fig_vol, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        st.markdown('<div class="section-title">Duygu Dağılımı</div>', unsafe_allow_html=True)
        sent_counts = df["duygu"].value_counts()
        labels_tr = {"positive": "Pozitif", "neutral": "Nötr", "negative": "Negatif"}
        colors_map = {"positive": "#22c55e", "neutral": "#64748b", "negative": "#ef4444"}
        lbls = [labels_tr.get(x, x) for x in sent_counts.index]
        clrs = [colors_map.get(x, "#8b5cf6") for x in sent_counts.index]

        fig_pie = go.Figure(go.Pie(
            labels=lbls, values=sent_counts.values,
            hole=0.62,
            marker=dict(colors=clrs, line=dict(color="#0a0e1a", width=2)),
            textinfo="percent",
            textfont=dict(size=12, color="white"),
        ))
        fig_pie.update_layout(
            paper_bgcolor="transparent",
            plot_bgcolor="transparent",
            showlegend=True,
            legend=dict(font=dict(color="#94a3b8", size=11), orientation="h", x=0.5, xanchor="center", y=-0.05),
            margin=dict(l=0, r=0, t=0, b=0),
            height=230
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    # ── PLATFORM DAĞILIMI ────────────────────────────────────────────────────
    col_p, col_latest = st.columns([1, 1.4])

    with col_p:
        st.markdown('<div class="section-title">Platform Kırılımı</div>', unsafe_allow_html=True)
        plat_df = df.groupby("platform").agg(
            toplam=("duygu","count"),
            negatif=("duygu", lambda x: (x=="negative").sum())
        ).reset_index()
        plat_df["negatif_oran"] = (plat_df["negatif"] / plat_df["toplam"] * 100).round(1)

        fig_bar = go.Figure(go.Bar(
            x=plat_df["toplam"],
            y=plat_df["platform"],
            orientation="h",
            marker=dict(
                color=plat_df["negatif_oran"],
                colorscale=[[0,"#22c55e"],[0.5,"#eab308"],[1,"#ef4444"]],
                colorbar=dict(title="Neg.%", tickfont=dict(color="#64748b",size=10), thickness=10),
                cmin=0, cmax=100
            ),
            text=plat_df["toplam"],
            textposition="inside",
            textfont=dict(color="white", size=11)
        ))
        fig_bar.update_layout(
            plot_bgcolor="transparent", paper_bgcolor="transparent",
            font=dict(color="#64748b", size=11),
            xaxis=dict(gridcolor="#1e2a3a", showline=False),
            yaxis=dict(gridcolor="transparent"),
            margin=dict(l=0,r=0,t=4,b=0),
            height=220
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    with col_latest:
        st.markdown('<div class="section-title">Son Olumsuz İçerikler</div>', unsafe_allow_html=True)
        neg_df = df[df["duygu"]=="negative"].head(6)
        rows_html = ""
        for _, row in neg_df.iterrows():
            t_ago = int((datetime.now() - row["zaman"]).total_seconds() / 3600)
            cs = row["kriz_skoru"]
            cs_col = "#ef4444" if cs >= 6 else "#eab308" if cs >= 3 else "#94a3b8"
            rows_html += f"""
            <tr>
              <td><span style='background:rgba(100,116,139,.1); color:#94a3b8; font-size:10px;
                               padding:2px 8px; border-radius:4px;'>{row['platform']}</span></td>
              <td style='max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'
                  title='{row["içerik"]}'>{row["içerik"][:52]}…</td>
              <td style='color:{cs_col}; font-weight:600;'>{cs}</td>
              <td style='color:#475569;'>{t_ago}sa</td>
            </tr>"""
        st.markdown(f"""
        <table class="data-table">
          <thead><tr>
            <th>Platform</th><th>İçerik</th><th>Skor</th><th>Önce</th>
          </tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)

# ─── İÇERİK AKIŞI ───────────────────────────────────────────────────────────
def show_content_feed(df):
    st.markdown("<h1>📰 Canlı İçerik Akışı</h1>", unsafe_allow_html=True)

    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        platform_filter = st.selectbox("Platform",
            ["Tümü"] + sorted(df["platform"].unique().tolist()))
    with col_f2:
        duygu_filter = st.selectbox("Duygu",
            ["Tümü", "negative", "positive", "neutral"])

    filtered = df.copy()
    if platform_filter != "Tümü":
        filtered = filtered[filtered["platform"] == platform_filter]
    if duygu_filter != "Tümü":
        filtered = filtered[filtered["duygu"] == duygu_filter]

    duygu_icon = {"positive": "✅", "neutral": "➖", "negative": "🔴"}
    duygu_tr   = {"positive": "Pozitif", "neutral": "Nötr", "negative": "Negatif"}

    rows_html = ""
    for _, row in filtered.iterrows():
        icon = duygu_icon.get(row["duygu"], "•")
        d_tr = duygu_tr.get(row["duygu"], row["duygu"])
        cs   = row["kriz_skoru"]
        cs_col = "#ef4444" if cs >= 6 else "#eab308" if cs >= 3 else "#22c55e"
        ts = row["zaman"].strftime("%d.%m %H:%M")
        rows_html += f"""
        <tr>
          <td style='text-align:center;'>{icon}</td>
          <td><span style='background:rgba(100,116,139,.1);color:#94a3b8;font-size:10px;
                           padding:2px 8px;border-radius:4px;'>{row['platform']}</span></td>
          <td style='color:#94a3b8;'>{d_tr}</td>
          <td>{row["içerik"]}</td>
          <td style='color:{cs_col};font-weight:600;text-align:center;'>{cs}</td>
          <td style='color:#475569;text-align:center;'>{ts}</td>
        </tr>"""

    st.markdown(f"""
    <table class="data-table" style="width:100%">
      <thead><tr>
        <th style='width:40px;'></th>
        <th>Platform</th>
        <th>Duygu</th>
        <th>İçerik</th>
        <th style='text-align:center;'>K.Skoru</th>
        <th style='text-align:center;'>Zaman</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>""", unsafe_allow_html=True)

    st.markdown(f"<p style='color:#475569; font-size:12px; margin-top:12px;'>{len(filtered)} sonuç gösteriliyor</p>", unsafe_allow_html=True)

# ─── TREND ANALİZİ ───────────────────────────────────────────────────────────
def show_trend_analysis(df, df_vol):
    st.markdown("<h1>📈 Trend Analizi</h1>", unsafe_allow_html=True)

    # İtibar skoru zaman serisi simülasyonu
    days = 30
    now = datetime.now()
    dates = [now - timedelta(days=days-i) for i in range(days)]
    np.random.seed(7)
    scores = 65 + np.cumsum(np.random.normal(0, 2, days))
    scores = np.clip(scores, 10, 95)
    # Spike
    scores[22:26] -= 18
    scores = np.clip(scores, 10, 95)

    fig_rep = go.Figure()
    fig_rep.add_trace(go.Scatter(
        x=dates, y=scores,
        mode="lines",
        line=dict(color="#8b5cf6", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(139,92,246,0.06)",
        name="İtibar Skoru"
    ))
    fig_rep.add_hline(y=50, line=dict(color="#ef4444", dash="dash", width=1),
                      annotation_text="Risk Eşiği", annotation_font_color="#ef4444",
                      annotation_font_size=11)
    fig_rep.update_layout(
        title=dict(text="İtibar Skoru Trendi (30 Gün)", font=dict(color="#f1f5f9", size=14)),
        plot_bgcolor="transparent", paper_bgcolor="transparent",
        font=dict(color="#64748b", size=11),
        xaxis=dict(gridcolor="#1e2a3a", tickformat="%d %b"),
        yaxis=dict(gridcolor="#1e2a3a", range=[0, 100]),
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        height=280
    )
    st.plotly_chart(fig_rep, use_container_width=True, config={"displayModeBar": False})

    col1, col2 = st.columns(2)

    with col1:
        # Platform karşılaştırma
        plat_time = df.groupby(["platform","duygu"]).size().unstack(fill_value=0).reset_index()
        plat_time.columns.name = None
        for col in ["positive","neutral","negative"]:
            if col not in plat_time.columns:
                plat_time[col] = 0
        fig_grouped = go.Figure(data=[
            go.Bar(name="Pozitif", x=plat_time["platform"], y=plat_time["positive"],
                   marker_color="#22c55e", opacity=0.85),
            go.Bar(name="Nötr",    x=plat_time["platform"], y=plat_time["neutral"],
                   marker_color="#64748b", opacity=0.85),
            go.Bar(name="Negatif", x=plat_time["platform"], y=plat_time["negative"],
                   marker_color="#ef4444", opacity=0.85),
        ])
        fig_grouped.update_layout(
            barmode="stack",
            title=dict(text="Platform Bazlı Duygu Dağılımı", font=dict(color="#f1f5f9",size=13)),
            plot_bgcolor="transparent", paper_bgcolor="transparent",
            font=dict(color="#64748b",size=11),
            xaxis=dict(gridcolor="#1e2a3a"),
            yaxis=dict(gridcolor="#1e2a3a"),
            legend=dict(font=dict(color="#94a3b8",size=10), orientation="h", y=-0.15),
            margin=dict(l=0,r=0,t=40,b=0),
            height=260
        )
        st.plotly_chart(fig_grouped, use_container_width=True, config={"displayModeBar": False})

    with col2:
        # Kriz skoru dağılımı histogram
        neg_only = df[df["duygu"]=="negative"]["kriz_skoru"]
        fig_hist = go.Figure(go.Histogram(
            x=neg_only, nbinsx=10,
            marker=dict(
                color=["#22c55e" if x<3 else "#eab308" if x<6 else "#ef4444"
                       for x in np.linspace(0,10,10)],
                line=dict(color="#0a0e1a",width=1)
            ),
            opacity=0.85
        ))
        fig_hist.update_layout(
            title=dict(text="Kriz Skoru Dağılımı (Olumsuz İçerikler)", font=dict(color="#f1f5f9",size=13)),
            plot_bgcolor="transparent", paper_bgcolor="transparent",
            font=dict(color="#64748b",size=11),
            xaxis=dict(gridcolor="#1e2a3a", title="Kriz Skoru"),
            yaxis=dict(gridcolor="#1e2a3a", title="İçerik Sayısı"),
            showlegend=False,
            margin=dict(l=0,r=0,t=40,b=0),
            height=260
        )
        st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

# ─── AYARLAR ────────────────────────────────────────────────────────────────
def show_settings():
    st.markdown("<h1>⚙️ Sistem Ayarları</h1>", unsafe_allow_html=True)

    col_s, _ = st.columns([1.4, 1])
    with col_s:
        st.markdown('<div class="section-title">Bildirim Eşikleri</div>', unsafe_allow_html=True)

        alert_thresh = st.slider("Kriz Şiddet Skoru Uyarı Eşiği", 1.0, 10.0, 5.0, 0.5)
        st.markdown(f"""
        <div style='padding:10px 14px; background:rgba(59,130,246,.06); border:1px solid rgba(59,130,246,.15);
                    border-radius:8px; font-size:12px; color:#64748b;'>
          Skor ≥ <b style='color:#f1f5f9;'>{alert_thresh}</b> olduğunda otomatik e-posta gönderilir
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">İzlenen Platformlar</div>', unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            p1 = st.checkbox("Haber Portalları", value=True)
            p2 = st.checkbox("Ekşi Sözlük", value=True)
        with col_c2:
            p3 = st.checkbox("Şikayetvar", value=True)
            p4 = st.checkbox("Twitter/X", value=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Tarama Frekansı</div>', unsafe_allow_html=True)
        mode = st.select_slider(
            "Normal mod tarama aralığı",
            options=["15 dk", "30 dk", "45 dk", "60 dk"],
            value="30 dk"
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Geri Bildirim: Son Bildirimler</div>', unsafe_allow_html=True)
        st.markdown("""
        <p style='font-size:13px; color:#64748b;'>
          Aşağıdaki bildirimleri etiketleyerek sistemin kalibrasyonuna katkı sağlayabilirsiniz.
        </p>""", unsafe_allow_html=True)

        sample_alerts = [
            {"ts": "12.01 09:22", "platform": "Şikayetvar", "özet": "Ürün kalitesiyle ilgili şikayetler artışı", "skor": 5.8},
            {"ts": "11.01 16:45", "platform": "Ekşi Sözlük", "özet": "Müşteri hizmetleri başlığı açıldı",         "skor": 3.2},
        ]
        for i, al in enumerate(sample_alerts):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.markdown(f"""
                <div style='padding:10px 12px; background:#111827; border:1px solid #1e2a3a;
                            border-radius:8px; font-size:12px;'>
                  <span style='color:#475569;'>{al['ts']} · {al['platform']}</span><br>
                  <span style='color:#94a3b8;'>{al['özet']}</span>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.button("✅ Gerçek Kriz", key=f"real_{i}")
            with c3:
                st.button("❌ Kriz Değil", key=f"not_{i}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾  Ayarları Kaydet"):
            st.success("✅ Ayarlar kaydedildi.")

# ─── ANA AKIŞ ────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    show_login()
else:
    show_dashboard()
