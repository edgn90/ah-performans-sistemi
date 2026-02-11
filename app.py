import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Resmi İtiraz Komisyon Raporu (A4)", layout="wide", page_icon="⚖️")

# --- SÜTUN LİSTESİ ---
ISTENEN_SUTUNLAR = [
    "SIRA NO", "ASM ADI", "HEKİM BİRİM NO", "HEKİM ADI SOYADI", "HEKİM-ASÇ TC KİMLİK NO",
    "İTİRAZ SEBEBİ", "İTİRAZ KONUSU", "İTİRAZ KONUSU KİŞİNİN ADI SOYADI", "İTİRAZ KONUSU KİŞİNİN TC KİMLİK NO",
    "GEBE İZLEM", "LOHUSA İZLEM", "BEBEK İZLEM", "ÇOCUK İZLEM",
    "DaBT-İPA-Hib-Hep-B", "HEP B", "BCG", "KKK", "HEP A", "KPA", "OPA", "SUÇİÇEĞİ", "DaBT-İPA", "TD",
    "KABUL", "RED", "GEREKSİZ BAŞVURU", "KARAR AÇIKLAMASI"
]

# --- PDF İÇİN METİN TEMİZLEME ---
def clean_text(text):
    if pd.isna(text): return ""
    text = str(text)
    replacements = {
        'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
        'ı': 'i', 'İ': 'I', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    return text

# --- A4 PDF SINIFI ---
class A4LandscapePDF(FPDF):
    def __init__(self, ilce, donem):
        # A4 Yatay (297mm genişlik, 210mm yükseklik)
        super().__init__(orientation='L', unit='mm', format='A4')
        self.ilce = ilce
        self.donem = donem
        self.set_margins(5, 10, 5) # Kenar boşluklarını daralt (Sığdırmak için)

    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "AILE HEKIMLIGI UYGULAMASI PERFORMANS ITIRAZ FORMLARI DEGERLENDIRME TABLOSU", 0, 1, 'C')
        self.cell(0, 5, f"{self.ilce} ILCE SAGLIK MUDURLUGU", 0, 1, 'C')
        self.cell(0, 5, f"ITIRAZ DONEMI : {self.donem}", 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-10)
        self.set_font('Arial', 'I', 6)
        self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

# --- ANA UYGULAMA ---
st.title("⚖️ A4 Formatlı İtiraz Komisyon Sistemi")
st.write("Çıktılar A4 Yatay kağıda tam sığacak şekilde optimize edilmiştir.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📝 Evrak Bilgileri")
    ilce_adi = st.text_input("İlçe Adı", "ÜMRANİYE").upper()
    donem = st.text_input("Dönem", "OCAK / 2026")
    
    st.markdown("---")
    st.header("✍️ Komisyon Üyeleri")
    baskan = st.text_input("Komisyon Başkanı", "Dr. Adı Soyadı")
    uyeler = []
    for i in range(1, 7):
        uye = st.text_input(f"Üye {i}", f"Üye Adı {i}")
        if uye: uyeler.append(uye)
    
    uploaded_file = st.file_uploader("Veri Dosyası (Excel/CSV)", type=['xlsx', 'csv'])

