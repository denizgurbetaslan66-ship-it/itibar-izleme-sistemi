"""
NLP ve Skorlama Modülü
Türkçe duygu analizi ve kriz tespiti yardımcı fonksiyonları

NOT: Bu modül gerçek bir NLP pipeline'ın yerini tutan kural-tabanlı bir prototiptir.
Üretim versiyonunda BERTurk/transformers fine-tuning entegrasyonu planlanmaktadır.
"""

import re
import numpy as np
from datetime import datetime, timedelta


# ─── TÜRKÇE DUYGU KELİME HAZİNELERİ ────────────────────────────────────────

NEGATIVE_STRONG = {
    "dolandırıcılık", "rezalet", "berbat", "korkunç", "felaket",
    "tehlikeli", "sahte", "yanıltıcı", "yalan", "skandal",
    "utanç", "kötü", "bozuk", "arızalı", "çalışmıyor",
    "iade", "şikayet", "hile", "aldatmaca", "zavallı"
}

NEGATIVE_MILD = {
    "hayal kırıklığı", "memnun değilim", "beklentimi karşılamadı",
    "geç geldi", "yavaş", "pahalı", "eksik", "hata", "sorun",
    "problem", "zorluk", "dikkat", "uyarı", "eleştiri"
}

POSITIVE = {
    "harika", "mükemmel", "muhteşem", "süper", "başarılı",
    "teşekkür", "memnun", "kaliteli", "hızlı", "güvenilir",
    "tavsiye", "sevdim", "beğendim", "iyi", "güzel", "başarı",
    "ödül", "lider", "örnek", "güven"
}

# Yüksek öncelikli kriz anahtar kelimeleri
CRISIS_KEYWORDS = {
    "dolandırıcılık": 3.0,
    "sağlık riski": 3.0,
    "kaza": 2.5,
    "zehir": 3.0,
    "tehlike": 2.5,
    "ölüm": 3.0,
    "dava": 2.0,
    "savcılık": 2.5,
    "haciz": 2.0,
    "iflas": 2.0,
    "kapatıldı": 1.8,
    "skandal": 2.0,
    "sahte": 2.0,
    "hile": 2.0,
}

# İroni kalıpları (Ekşi Sözlük tarzı)
IRONY_PATTERNS = [
    r"ne kadar\s+\w+\s+(değil mi|ya|hani)",
    r"(tabi ki|tabii ki|elbette)\s+\w+",
    r"(bravo|helal|alkış)\s+(sana|size|olsun)",
    r"çok\s+(profesyonel|kaliteli|başarılı)\s+(yani|ha|ya)",
]

IRONY_REGEX = [re.compile(p, re.IGNORECASE) for p in IRONY_PATTERNS]


def simple_sentiment(text: str) -> dict:
    """
    Kural tabanlı Türkçe duygu analizi.
    Returns: {"label": "positive"|"negative"|"neutral", "score": float, "irony": bool}
    """
    text_lower = text.lower()
    tokens = set(text_lower.split())

    neg_strong_hits = len(tokens & NEGATIVE_STRONG)
    neg_mild_hits   = len(tokens & NEGATIVE_MILD)
    pos_hits        = len(tokens & POSITIVE)

    irony_detected = any(p.search(text_lower) for p in IRONY_REGEX)

    raw_score = (pos_hits * 1.0) - (neg_strong_hits * 2.0) - (neg_mild_hits * 0.8)

    if irony_detected and raw_score > 0:
        raw_score = -raw_score * 0.7  # İroni tespit edilince skoru negatife çevir

    if raw_score > 0.5:
        label = "positive"
        confidence = min(0.5 + raw_score * 0.2, 0.95)
    elif raw_score < -0.5:
        label = "negative"
        confidence = min(0.5 + abs(raw_score) * 0.2, 0.95)
    else:
        label = "neutral"
        confidence = 0.55

    return {
        "label": label,
        "confidence": round(confidence, 2),
        "irony": irony_detected,
        "neg_strong": neg_strong_hits,
        "neg_mild": neg_mild_hits,
        "pos": pos_hits,
    }


def crisis_keyword_boost(text: str) -> float:
    """Kriz anahtar kelime tespiti — ek şiddet puanı döndürür."""
    text_lower = text.lower()
    boost = 0.0
    for kw, weight in CRISIS_KEYWORDS.items():
        if kw in text_lower:
            boost += weight
    return min(boost, 4.0)  # Max 4 puan ek boost


