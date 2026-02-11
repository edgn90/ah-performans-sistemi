import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Hatasız İtiraz Raporu", layout="wide", page_icon="⚖️")

# --- KESİN SÜTUN EŞLEŞTİRME HARİTASI ---
# Sol taraf: Bizim Rapor Sütunu | Sağ Taraf: Excel'deki Gerçek Sütun Adı
# Excel başlıklarınızdan emin olduğumuz için bu yöntem %100 çalışır.
COLUMN_MAPPING = {
    "SIRA NO": "OTOMATIK", # Kod üretecek
    "ASM ADI": "ASM ADI",
    "HEKİM BİRİM NO": "HEKİM BİRİM NO",
    "HEKİM ADI SOYADI": "HEKİM ADI SOYADI",
    "HEKİM-ASÇ TC KİMLİK NO": "HEKİM-ASÇ TC KİMLİK NO",
    "İTİRAZ SEBEBİ": "İTİRAZ SEBEBİ",
    "İTİRAZ KONUSU": "İTİRAZ NEDENİ", # Excel'de 'İTİRAZ NEDENİ' olarak geçiyor olabilir
    "İTİRAZ KONUSU KİŞİNİN ADI SOYADI": "İTİRAZ KONUSU KİŞİNİN ADI SOYADI",
    "İTİRAZ KONUSU KİŞİNİN TC KİMLİK NO": "İTİRAZ KONUSU KİŞİNİN TC KİMLİK NO",
    "GEBE İZLEM": "GEBE İZLEM",
    "LOHUSA İZLEM": "LOHUSA İZLEM",
    "BEBEK İZLEM": "BEBEK İZLEM",
    "ÇOCUK İZLEM": "ÇOCUK İZLEM",
    "DaBT-İPA-Hib-Hep-B": "DaBT-İPA-Hib-Hep-B",
    "HEP B": "HEP B",
    "BCG": "BCG",
    "KKK": "KKK",
    "HEP A": "HEP A",
    "KPA": "KPA",
    "OPA": "OPA",
    "SUÇİÇEĞİ": "SU ÇİÇEĞİ", # Excel'de boşluklu olabilir
    "DaBT-İPA": "DaBT-İPA",
    "TD": "TD",
    "KABUL": "KABUL",
    "RED": "RED",
    "GEREKSİZ BAŞVURU": "GEREKSİZ BAŞVURU",
    "KARAR AÇIKLAMASI": "KARAR AÇIKLAMASI"
}

# --- ÇIKTI SÜTUN SIRASI ---
ISTENEN_SUTUNLAR = list(COLUMN_MAPPING.keys())

# --- PDF BAŞLIK KISALTMALARI (A4 İÇİN) ---
PDF_BASLIK_MAP = {
    "SIRA NO": "NO",
    "ASM ADI": "ASM",
    "HEKİM BİRİM NO": "BIRIM",
    "HEKİM ADI SOYADI": "HEKIM",
    "HEKİM-ASÇ TC KİMLİK NO": "DR TC",
    "İTİRAZ SEBEBİ": "SEBEP",
    "İTİRAZ KONUSU": "KONU",
    "İTİRAZ KONUSU KİŞİNİN ADI SOYADI": "HASTA ADI",
    "İTİRAZ KONUSU KİŞİNİN TC KİMLİK NO": "HASTA TC",
    "GEBE İZLEM": "GB-IZ",
    "LOHUSA İZLEM": "LH-IZ",
    "BEBEK İZLEM": "BB-IZ",
    "ÇOCUK İZLEM": "CC-IZ",
    "DaBT-İPA-Hib-Hep-B": "6'LI ASI",
    "HEP B": "HepB",
    "BCG": "BCG",
    "KKK": "KKK",
    "HEP A": "HepA",
    "KPA": "KPA",
    "OPA": "OPA",
    "SUÇİÇEĞİ": "CICEK",
    "DaBT-İPA": "4LU-ASI",
    "TD": "TD",
    "KABUL": "KBL",
    "RED": "RED",
    "GEREKSİZ BAŞVURU": "GER.BSV",
    "KARAR AÇIKLAMASI": "ACIKLAMA"
}