if uploaded_file:
    # Veri Okuma
    if uploaded_file.name.endswith('.csv'):
        df_raw = pd.read_csv(uploaded_file, sep=None, engine='python')
    else:
        df_raw = pd.read_excel(uploaded_file)
    
    # Veri Formatlama
    df_final = pd.DataFrame(columns=ISTENEN_SUTUNLAR)
    for col in ISTENEN_SUTUNLAR:
        match = [c for c in df_raw.columns if col[:4].lower() in c.lower()]
        if match:
            df_final[col] = df_raw[match[0]]
        else:
            df_final[col] = ""
            
    df_final["SIRA NO"] = range(1, len(df_final) + 1)
    
    st.dataframe(df_final.head())
    
    col1, col2 = st.columns(2)

    # --- 1. EXCEL (A4 SIĞDIRMA AYARLI) ---
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, sheet_name='Rapor', startrow=4, index=False)
        workbook = writer.book
        worksheet = writer.sheets['Rapor']
        
        # A4 YATAY ve SIĞDIRMA AYARLARI
        worksheet.set_landscape() # Yatay
        worksheet.set_paper(9)    # 9 = A4 Kağıdı
        worksheet.fit_to_pages(1, 0) # Genişlik 1 sayfaya sığsın, uzunluk serbest (0)
        worksheet.set_margins(left=0.2, right=0.2, top=0.5, bottom=0.5)

        # Stiller
        text_wrap_format = workbook.add_format({
            'text_wrap': True, 
            'valign': 'vcenter', 
            'align': 'center', 
            'border': 1,
            'font_size': 8 # Excel için okunabilir küçük font
        })
        
        header_format = workbook.add_format({
            'bold': True, 'align': 'center', 'bg_color': '#DDDDDD', 'border': 1, 'text_wrap': True, 'font_size': 9
        })
        
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 12})

        # Başlıklar
        worksheet.merge_range('A1:AA1', "AİLE HEKİMLİĞİ UYGULAMASI PERFORMANS İTİRAZ FORMLARI DEĞERLENDİRME TABLOSU", title_format)
        worksheet.merge_range('A2:AA2', f"{ilce_adi} İLÇE SAĞLIK MÜDÜRLÜĞÜ", title_format)
        worksheet.merge_range('A3:AA3', f"İTİRAZ DÖNEMİ : {donem}", title_format)

        # Sütun Başlıkları ve Genişlikleri
        # A4'e sığması için optimum genişlik oranları
        column_widths = [
            4, 15, 8, 12, 10,  # Sıra, Asm, Birim, Dr, TC
            12, 12, 12, 10,    # Sebep, Konu, Kişi, TC
            5, 5, 5, 5,        # İzlemler
            8, 5, 5, 5, 5, 5, 5, 5, 5, 5, # Aşılar
            5, 5, 5, 20        # Kabul/Red, Açıklama
        ]

        for i, width in enumerate(column_widths):
            # Eğer listedeki sütun sayısı az gelirse varsayılan 8 yap
            w = width if i < len(column_widths) else 8
            worksheet.set_column(i, i, w)
            worksheet.write(4, i, df_final.columns[i], header_format)

        # Veri Hücrelerine Wrap Formatı Uygula
        for row_idx in range(len(df_final)):
            for col_idx in range(len(df_final.columns)):
                cell_value = df_final.iloc[row_idx, col_idx]
                worksheet.write(row_idx + 5, col_idx, cell_value, text_wrap_format)

        # İmza Alanı
        last_row = len(df_final) + 8
        worksheet.write(last_row, 2, "KOMİSYON ÜYELERİ", workbook.add_format({'bold': True}))
        
        col_pos = 1
        for member in uyeler:
            worksheet.write(last_row + 2, col_pos, member, workbook.add_format({'align': 'center', 'font_size': 10}))
            worksheet.write(last_row + 3, col_pos, "İmza", workbook.add_format({'align': 'center', 'font_size': 8}))
            col_pos += 4
        
        worksheet.write(last_row + 6, 12, baskan, workbook.add_format({'bold': True, 'align': 'center'}))
        worksheet.write(last_row + 7, 12, "Komisyon Başkanı", workbook.add_format({'align': 'center'}))

    with col1:
        st.download_button(
            label="📗 Excel İndir (A4 Uyumlu)",
            data=excel_buffer.getvalue(),
            file_name=f"{ilce_adi}_Rapor_A4.xlsx",
            mime="application/vnd.ms-excel"
        )

    # --- 2. PDF (A4 SMART ROW ALGORİTMASI) ---
    try:
        pdf = A4LandscapePDF(clean_text(ilce_adi), clean_text(donem))
        pdf.add_page()
        
        # A4 Yatay Genişlik: ~287mm (Kenar boşlukları hariç)
        # Sütun Genişliklerini Milimetre cinsinden tanımlıyoruz
        # Toplam 27 sütun var. Toplamın 285mm'yi geçmemesi lazım.
        col_ws = [
            6,  # SIRA
            20, # ASM
            10, # BIRIM
            18, # DR ADI
            16, # DR TC
            15, # SEBEP
            15, # KONU
            18, # KISI ADI
            16, # KISI TC
            5, 5, 5, 5, # IZLEMLER (4x5=20)
            10, # DaBT uzun
            5, 5, 5, 5, 5, 5, 5, 5, 5, # ASILAR (9x5=45)
            6, 6, 8, # KABUL/RED/GEREKSIZ
            30  # ACIKLAMA (Kalan pay)
        ]
        
        # Başlık Yazdırma
        pdf.set_font('Arial', 'B', 5) # Font boyutu 5 olmak zorunda (Sığması için)
        
        # Tablo Header
        max_h = 0
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        # Header'ı yazdır
        for i, header in enumerate(ISTENEN_SUTUNLAR):
            # Header'da wrap gerekebilir mi? Evet.
            # MultiCell kullanarak yüksekliği bulmuyoruz, header tek satır varsayalım veya manuel wrap
            pdf.set_xy(x_start + sum(col_ws[:i]), y_start)
            pdf.multi_cell(col_ws[i], 4, clean_text(header)[:15], 1, 'C')
        
        pdf.ln(8) # Header yüksekliği manuel
        
        # Veri Yazdırma (Smart Row Logic)
        pdf.set_font('Arial', '', 5)
        
        for _, row in df_final.iterrows():
            # 1. Bu satırın maksimum yüksekliğini hesapla
            line_height = 3 # Her satırın yüksekliği 3mm
            max_lines = 1
            
            # Tüm hücreleri kontrol et, en çok satır kaplayanı bul
            for i, col_name in enumerate(ISTENEN_SUTUNLAR):
                text = clean_text(row[col_name])
                # FPDF'in get_string_width fonksiyonu ile genişliği ölç
                width = pdf.get_string_width(text)
                available_width = col_ws[i] - 1 # Biraz padding
                lines = (width / available_width)
                if lines > max_lines:
                    max_lines = int(lines) + 1
            
            # Maksimum satır sayısını 4 ile sınırla (Çok uzun açıklamalarda sayfa patlamasın)
            if max_lines > 5: max_lines = 5
            
            current_row_height = max_lines * line_height
            
            # Sayfa sonu kontrolü
            if pdf.get_y() + current_row_height > 190:
                pdf.add_page()
                # Header tekrar
                pdf.set_font('Arial', 'B', 5)
                x_head = 5 # Margin left
                y_head = pdf.get_y()
                for i, header in enumerate(ISTENEN_SUTUNLAR):
                    pdf.set_xy(x_head + sum(col_ws[:i]), y_head)
                    pdf.multi_cell(col_ws[i], 4, clean_text(header)[:15], 1, 'C')
                pdf.ln(8)
                pdf.set_font('Arial', '', 5)

            # 2. Hücreleri Yazdır
            x_curr = 5 # Margin left
            y_curr = pdf.get_y()
            
            for i, col_name in enumerate(ISTENEN_SUTUNLAR):
                text = clean_text(row[col_name])
                pdf.set_xy(x_curr + sum(col_ws[:i]), y_curr)
                # MultiCell ile metni kaydır (Wrap Text)
                pdf.multi_cell(col_ws[i], line_height, text, 1, 'C')
                # İmleci geri çekip kutuyu tamamla (Görsel düzgünlük için)
                # (FPDF MultiCell sonrası imleci aşağı atar, biz yana geçmeliyiz, o yüzden x/y set ediyoruz)
            
            # İmleci bir sonraki satıra hazırla
            pdf.set_y(y_curr + current_row_height)
        
        # İmza Alanı
        if pdf.get_y() > 170: pdf.add_page()
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 7)
        
        y_sig = pdf.get_y()
        # Üyeler
        for i, member in enumerate(uyeler):
            x_pos = 10 + (i * 45)
            pdf.set_xy(x_pos, y_sig)
            pdf.cell(40, 4, clean_text(member), 0, 1, 'C')
            pdf.set_xy(x_pos, y_sig + 4)
            pdf.cell(40, 4, "Uye (Imza)", 0, 1, 'C')
            
        # Başkan
        pdf.set_xy(130, y_sig + 15)
        pdf.cell(40, 4, clean_text(baskan), 0, 1, 'C')
        pdf.set_xy(130, y_sig + 19)
        pdf.cell(40, 4, "Baskan (Imza)", 0, 1, 'C')
        
        pdf_out = pdf.output(dest='S').encode('latin-1', 'ignore')
        
        with col2:
            st.download_button(
                label="📕 PDF İndir (A4 Uyumlu)",
                data=pdf_out,
                file_name=f"{ilce_adi}_Rapor_A4.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"PDF Oluşturma Hatası: {e}")

else:
    st.info("Lütfen Excel dosyanızı yükleyiniz.")
