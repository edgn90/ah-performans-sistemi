import streamlit as st
import pandas as pd
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Performans İtiraz Sistemi", layout="wide", page_icon="⚖️")

# --- SABİT LİSTELER ---
ISTANBUL_ILCELERI = [
    "ADALAR", "ARNAVUTKÖY", "ATAŞEHİR", "AVCILAR", "BAĞCILAR", "BAHÇELİEVLER", "BAKIRKÖY", "BAŞAKŞEHİR",
    "BAYRAMPAŞA", "BEŞİKTAŞ", "BEYKOZ", "BEYLİKDÜZÜ", "BEYOĞLU", "BÜYÜKÇEKMECE", "ÇATALCA", "ÇEKMEKÖY",
    "ESENLER", "ESENYURT", "EYÜPSULTAN", "FATİH", "GAZİOSMANPAŞA", "GÜNGÖREN", "KADIKÖY", "KAĞITHANE",
    "KARTAL", "KÜÇÜKÇEKMECE", "MALTEPE", "PENDİK", "SANCAKTEPE", "SARIYER", "SİLİVRİ", "SULTANBEYLİ",
    "SULTANGAZİ", "ŞİLE", "ŞİŞLİ", "TUZLA", "ÜMRANİYE", "ÜSKÜDAR", "ZEYTİNBURNU"
]

AYLAR = ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"]
YILLAR = [str(y) for y in range(2025, 2030)]

# --- SÜTUN EŞLEŞTİRME ---
COLUMN_MAPPING = {
    "SIRA NO": "OTOMATIK", 
    "ASM ADI": "ASM ADI",
    "HEKİM BİRİM NO": "HEKİM BİRİM NO",
    "HEKİM ADI SOYADI": "HEKİM ADI SOYADI",
    "HEKİM-ASÇ TC KİMLİK NO": "HEKİM-ASÇ TC KİMLİK NO",
    "İTİRAZ SEBEBİ": "İTİRAZ SEBEBİ",
    "İTİRAZ KONUSU": "İTİRAZ NEDENİ",
    "İTİRAZ KONUSU KİŞİNİN ADI SOYADI": "İTİRAZ KONUSU KİŞİNİN ADI SOYADI",
    "İTİRAZ KONUSU KİŞİNİN TC KİMLİK NO": "İTİRAZ KONUSU KİŞİNİN TC KİMLİK NO",
    "GEBE İZLEM": "GEBE İZLEM", "LOHUSA İZLEM": "LOHUSA İZLEM", "BEBEK İZLEM": "BEBEK İZLEM", "ÇOCUK İZLEM": "ÇOCUK İZLEM",
    "DaBT-İPA-Hib-Hep-B": "DaBT-İPA-Hib-Hep-B", "HEP B": "HEP B", "BCG": "BCG", "KKK": "KKK", "HEP A": "HEP A",
    "KPA": "KPA", "OPA": "OPA", "SUÇİÇEĞİ": "SU ÇİÇEĞİ", "DaBT-İPA": "DaBT-İPA", "TD": "TD",
    "KABUL": "KABUL", "RED": "RED", "GEREKSİZ BAŞVURU": "GEREKSİZ BAŞVURU", "KARAR AÇIKLAMASI": "KARAR AÇIKLAMASI"
}
ISTENEN_SUTUNLAR = list(COLUMN_MAPPING.keys())

# --- ANA UYGULAMA ---
st.title("⚖️ Performans İtiraz Rapor Paneli")

# --- SOL MENÜ ---
with st.sidebar:
    st.header("📂 Veri Girişi")
    uploaded_file = st.file_uploader("DOSYA YÜKLE (Excel)", type=['xlsx'])
    st.markdown("---")
    
    st.header("⚙️ Rapor Ayarları")
    ilce_adi = st.selectbox("İlçe Seçiniz", ISTANBUL_ILCELERI, index=36)
    col_ay, col_yil = st.columns(2)
    secilen_ay = col_ay.selectbox("Ay", AYLAR)
    secilen_yil = col_yil.selectbox("Yıl", YILLAR, index=1)
    donem = f"{secilen_ay} / {secilen_yil}"
    st.markdown("---")

    with st.expander("📝 KOMİSYON BİLGİLERİ", expanded=False):
        baskan = st.text_input("Komisyon Başkanı", "Dr. Adı Soyadı")
        st.markdown("---")
        uyeler = []
        for i in range(1, 6):
            uye = st.text_input(f"{i}. Üye Adı Soyadı", key=f"uye_{i}")
            if uye: uyeler.append(uye)