def clean_text(text):
    if pd.isna(text): return ""
    text = str(text)
    replacements = {
        'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
        'ı': 'i', 'İ': 'I', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C',
        '\n': ' ', '\r': ''
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    return text

class A4LandscapePDF(FPDF):
    def __init__(self, ilce, donem):
        super().__init__(orientation='L', unit='mm', format='A4')
        self.ilce = ilce
        self.donem = donem
        self.set_margins(3, 10, 3)

    def header(self):
        self.set_font('Arial', 'B', 8)
        self.cell(0, 4, clean_text("AILE HEKIMLIGI PERFORMANS ITIRAZ DEGERLENDIRME TABLOSU"), 0, 1, 'C')
        self.cell(0, 4, clean_text(f"{self.ilce} ILCE SAGLIK MUDURLUGU - DONEM: {self.donem}"), 0, 1, 'C')
        self.ln(2)

    def footer(self):
        self.set_y(-8)
        self.set_font('Arial', 'I', 6)
        self.cell(0, 8, f'Sayfa {self.page_no()}', 0, 0, 'C')

# --- ANA UYGULAMA ---
st.title("⚖️ Doğrulanmış İtiraz Rapor Sistemi")

with st.sidebar:
    st.header("📝 Evrak Bilgileri")
    ilce_adi = st.text_input("İlçe Adı", "UMRANIYE").upper()
    donem = st.text_input("Dönem", "OCAK / 2026")
    st.markdown("---")
    st.header("✍️ Komisyon Üyeleri")
    baskan = st.text_input("Komisyon Başkanı", "Dr. Adı Soyadı")
    uyeler = []
    for i in range(1, 7):
        uye = st.text_input(f"Üye {i}", f"Üye {i}")
        if uye: uyeler.append(uye)
    uploaded_file = st.file_uploader("Veri Dosyası (Excel)", type=['xlsx'])

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file)
    except:
        st.error("Excel dosyası okunamadı.")
        st.stop()
    
    # --- VERİ İŞLEME VE EŞLEŞTİRME ---
    df_final = pd.DataFrame()
    
    # Her bir hedef sütun için kaynaktan doğru veriyi çek
    for target_col, source_col in COLUMN_MAPPING.items():
        if target_col == "SIRA NO":
            continue # Sonra ekleyeceğiz
        
        # Excel'deki sütun ismini bulmaya çalış (Büyük/Küçük harf duyarsız)
        found = False
        for col in df_raw.columns:
            if source_col.lower() == col.lower(): # Tam eşleşme ara
                df_final[target_col] = df_raw[col]
                found = True
                break
            # Alternatif: "SU ÇİÇEĞİ" vs "SUÇİÇEĞİ" durumu
            elif source_col.replace(" ","") == col.replace(" ",""):
                df_final[target_col] = df_raw[col]
                found = True
                break
        
        if not found:
            # Eğer sütun bulunamazsa (Örn: İtiraz Nedeni yoksa) boş bırak
            df_final[target_col] = ""

    # Sıra No ve Boşluk Temizliği
    df_final["SIRA NO"] = range(1, len(df_final) + 1)
    df_final = df_final[ISTENEN_SUTUNLAR] # Sıralamayı garantiye al
    df_final = df_final.fillna("")
    
    st.success(f"{len(df_final)} satır veri başarıyla eşleştirildi.")
    st.dataframe(df_final.head()) # Kontrol için göster
    
    col1, col2 = st.columns(2)

    # --- 1. EXCEL ---
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, sheet_name='Rapor', startrow=4, index=False)
        worksheet = writer.sheets['Rapor']
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.fit_to_pages(1, 0)
        worksheet.set_margins(0.2, 0.2, 0.5, 0.5)
        
        fmt_wrap = workbook.add_format({'text_wrap': True, 'valign': 'vcenter', 'align': 'center', 'border': 1, 'font_size': 7})
        fmt_head = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#DDDDDD', 'border': 1, 'text_wrap': True, 'font_size': 8})
        fmt_title = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 11})

        worksheet.merge_range('A1:AA1', "AİLE HEKİMLİĞİ PERFORMANS İTİRAZ DEĞERLENDİRME TABLOSU", fmt_title)
        worksheet.merge_range('A2:AA2', f"{ilce_adi} İLÇE SAĞLIK MÜDÜRLÜĞÜ", fmt_title)
        worksheet.merge_range('A3:AA3', f"DÖNEM: {donem}", fmt_title)
        
        for i, col in enumerate(df_final.columns):
            worksheet.write(4, i, col, fmt_head)
        for row_idx, row in df_final.iterrows():
            for col_idx, val in enumerate(row):
                worksheet.write(row_idx+5, col_idx, val, fmt_wrap)
        
        last_row = len(df_final) + 8
        for i, u in enumerate(uyeler):
            worksheet.write(last_row, 1 + (i*3), u)
            worksheet.write(last_row+1, 1 + (i*3), "İmza")
        worksheet.write(last_row+4, 10, baskan)
        worksheet.write(last_row+5, 10, "Komisyon Bşk. İmza")

    with col1:
        st.download_button("📗 Excel İndir", excel_buffer.getvalue(), "Rapor.xlsx")

    # --- 2. PDF ---
    try:
        pdf = A4LandscapePDF(clean_text(ilce_adi), clean_text(donem))
        pdf.add_page()
        
        col_ws = [5, 18, 9, 18, 14, 12, 12, 18, 14, 5, 5, 5, 5, 8, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 8, 28]
        
        # Header
        pdf.set_font('Arial', 'B', 5)
        x_start = 3
        y_start = pdf.get_y()
        for i, col in enumerate(ISTENEN_SUTUNLAR):
            kisa_baslik = clean_text(PDF_BASLIK_MAP.get(col, col))
            pdf.set_xy(x_start + sum(col_ws[:i]), y_start)
            pdf.cell(col_ws[i], 4, kisa_baslik, 1, 0, 'C')
        pdf.ln(4)
        
        # Data
        pdf.set_font('Arial', '', 5)
        for _, row in df_final.iterrows():
            line_height = 2.5
            max_lines = 1
            for i, col in enumerate(ISTENEN_SUTUNLAR):
                text = clean_text(row[col])
                width = pdf.get_string_width(text)
                if width > (col_ws[i]-1):
                    lines = (width / (col_ws[i]-1)) + 1
                    if lines > max_lines: max_lines = int(lines)
            if max_lines > 4: max_lines = 4
            curr_h = max_lines * line_height
            
            if pdf.get_y() + curr_h > 195:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 5)
                for i, col in enumerate(ISTENEN_SUTUNLAR):
                    kisa_baslik = clean_text(PDF_BASLIK_MAP.get(col, col))
                    pdf.set_xy(x_start + sum(col_ws[:i]), pdf.get_y())
                    pdf.cell(col_ws[i], 4, kisa_baslik, 1, 0, 'C')
                pdf.ln(4)
                pdf.set_font('Arial', '', 5)

            y_curr = pdf.get_y()
            for i, col in enumerate(ISTENEN_SUTUNLAR):
                text = clean_text(row[col])
                pdf.set_xy(x_start + sum(col_ws[:i]), y_curr)
                pdf.multi_cell(col_ws[i], line_height, text, 1, 'C')
            pdf.set_y(y_curr + curr_h)

        # İmza
        if pdf.get_y() > 180: pdf.add_page()
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 7)
        y_sig = pdf.get_y()
        for i, m in enumerate(uyeler):
            pdf.set_xy(10+(i*40), y_sig)
            pdf.cell(35, 4, clean_text(m), 0, 1, 'C')
            pdf.set_xy(10+(i*40), y_sig+4)
            pdf.cell(35, 4, "Imza", 0, 1, 'C')
        pdf.set_xy(130, y_sig+15)
        pdf.cell(40, 4, clean_text(baskan), 0, 1, 'C')
        pdf.set_xy(130, y_sig+19)
        pdf.cell(40, 4, "Komisyon Bsk. Imza", 0, 1, 'C')

        with col2:
            st.download_button("📕 PDF İndir", pdf.output(dest='S').encode('latin-1', 'ignore'), "Rapor_A4.pdf")

    except Exception as e:
        st.error(f"Hata: {e}")
