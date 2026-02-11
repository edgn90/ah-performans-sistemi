import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Resmi İtiraz Komisyon Raporu", layout="wide", page_icon="⚖️")

# --- SABİT SÜTUN LİSTESİ (İSTENEN FORMAT) ---
ISTENEN_SUTUNLAR = [
    "SIRA NO", "ASM ADI", "HEKİM BİRİM NO", "HEKİMİN ADI SOYADI", "HEKİMİN TC KİMLİK NO'SU",
    "İTİRAZ SEBEBİ", "İTİRAZ KONUSU", "İTİRAZ KONUSU KİŞİNİN ADI SOYADI", "İTİRAZ KONUSU KİŞİNİN TC KİMLİK NO'SU",
    "GEBE İZLEM", "LOHUSA İZLEM", "BEBEK İZLEM", "ÇOCUK İZLEM",
    "DaBT-İPA-Hib-Hep-B", "HEP B", "BCG", "KKK", "HEP A", "KPA", "OPA", "SUÇİÇEĞİ", "DaBT-İPA", "TD",
    "KABUL", "RED", "GEREKSİZ BAŞVURU", "KARAR AÇIKLAMASI"
]

# --- PDF SINIFI (A3 YATAY & RESMİ BAŞLIK) ---
class ResmiPDF(FPDF):
    def __init__(self, ilce, donem):
        super().__init__(orientation='L', unit='mm', format='A3') # Sütun çokluğundan dolayı A3
        self.ilce = ilce
        self.donem = donem

    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 6, "AILE HEKIMLIGI UYGULAMASI PERFORMANS ITIRAZ FORMLARI DEGERLENDIRME TABLOSU", 0, 1, 'C')
        self.cell(0, 6, f"{self.ilce} ILCE SAGLIK MUDURLUGU", 0, 1, 'C')
        self.cell(0, 6, f"ITIRAZ DONEMI : {self.donem}", 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

def clean_text(text):
    """Türkçe karakterleri PDF için Latin-1'e uygun hale getirir"""
    if pd.isna(text): return ""
    text = str(text)
    replacements = {
        'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
        'ı': 'i', 'İ': 'I', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    return text

# --- ANA UYGULAMA ---
st.title("⚖️ Resmi Format: Performans İtiraz Değerlendirme Tablosu")
st.markdown("Bu modül, yüklenen veriyi **A3 boyutunda PDF** ve **resmi başlıklı Excel** formatına dönüştürür.")

# --- SIDEBAR: VERİ GİRİŞİ ---
with st.sidebar:
    st.header("📝 Evrak Bilgileri")
    ilce_adi = st.text_input("İlçe Adı (Büyük Harf)", "ÜMRANİYE").upper()
    donem = st.text_input("Dönem (Ay / Yıl)", "OCAK / 2026")
    
    st.markdown("---")
    st.header("✍️ Komisyon Üyeleri")
    baskan = st.text_input("Komisyon Başkanı", "Dr. Adı Soyadı")
    uyeler = []
    for i in range(1, 6):
        uye = st.text_input(f"Üye {i}", f"Üye {i} Adı Soyadı")
        if uye: uyeler.append(uye)

    st.markdown("---")
    uploaded_file = st.file_uploader("Veri Dosyası Yükle (Excel/CSV)", type=['xlsx', 'csv'])

# --- İŞLEM MANTIĞI ---
if uploaded_file:
    # 1. Veriyi Oku
    if uploaded_file.name.endswith('.csv'):
        df_raw = pd.read_csv(uploaded_file, sep=None, engine='python')
    else:
        df_raw = pd.read_excel(uploaded_file)
    
    st.info(f"Yüklenen dosyada {len(df_raw)} satır veri bulundu. Şimdi resmi formata dönüştürülüyor...")

    # 2. DataFrame'i İstenen 27 Sütunluk Formata Oturt
    # Boş bir taslak oluştur
    df_final = pd.DataFrame(columns=ISTENEN_SUTUNLAR)
    
    # Mevcut veriyi eşleştirmeye çalış (Basit eşleştirme)
    # Eğer yüklenen dosyada sütun isimleri birebir aynı değilse, kullanıcıya manuel seçim yaptırabiliriz
    # Ancak pratiklik adına burada otomatik sütun oluşturuyoruz, verileri dosyadaki sıraya veya isme göre çekiyoruz.
    
    # Otomatik sütun eşleştirme (İsim benzerliğine göre)
    for col in ISTENEN_SUTUNLAR:
        # Yüklenen dosyada bu sütuna benzer bir şey var mı?
        match = [c for c in df_raw.columns if col.replace(" ", "").lower() in c.replace(" ", "").lower()]
        if match:
            df_final[col] = df_raw[match[0]]
        else:
            df_final[col] = "" # Yoksa boş bırak

    # Sıra No Otomatik Ver
    df_final["SIRA NO"] = range(1, len(df_final) + 1)

    # Veri Önizleme
    st.write("### 🔍 Oluşturulacak Tablo Önizlemesi")
    st.dataframe(df_final.head())

    # --- İNDİRME ALANI ---
    col1, col2 = st.columns(2)

    # --- A. EXCEL OLUŞTURMA (XLSXWRITER) ---
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, sheet_name='Itiraz_Degerlendirme', startrow=4, index=False)
        workbook = writer.book
        worksheet = writer.sheets['Itiraz_Degerlendirme']
        
        # Formatlar
        merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 12})
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#f0f0f0', 'border': 1})
        border_format = workbook.add_format({'border': 1})
        
        # 1. Başlık Kısmı (Satır 1-3)
        worksheet.merge_range('A1:AA1', "AİLE HEKİMLİĞİ UYGULAMASI PERFORMANS İTİRAZ FORMLARI DEĞERLENDİRME TABLOSU", merge_format)
        worksheet.merge_range('A2:AA2', f"{ilce_adi} İLÇE SAĞLIK MÜDÜRLÜĞÜ", merge_format)
        worksheet.merge_range('A3:AA3', f"İTİRAZ DÖNEMİ : {donem}", merge_format)
        
        # 2. Sütun Başlıklarını Formatla
        for col_num, value in enumerate(df_final.columns.values):
            worksheet.write(4, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15) # Sütun genişliği

        # 3. İmza Bloğu (Verinin bittiği yerin altına)
        last_row = len(df_final) + 7
        
        # Üyeler
        worksheet.write(last_row, 2, "KOMİSYON ÜYELERİ", workbook.add_format({'bold': True}))
        for i, uye in enumerate(uyeler):
            worksheet.write(last_row + 2, (i*4)+1, uye, workbook.add_format({'align': 'center'}))
            worksheet.write(last_row + 3, (i*4)+1, "Komisyon Üyesi\n(İmza)", workbook.add_format({'align': 'center', 'text_wrap': True}))

        # Başkan
        worksheet.write(last_row + 6, 10, baskan, workbook.add_format({'align': 'center', 'bold': True}))
        worksheet.write(last_row + 7, 10, "Komisyon Başkanı\n(İmza)", workbook.add_format({'align': 'center'}))

    with col1:
        st.download_button(
            label="📗 Resmi Excel İndir",
            data=excel_buffer.getvalue(),
            file_name=f"{ilce_adi}_Itiraz_Komisyon_Karari.xlsx",
            mime="application/vnd.ms-excel"
        )

    # --- B. PDF OLUŞTURMA (FPDF A3) ---
    pdf = ResmiPDF(clean_text(ilce_adi), clean_text(donem))
    pdf.add_page()
    
    # Tablo Başlıkları
    pdf.set_font('Arial', 'B', 7) # Küçük font (27 sütun için mecburi)
    col_width = 15 # Ortalama sütun genişliği (mm)
    
    # Bazı sütunları daralt, bazılarını genişlet
    widths = [8, 25, 12, 25, 20, 20, 20, 25, 20] + [10]*14 + [10, 10, 15, 30]
    
    # Başlık Satırı Yaz
    row_height = 8
    for i, col_name in enumerate(ISTENEN_SUTUNLAR):
        pdf.cell(widths[i], row_height, clean_text(col_name)[:15], 1, 0, 'C')
    pdf.ln()
    
    # Veri Satırları
    pdf.set_font('Arial', '', 6)
    for _, row in df_final.iterrows():
        # Sayfa sonu kontrolü
        if pdf.get_y() > 270:
            pdf.add_page()
            # Başlıkları tekrar yaz
            pdf.set_font('Arial', 'B', 7)
            for i, col_name in enumerate(ISTENEN_SUTUNLAR):
                pdf.cell(widths[i], row_height, clean_text(col_name)[:15], 1, 0, 'C')
            pdf.ln()
            pdf.set_font('Arial', '', 6)

        for i, col_name in enumerate(ISTENEN_SUTUNLAR):
            val = clean_text(row[col_name])
            pdf.cell(widths[i], 6, val[:20], 1, 0, 'C') # İçeriği kırp
        pdf.ln()

    # İmza Bloğu
    if pdf.get_y() > 240: pdf.add_page()
    pdf.ln(15)
    pdf.set_font('Arial', 'B', 8)
    
    # Üyeleri yan yana diz
    y_pos = pdf.get_y()
    for i, uye in enumerate(uyeler):
        x_pos = 10 + (i * 50)
        pdf.set_xy(x_pos, y_pos)
        pdf.cell(45, 5, clean_text(uye), 0, 1, 'C')
        pdf.set_xy(x_pos, y_pos + 5)
        pdf.cell(45, 5, "Komisyon Uyesi", 0, 1, 'C')
    
    # Başkanı ortaya koy
    pdf.set_xy(150, y_pos + 20)
    pdf.cell(50, 5, clean_text(baskan), 0, 1, 'C')
    pdf.set_xy(150, y_pos + 25)
    pdf.cell(50, 5, "Komisyon Baskani", 0, 1, 'C')

    pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')

    with col2:
        st.download_button(
            label="📕 Resmi PDF İndir (A3)",
            data=pdf_output,
            file_name=f"{ilce_adi}_Itiraz_Komisyon_Karari.pdf",
            mime="application/pdf"
        )
else:
    st.warning("Lütfen işlem yapmak için bir veri dosyası yükleyiniz.")
