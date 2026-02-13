import streamlit as st
import pandas as pd
import plotly.express as px

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Performans İtiraz Yönetim Paneli", layout="wide", page_icon="📊")

# --- SABİT LİSTELER ---
ISTANBUL_ILCELERI = ["TÜMÜ"] + [
    "ADALAR", "ARNAVUTKÖY", "ATAŞEHİR", "AVCILAR", "BAĞCILAR", "BAHÇELİEVLER", "BAKIRKÖY", "BAŞAKŞEHİR",
    "BAYRAMPAŞA", "BEŞİKTAŞ", "BEYKOZ", "BEYLİKDÜZÜ", "BEYOĞLU", "BÜYÜKÇEKMECE", "ÇATALCA", "ÇEKMEKÖY",
    "ESENLER", "ESENYURT", "EYÜPSULTAN", "FATİH", "GAZİOSMANPAŞA", "GÜNGÖREN", "KADIKÖY", "KAĞITHANE",
    "KARTAL", "KÜÇÜKÇEKMECE", "MALTEPE", "PENDİK", "SANCAKTEPE", "SARIYER", "SİLİVRİ", "SULTANBEYLİ",
    "SULTANGAZİ", "ŞİLE", "ŞİŞLİ", "TUZLA", "ÜMRANİYE", "ÜSKÜDAR", "ZEYTİNBURNU"
]

AYLAR = ["TÜMÜ", "OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"]
YILLAR = [str(y) for y in range(2025, 2030)]

AY_NO_MAP = {
    "OCAK": "01", "ŞUBAT": "02", "MART": "03", "NİSAN": "04", "MAYIS": "05", "HAZİRAN": "06",
    "TEMMUZ": "07", "AĞUSTOS": "08", "EYLÜL": "09", "EKİM": "10", "KASIM": "11", "ARALIK": "12"
}

# --- ANA UYGULAMA ---
st.title("📊 Performans İtiraz Yönetim Paneli")

# --- SOL MENÜ ---
with st.sidebar:
    st.header("📂 Veri Girişi")
    uploaded_file = st.file_uploader("DOSYA YÜKLE (Excel)", type=['xlsx'])
    st.markdown("---")
    
    st.header("⚙️ Filtre Ayarları")
    ilce_adi = st.selectbox("İlçe Filtrele", ISTANBUL_ILCELERI, index=0)
    
    col_ay, col_yil = st.columns(2)
    secilen_ay = col_ay.selectbox("Ay", AYLAR, index=0)
    secilen_yil = col_yil.selectbox("Yıl", YILLAR, index=1)
    
    if ilce_adi == "TÜMÜ":
        baslik_ilce = "İSTANBUL (GENEL)"
    else:
        baslik_ilce = f"{ilce_adi} İLÇESİ"

    if secilen_ay == "TÜMÜ":
        baslik_donem = f"{secilen_yil} (TÜM AYLAR)"
    else:
        baslik_donem = f"{secilen_ay} / {secilen_yil}"
        
    st.success(f"Seçili: {baslik_ilce} - {baslik_donem}")