def compute_crisis_score(mentions: list) -> float:
    """
    Mention listesinden Kriz Şiddet Skoru hesapla (1–10).
    
    Her mention dict formatı:
    {
        "text": str,
        "platform": str,
        "timestamp": datetime,
        "sentiment": str  # "positive"|"negative"|"neutral"
    }
    """
    if not mentions:
        return 0.0

    now = datetime.now()
    recent_24h = [m for m in mentions
                  if (now - m.get("timestamp", now)).total_seconds() < 86400]

    if not recent_24h:
        return 0.0

    neg_recent = [m for m in recent_24h if m.get("sentiment") == "negative"]
    if not neg_recent:
        return 0.0

    # 1. Yayılma hızı (velocity): son 24h negatif / toplam
    velocity = len(neg_recent) / max(len(mentions), 1) * 10

    # 2. Platform çeşitliliği
    platforms = {m.get("platform", "unknown") for m in neg_recent}
    cross_platform = len(platforms) / 4.0 * 10  # 4 platform = max

    # 3. Kriz keyword boost
    kw_boost = np.mean([crisis_keyword_boost(m.get("text","")) for m in neg_recent])

    # 4. Ağırlıklı bileşim
    raw = velocity * 0.35 + cross_platform * 0.30 + kw_boost * 0.35
    return round(min(raw * 1.15, 10.0), 1)


def compute_reputation_score(mentions: list, window_hours: int = 72) -> int:
    """
    İtibar Skoru (0–100) hesapla.
    
    Platform ağırlıkları:
      haber        = 3.0
      şikayetvar   = 2.0
      twitter      = 2.0
      ekşi sözlük  = 1.5
      instagram    = 1.0
    """
    if not mentions:
        return 50

    PLATFORM_WEIGHTS = {
        "haber": 3.0,
        "şikayetvar": 2.0,
        "twitter": 2.0,
        "ekşi sözlük": 1.5,
        "instagram": 1.0,
    }
    SENTIMENT_SCORES = {"positive": 100, "neutral": 50, "negative": 0}

    now = datetime.now()
    cutoff = now - timedelta(hours=window_hours)
    windowed = [m for m in mentions if m.get("timestamp", now) >= cutoff]

    if not windowed:
        return 50

    total_weight, total_score = 0.0, 0.0
    for m in windowed:
        age_h   = max(1, (now - m.get("timestamp", now)).total_seconds() / 3600)
        recency = np.exp(-age_h / 48)  # Üstel azalma
        pw      = PLATFORM_WEIGHTS.get(m.get("platform", ""), 1.0)
        weight  = pw * recency
        sent_sc = SENTIMENT_SCORES.get(m.get("sentiment", "neutral"), 50)

        total_weight += weight
        total_score  += sent_sc * weight

    return round(total_score / total_weight) if total_weight > 0 else 50


def format_alert_email(kurum: str, crisis_score: float,
                        platforms: list, summary: str,
                        urgency: str = "ORTA") -> str:
    """Otomatik e-posta bildirim metni üret."""
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    platform_str = ", ".join(platforms) if platforms else "—"

    return f"""
Konu: [İtibar Sistemi] Kriz Uyarısı — {urgency} Seviye | {kurum}

Sayın Yetkili,

{now} itibarıyla {kurum} hakkında erken uyarı sistemi tetiklenmiştir.

───────────────────────────────────────
KRİZ ŞİDDET SKORU : {crisis_score:.1f} / 10
ÖNERİLEN ACİLİYET : {urgency}
GÖRÜLDÜĞÜ PLATFORMLAR: {platform_str}
───────────────────────────────────────

KONU ÖZETİ:
{summary}

Önerilen Aksiyon:
- Dashboard'ı inceleyiniz ve ilgili içerikleri gözden geçiriniz.
- Gerekiyorsa kurumsal iletişim biriminizi bildiriniz.
- Bildirimi "Gerçek Kriz" veya "Kriz Değil" olarak etiketleyiniz 
  (sistem kalibrasyonuna katkı sağlar).

Sisteme erişmek için: http://localhost:8501

─────────────────────────────────────────────────────
Bu mesaj Erken İtibar Krizi Tespit Sistemi tarafından 
otomatik olarak oluşturulmuştur.
TÜBİTAK 1002 Proje Prototipi — Çankaya Üniversitesi
─────────────────────────────────────────────────────
""".strip()
