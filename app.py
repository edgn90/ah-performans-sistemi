import streamlit as st
import pandas as pd
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Performans İtiraz Sistemi", layout="wide", page_icon="⚖️")

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

# --- SÜTUN EŞLEŞTİRME (SIRA NO -> SIRA OLARAK GÜNCELLENDİ) ---
COLUMN_MAPPING = {
    "SIRA": "OTOMATIK", # <--- GÜNCELLENDİ
    "ASM ADI": "ASM ADI",
    "HEKİM BİRİM NO": "HEKİM BİRİM NO",
    "HEKİM ADI SOYADI": "HEKİM ADI SOYADI",
    "HEKİM-ASÇ TC KİMLİK NO": "HEKİM-ASÇ TC KİMLİK NO",
    "İTİRAZ SEBEBİ": "İTİRAZ SEBEBİ",
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
    
    st.header("⚙️ Filtre Ayarları")
    ilce_adi = st.selectbox("İlçe Filtrele", ISTANBUL_ILCELERI, index=0)
    
    col_ay, col_yil = st.columns(2)
    secilen_ay = col_ay.selectbox("Ay", AYLAR, index=0)
    secilen_yil = col_yil.selectbox("Yıl", YILLAR, index=1)
    
    if ilce_adi == "TÜMÜ":
        baslik_ilce = "İSTANBUL İL SAĞLIK MÜDÜRLÜĞÜ (GENEL)"
    else:
        baslik_ilce = f"{ilce_adi} İLÇE SAĞLIK MÜDÜRLÜĞÜ"

    if secilen_ay == "TÜMÜ":
        baslik_donem = f"DÖNEM: {secilen_yil} (TÜM AYLAR)"
    else:
        baslik_donem = f"DÖNEM: {secilen_ay} / {secilen_yil}"
        
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
    
    # --- FİLTRELEME ---
    if ilce_adi != "TÜMÜ":
        ilce_col = next((col for col in df_raw.columns if "İLÇE" in col.upper()), None)
        if ilce_col: df_raw = df_raw[df_raw[ilce_col] == ilce_adi]

    if secilen_ay != "TÜMÜ":
        hedef_donem = f"{secilen_yil}-{AY_NO_MAP[secilen_ay]}"
        donem_col = next((col for col in df_raw.columns if "DÖNEM" in col.upper() or "PERFORMANS" in col.upper()), None)
        if donem_col: df_raw = df_raw[df_raw[donem_col].astype(str).str.contains(hedef_donem, na=False)]

    if len(df_raw) == 0:
        st.error("⚠️ Seçilen filtrelere uygun kayıt bulunamadı.")
        st.stop()

    # --- VERİ HAZIRLAMA ---
    df_final = pd.DataFrame()
    for target_col, source_col in COLUMN_MAPPING.items():
        if target_col == "SIRA": continue
        found_col = None
        for col in df_raw.columns:
            if source_col.lower() == col.lower(): found_col = col; break
            if source_col.replace(" ","").lower() == col.replace(" ","").lower(): found_col = col; break
        if found_col: df_final[target_col] = df_raw[found_col]
        else: df_final[target_col] = ""

    df_final["SIRA"] = range(1, len(df_final) + 1)
    df_final = df_final[ISTENEN_SUTUNLAR]
    df_final = df_final.fillna("")
    
    st.success(f"✅ {len(df_final)} Kayıt Hazırlandı.")
    st.info(f"📍 {baslik_ilce} - 📅 {baslik_donem}")

    # --- EXCEL OLUŞTURMA (ULTRA KOMPAKT) ---
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, sheet_name='Rapor', startrow=4, index=False)
        workbook = writer.book
        worksheet = writer.sheets['Rapor']
        
        # Sayfa Ayarları
        worksheet.set_landscape()
        worksheet.set_paper(9) # A4
        worksheet.fit_to_pages(1, 0)
        worksheet.set_margins(left=0.1, right=0.1, top=0.3, bottom=0.3)
        
        # --- FORMATLAR (FONT 5 PUNTO) ---
        fmt_std = workbook.add_format({
            'text_wrap': True, 'valign': 'vcenter', 'align': 'center', 'border': 1, 'font_size': 5
        })
        # TC Hücresi (Wrap KAPALI, Font 6) - Biraz daha büyük ki okunsun
        fmt_tc = workbook.add_format({
            'text_wrap': False, 'valign': 'vcenter', 'align': 'center', 'border': 1, 'font_size': 6, 'num_format': '0'
        })
        # Başlıklar (Font 6)
        fmt_head = workbook.add_format({
            'bold': True, 'align': 'center', 'bg_color': '#DDDDDD', 'border': 1, 'text_wrap': True, 'font_size': 6
        })
        fmt_title = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 9})
        fmt_imza_isim = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 7})
        fmt_imza_unvan = workbook.add_format({'align': 'center', 'font_size': 6, 'italic': True})

        # Üst Başlıklar
        worksheet.merge_range('A1:Z1', "AİLE HEKİMLİĞİ PERFORMANS İTİRAZ DEĞERLENDİRME TABLOSU", fmt_title)
        worksheet.merge_range('A2:Z2', baslik_ilce, fmt_title)
        worksheet.merge_range('A3:Z3', baslik_donem, fmt_title)
        
        # --- SÜTUN GENİŞLİKLERİ (OPTİMİZE EDİLDİ) ---
        # Amaç: Yazıların aşağı kaymasını engellemek için metin sütunlarını genişlet,
        # sayı sütunlarını daralt.
        
        column_widths = {
            "SIRA": 3,
            "ASM ADI": 12,
            "HEKİM BİRİM NO": 7,
            "HEKİM ADI SOYADI": 12,
            "HEKİM-ASÇ TC KİMLİK NO": 10, # Sığar (Font 6)
            "İTİRAZ SEBEBİ": 15,
            "İTİRAZ KONUSU KİŞİNİN ADI SOYADI": 12,
            "İTİRAZ KONUSU KİŞİNİN TC KİMLİK NO": 10,
            "KARAR AÇIKLAMASI": 18,
            "GEREKSİZ BAŞVURU": 4,
            "KABUL": 4,
            "RED": 4,
            # Varsayılan diğerleri (Aşılar vb.)
            "DEFAULT": 3.5 
        }

        for i, col_name in enumerate(df_final.columns):
            worksheet.write(4, i, col_name, fmt_head)
            
            # Genişlik Belirle
            width = column_widths.get(col_name, column_widths["DEFAULT"])
            
            # Eğer aşı isimleri çok uzunsa ve başlık sığmıyorsa, başlık wrap olur.
            # Veri 3.5 genişliğe sığar (çünkü veriler genelde boş veya sayı)
            worksheet.set_column(i, i, width)

        # Veri Yazdırma
        for row_idx, row in df_final.iterrows():
            for col_idx, val in enumerate(row):
                col_name = df_final.columns[col_idx]
                current_fmt = fmt_tc if "TC" in col_name else fmt_std
                worksheet.write(row_idx+5, col_idx, val, current_fmt)
        
        # --- İMZA BLOĞU ---
        start_row = len(df_final) + 8
        total_cols = 26 
        
        if uyeler:
            num_members = len(uyeler)
            step = total_cols / (num_members + 1)
            for i, member in enumerate(uyeler):
                col_pos = int(step * (i + 1))
                worksheet.write(start_row, col_pos, member, fmt_imza_isim)
                worksheet.write(start_row + 1, col_pos, "Üye (İmza)", fmt_imza_unvan)

        president_row = start_row + 4
        center_col = 13
        worksheet.write(president_row, center_col, baskan, fmt_imza_isim)
        worksheet.write(president_row + 1, center_col, "Komisyon Başkanı (İmza)", fmt_imza_unvan)

    st.download_button(
        label="📗 Excel Raporunu İndir (Kompakt)",
        data=excel_buffer.getvalue(),
        file_name=f"Rapor_{ilce_adi if ilce_adi != 'TÜMÜ' else 'Genel'}.xlsx",
        mime="application/vnd.ms-excel",
        use_container_width=True
    )

else:
    st.info("👈 Rapor oluşturmak için lütfen sol menüden Excel dosyanızı yükleyiniz.")