# --- İŞLEM ---
if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file)
    except:
        st.error("Dosya formatı hatalı.")
        st.stop()
    
    # Veri Temizleme
    df_final = pd.DataFrame()
    for target_col, source_col in COLUMN_MAPPING.items():
        if target_col == "SIRA NO": continue
        found_col = None
        for col in df_raw.columns:
            if source_col.lower() == col.lower(): found_col = col; break
            if source_col.replace(" ","").lower() == col.replace(" ","").lower(): found_col = col; break
        if found_col: df_final[target_col] = df_raw[found_col]
        else: df_final[target_col] = ""

    df_final["SIRA NO"] = range(1, len(df_final) + 1)
    df_final = df_final[ISTENEN_SUTUNLAR]
    df_final = df_final.fillna("")
    
    st.success(f"✅ {len(df_final)} Kayıt Hazırlandı.")
    st.info(f"📍 {ilce_adi} - 📅 {donem} dönemi için Excel raporu oluşturuluyor.")

    # --- EXCEL OLUŞTURMA ---
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, sheet_name='Rapor', startrow=4, index=False)
        workbook = writer.book
        worksheet = writer.sheets['Rapor']
        
        # Sayfa Ayarları (A4 Yatay Sığdır)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.fit_to_pages(1, 0)
        worksheet.set_margins(0.2, 0.2, 0.5, 0.5)
        
        # Formatlar
        fmt_wrap = workbook.add_format({'text_wrap': True, 'valign': 'vcenter', 'align': 'center', 'border': 1, 'font_size': 7})
        fmt_head = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#DDDDDD', 'border': 1, 'text_wrap': True, 'font_size': 8})
        fmt_title = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 11})
        fmt_imza_isim = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 9})
        fmt_imza_unvan = workbook.add_format({'align': 'center', 'font_size': 8, 'italic': True})

        # Başlıklar
        worksheet.merge_range('A1:AA1', "AİLE HEKİMLİĞİ PERFORMANS İTİRAZ DEĞERLENDİRME TABLOSU", fmt_title)
        worksheet.merge_range('A2:AA2', f"{ilce_adi} İLÇE SAĞLIK MÜDÜRLÜĞÜ", fmt_title)
        worksheet.merge_range('A3:AA3', f"DÖNEM: {donem}", fmt_title)
        
        # Veri Yazdırma
        for i, col in enumerate(df_final.columns): worksheet.write(4, i, col, fmt_head)
        for row_idx, row in df_final.iterrows():
            for col_idx, val in enumerate(row): worksheet.write(row_idx+5, col_idx, val, fmt_wrap)
        
        # --- İMZA BLOĞU DÜZENLEME (ORTALI VE EŞİT DAĞILIM) ---
        start_row = len(df_final) + 8
        total_cols = 27 # A'dan AA'ya kadar
        
        # 1. KOMİSYON ÜYELERİ (Yatay ve Eşit Aralıklı)
        if uyeler:
            num_members = len(uyeler)
            # Sayfa genişliğini üye sayısına bölerek eşit aralıkları bul
            step = total_cols / (num_members + 1)
            
            for i, member in enumerate(uyeler):
                # Her üyenin geleceği sütun indeksi (Matematiksel ortalama)
                col_pos = int(step * (i + 1))
                
                # İsim ve İmza yeri
                worksheet.write(start_row, col_pos, member, fmt_imza_isim)
                worksheet.write(start_row + 1, col_pos, "Üye (İmza)", fmt_imza_unvan)

        # 2. KOMİSYON BAŞKANI (Alt Satır, Tam Orta, Tek Başına)
        president_row = start_row + 4
        center_col = 13 # 27 sütunun tam ortası (Index 13 = N Sütunu)
        
        worksheet.write(president_row, center_col, baskan, fmt_imza_isim)
        worksheet.write(president_row + 1, center_col, "Komisyon Başkanı (İmza)", fmt_imza_unvan)

    st.download_button(
        label="📗 Excel Raporunu İndir",
        data=excel_buffer.getvalue(),
        file_name=f"{ilce_adi}_Rapor.xlsx",
        mime="application/vnd.ms-excel",
        use_container_width=True
    )

else:
    st.info("👈 Rapor oluşturmak için lütfen sol menüden Excel dosyanızı yükleyiniz.")