# --- İŞLEM ---
if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file)
    except:
        st.error("Dosya formatı hatalı.")
        st.stop()
    
    # --- FİLTRELEME ---
    df_filtered = df_raw.copy()
    
    # 1. İlçe Filtresi
    ilce_col = next((col for col in df_filtered.columns if "İLÇE" in col.upper()), None)
    if ilce_adi != "TÜMÜ" and ilce_col:
        df_filtered = df_filtered[df_filtered[ilce_col] == ilce_adi]

    # 2. Dönem Filtresi
    if secilen_ay != "TÜMÜ":
        hedef_donem = f"{secilen_yil}-{AY_NO_MAP[secilen_ay]}"
        donem_col = next((col for col in df_filtered.columns if "DÖNEM" in col.upper() or "PERFORMANS" in col.upper()), None)
        if donem_col: df_filtered = df_filtered[df_filtered[donem_col].astype(str).str.contains(hedef_donem, na=False)]

    if len(df_filtered) == 0:
        st.error("⚠️ Seçilen filtrelere uygun kayıt bulunamadı.")
        st.stop()

    # --- YARDIMCI FONKSİYONLAR ---
    def safe_count(df, col_name):
        """Hücre dolu mu boş mu sayar"""
        if col_name not in df.columns: return 0
        s = df[col_name].astype(str).replace(['nan', 'NaN', 'None', 'NAT', '<NA>'], '').str.strip()
        return (s != '').sum()

    def count_contains(df, col_keywords, search_term):
        """Belirli bir sütunda kelime arar"""
        col_name = next((col for col in df.columns if any(k in col.upper() for k in col_keywords)), None)
        if not col_name: return 0
        
        # Türkçe karakter normalizasyonu
        s = df[col_name].astype(str).str.upper().str.replace('İ', 'I').str.replace('Ğ', 'G').str.replace('Ü', 'U').str.replace('Ş', 'S').str.replace('Ö', 'O').str.replace('Ç', 'C')
        search_term = search_term.upper().replace('İ', 'I').replace('Ğ', 'G').replace('Ü', 'U').replace('Ş', 'S').replace('Ö', 'O').replace('Ç', 'C')
        
        return s.str.contains(search_term, na=False).sum()

    # =========================================================================
    # ANALİZ PANELİ
    # =========================================================================
    
    st.subheader(f"📊 {baslik_ilce} - {baslik_donem} Özeti")
    
    # --- 1. TEMEL KPI'LAR ---
    count_gebe = safe_count(df_filtered, "GEBE İZLEM")
    count_lohusa = safe_count(df_filtered, "LOHUSA İZLEM")
    count_bebek = safe_count(df_filtered, "BEBEK İZLEM")
    count_cocuk = safe_count(df_filtered, "ÇOCUK İZLEM")
    total_itiraz = len(df_filtered)

    cols = st.columns(5)
    cols[0].metric("Toplam İtiraz", total_itiraz, border=True)
    cols[1].metric("Gebe İzlem", count_gebe, border=True)
    cols[2].metric("Lohusa İzlem", count_lohusa, border=True)
    cols[3].metric("Bebek İzlem", count_bebek, border=True)
    cols[4].metric("Çocuk İzlem", count_cocuk, border=True)
    
    st.markdown("---")

    # --- 2. ASM ONAM VE İLÇE TEYİT ANALİZİ ---
    col_asm, col_ilce = st.columns(2)

    with col_asm:
        st.info("📝 **ASM Onam Durumu**")
        asm_onam_keywords = ["ASM ONAM", "ONAM"]
        count_imzali = count_contains(df_filtered, asm_onam_keywords, "IMZALI RED")
        count_imtina = count_contains(df_filtered, asm_onam_keywords, "IMTINA")
        
        ratio_imzali = (count_imzali / total_itiraz * 100) if total_itiraz > 0 else 0
        ratio_imtina = (count_imtina / total_itiraz * 100) if total_itiraz > 0 else 0
        
        c1, c2 = st.columns(2)
        c1.metric("İmzalı Red", count_imzali, f"%{ratio_imzali:.1f}")
        c2.metric("İmzadan İmtina", count_imtina, f"%{ratio_imtina:.1f}")
        
        df_onam = pd.DataFrame({
            "Durum": ["İmzalı Red", "İmzadan İmtina", "Diğer"],
            "Adet": [count_imzali, count_imtina, total_itiraz - (count_imzali + count_imtina)]
        })
        fig_onam = px.pie(df_onam, values='Adet', names='Durum', hole=0.4, 
                          color_discrete_map={'İmzalı Red':'#FF6B6B', 'İmzadan İmtina':'#FFA502', 'Diğer':'#f1f2f6'})
        fig_onam.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_onam, use_container_width=True)

    with col_ilce:
        st.info("🔍 **İlçe Sağlık Teyit Yöntemi**")
        teyit_keywords = ["İLÇE SAĞLIK TEYİT", "İLÇE TEYİT", "TEYİT SONUCU"]
        count_telefon = count_contains(df_filtered, teyit_keywords, "TELEFON")
        count_ev = count_contains(df_filtered, teyit_keywords, "EV")
        
        ratio_telefon = (count_telefon / total_itiraz * 100) if total_itiraz > 0 else 0
        ratio_ev = (count_ev / total_itiraz * 100) if total_itiraz > 0 else 0
        
        c3, c4 = st.columns(2)
        c3.metric("Telefonla Teyit", count_telefon, f"%{ratio_telefon:.1f}")
        c4.metric("Ev Ziyareti", count_ev, f"%{ratio_ev:.1f}")
        
        df_teyit = pd.DataFrame({
            "Yöntem": ["Telefon", "Ev Ziyareti", "Diğer/Belirsiz"],
            "Adet": [count_telefon, count_ev, total_itiraz - (count_telefon + count_ev)]
        })
        fig_teyit = px.bar(df_teyit, x="Yöntem", y="Adet", text_auto=True, color="Yöntem",
                           color_discrete_map={'Telefon':'#1dd1a1', 'Ev Ziyareti':'#54a0ff', 'Diğer/Belirsiz':'#c8d6e5'})
        fig_teyit.update_layout(height=250, margin=dict(t=10, b=0, l=0, r=0), showlegend=False)
        st.plotly_chart(fig_teyit, use_container_width=True)

    st.markdown("---")

    # --- 3. RED NEDENLERİ ANALİZİ (BÖLÜNMÜŞ VE BİRLEŞTİRİLMİŞ) ---
    st.subheader("🚫 Red Nedenleri Analizi (ASM + İlçe Sağlık)")
    
    # İlgili sütunları bul
    col_asm_red = next((col for col in df_filtered.columns if "ASM RED" in col.upper()), None)
    col_ilce_red = next((col for col in df_filtered.columns if "İLÇE SAĞLIK RED" in col.upper() or "İLÇE RED" in col.upper()), None)

    all_red_reasons = []

    def process_and_add_reasons(df, col_name, target_list):
        if col_name and col_name in df.columns:
            # Sütundaki tüm verileri string olarak al ve NaN'ları at
            raw_list = df[col_name].dropna().astype(str).tolist()
            
            for item in raw_list:
                # 1. '|' işaretine göre böl
                parts = item.split('|')
                
                for part in parts:
                    # 2. Temizle
                    clean_part = part.strip()
                    # 3. Anlamsız verileri filtrele (Nan, 0, -, boşluk)
                    if len(clean_part) > 2 and clean_part.lower() not in ['nan', 'none', '0', '-', 'yok']:
                        target_list.append(clean_part)

    # Her iki sütunu da işle
    process_and_add_reasons(df_filtered, col_asm_red, all_red_reasons)
    process_and_add_reasons(df_filtered, col_ilce_red, all_red_reasons)

    if all_red_reasons:
        # Pandas Serisine çevirip saydır
        red_series = pd.Series(all_red_reasons)
        red_counts = red_series.value_counts().reset_index()
        red_counts.columns = ["Red Nedeni", "Sayı"]
        
        # İlk 15 Nedeni Göster (Liste uzayabilir)
        top_red_reasons = red_counts.head(15)
        
        col_r1, col_r2 = st.columns([2, 1])
        
        with col_r1:
             fig_red = px.pie(top_red_reasons, values='Sayı', names='Red Nedeni', 
                              title='En Sık Karşılaşılan Red Nedenleri', hole=0.4)
             st.plotly_chart(fig_red, use_container_width=True)
             
        with col_r2:
            st.write("**Detaylı Liste**")
            st.dataframe(red_counts, use_container_width=True, height=350, hide_index=True)
            
    else:
        st.info("Red nedeni içeren veri bulunamadı veya sütun isimleri eşleşmedi.")

    st.markdown("---")

    # --- 4. AŞI VE İLÇE GRAFİKLERİ ---
    col_a1, col_a2 = st.columns([2, 1])

    with col_a1:
        st.subheader("💉 Aşı Türüne Göre İtirazlar")
        asi_listesi = ["DaBT-İPA-Hib-Hep-B", "HEP B", "BCG", "KKK", "HEP A", "KPA", "OPA", "SUÇİÇEĞİ", "DaBT-İPA", "TD"]
        
        asi_verileri = []
        for asi in asi_listesi:
            count = safe_count(df_filtered, asi)
            if count > 0:
                asi_verileri.append({"Aşı Adı": asi, "İtiraz Sayısı": count})
        
        if asi_verileri:
            df_asi = pd.DataFrame(asi_verileri).sort_values("İtiraz Sayısı", ascending=True)
            fig_asi = px.bar(df_asi, x="İtiraz Sayısı", y="Aşı Adı", text_auto=True, orientation='h', color="İtiraz Sayısı")
            st.plotly_chart(fig_asi, use_container_width=True)
        else:
            st.warning("Veri setinde aşı itirazı bulunamadı.")

    with col_a2:
        st.subheader("🏙️ İlçe Dağılımı")
        if ilce_col:
            df_ilce = df_filtered[ilce_col].value_counts().reset_index()
            df_ilce.columns = ["İlçe", "Adet"]
            df_ilce = df_ilce.sort_values("Adet", ascending=True).tail(15) 
            
            fig_bar_ilce = px.bar(df_ilce, x="Adet", y="İlçe", text_auto=True, orientation='h')
            fig_bar_ilce.update_layout(height=450)
            st.plotly_chart(fig_bar_ilce, use_container_width=True)
        else:
            st.warning("İlçe sütunu bulunamadı.")

else:
    st.info("👈 Analiz paneline erişmek için lütfen sol menüden Excel dosyanızı yükleyiniz.")
