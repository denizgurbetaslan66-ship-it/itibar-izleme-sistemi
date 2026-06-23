"""
Veri Toplama Modülü
RSS akışlarından gerçek zamanlı içerik toplama

KULLANIM:
  collector = DataCollector(kurum_adi="TechMarka A.Ş.", anahtar_kelimeler=["techmarka","tech marka"])
  df = collector.fetch_all()

NOT: Bu modül gerçek RSS kaynaklarını çeker. Platform API/RSS kısıtlamaları
nedeniyle bazı kaynaklar demo modunda simüle edilmektedir.
"""

import feedparser
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
import re

logger = logging.getLogger(__name__)


# ─── RSS KAYNAKLARI ──────────────────────────────────────────────────────────
NEWS_FEEDS = [
    {"name": "Hürriyet",      "url": "https://www.hurriyet.com.tr/rss/anasayfa"},
    {"name": "Sabah",         "url": "https://www.sabah.com.tr/rss/anasayfa.xml"},
    {"name": "NTV",           "url": "https://www.ntv.com.tr/son-dakika.rss"},
    {"name": "Milliyet",      "url": "https://www.milliyet.com.tr/rss/rssNew/anaSayfa.xml"},
    {"name": "Cumhuriyet",    "url": "https://www.cumhuriyet.com.tr/rss/son_dakika.xml"},
]

# Gelecekte entegre edilecek platformlar (API gerektirir)
FUTURE_PLATFORMS = {
    "eksi_sozluk": "https://eksisozluk.com/basliklar/gundem",  # RSS yok, scraping gerekir
    "sikayetvar":  "https://www.sikayetvar.com/",               # API gerektirir
    "twitter":     "Twitter API v2",                             # Bearer token gerektirir
}


class DataCollector:
    """
    Kuruma özel içerik toplayıcı.
    
    Attributes:
        kurum_adi:        İzlenecek kurum adı
        anahtar_kelimeler: Aramada kullanılacak kelimeler listesi
        lookback_hours:   Kaç saate kadar geriye gidilsin
    """

    def __init__(self, kurum_adi: str, anahtar_kelimeler: list = None,
                 lookback_hours: int = 48):
        self.kurum_adi          = kurum_adi
        self.anahtar_kelimeler  = anahtar_kelimeler or [kurum_adi.lower()]
        self.lookback_hours     = lookback_hours
        self._cache             = {}
        self._last_fetch        = None

    def _is_relevant(self, text: str) -> bool:
        """İçeriğin kurumla ilgili olup olmadığını kontrol eder."""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.anahtar_kelimeler)

    def _parse_date(self, entry) -> datetime:
        """feedparser'dan datetime çıkar."""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        return datetime.now()

    def fetch_rss_news(self) -> list:
        """Haber RSS akışlarını çekip filtreler."""
        results = []
        cutoff  = datetime.now() - timedelta(hours=self.lookback_hours)

        for feed_info in NEWS_FEEDS:
            try:
                feed = feedparser.parse(feed_info["url"])
                for entry in feed.entries:
                    title   = entry.get("title", "")
                    summary = entry.get("summary", "")
                    text    = f"{title} {summary}"

                    if not self._is_relevant(text):
                        continue

                    pub_date = self._parse_date(entry)
                    if pub_date < cutoff:
                        continue

                    results.append({
                        "platform":  feed_info["name"],
                        "platform_type": "haber",
                        "başlık":    title,
                        "özet":      summary[:300],
                        "url":       entry.get("link", ""),
                        "zaman":     pub_date,
                        "ham_metin": text,
                    })
                time.sleep(0.3)  # Rate limiting

            except Exception as e:
                logger.warning(f"{feed_info['name']} RSS hatası: {e}")

        return results

    def fetch_all(self) -> pd.DataFrame:
        """
        Tüm kaynaklardan veri çekip DataFrame döndürür.
        Gerçek RSS + simüle edilmiş platform verileri birleştirilir.
        """
        all_results = []

        # Gerçek RSS haberleri
        news = self.fetch_rss_news()
        all_results.extend(news)

        # Ekşi Sözlük simülasyonu (gerçek entegrasyon için scraping/API gerekli)
        all_results.extend(self._simulate_eksi_entries())

        # Şikayetvar simülasyonu
        all_results.extend(self._simulate_sikayetvar_entries())

        if not all_results:
            return pd.DataFrame(columns=[
                "platform","platform_type","başlık","özet","url","zaman","ham_metin"
            ])

        df = pd.DataFrame(all_results)
        df = df.sort_values("zaman", ascending=False).reset_index(drop=True)
        self._last_fetch = datetime.now()
        return df

    def _simulate_eksi_entries(self) -> list:
        """Ekşi Sözlük benzeri içerik simülasyonu."""
        import random
        templates = [
            f"{self.kurum_adi} son zamanlarda kalite düşüşü yaşıyor galiba",
            f"biri {self.kurum_adi} müşteri hizmetlerini aradı mı, ulaşamıyorum",
            f"{self.kurum_adi} ürününü aldım gayet memnunum",
            f"{self.kurum_adi} hakkında şikayet yazmak istiyorum ama nereye yazayım",
        ]
        results = []
        now = datetime.now()
        for i, t in enumerate(templates):
            if self._is_relevant(t):
                results.append({
                    "platform": "ekşi sözlük",
                    "platform_type": "forum",
                    "başlık": t[:80],
                    "özet": t,
                    "url": f"https://eksisozluk.com/simulated/{i}",
                    "zaman": now - timedelta(hours=random.randint(1, 36)),
                    "ham_metin": t,
                })
        return results

    def _simulate_sikayetvar_entries(self) -> list:
        """Şikayetvar benzeri içerik simülasyonu."""
        import random
        templates = [
            f"{self.kurum_adi} siparişim 10 gündür gelmedi iade istiyorum",
            f"{self.kurum_adi} ürünü hasarlı geldi kutu bile açılmamıştı",
            f"{self.kurum_adi} çok hızlı kargo yaptı teşekkürler",
        ]
        results = []
        now = datetime.now()
        for i, t in enumerate(templates):
            results.append({
                "platform": "şikayetvar",
                "platform_type": "şikayet",
                "başlık": t[:80],
                "özet": t,
                "url": f"https://www.sikayetvar.com/simulated/{i}",
                "zaman": now - timedelta(hours=random.randint(2, 24)),
                "ham_metin": t,
            })
        return results


def adaptive_scan_interval(crisis_score: float,
                            base_minutes: int = 30) -> int:
    """
    Adaptif tarama: kriz skoru yükseldikçe aralığı kısalt.
    
    Returns: Tarama aralığı (dakika cinsinden)
    """
    if crisis_score >= 7:
        return 5
    elif crisis_score >= 5:
        return 10
    elif crisis_score >= 3:
        return 15
    return base_minutes
