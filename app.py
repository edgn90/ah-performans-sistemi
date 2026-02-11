import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Performans İtiraz Yönetimi", layout="wide")

# --- CSS İLE STİLLENDİRME ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007BFF; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FONKSİYONLAR ---
def classify_performance(score):
    if score < 85: return "Acil Müdahale"
    elif score < 95: return "Geliştirilmeli"
    else: return "Başarılı"

# --- PDF SINIFI (BAŞLIK VE İMZA DESTEĞİ) ---
class RaporPDF(FPDF):
    def __init__(self, baslik, uyeler, baskan):
        super().__init__()
        self.rapor_basligi = baslik
        self.uyeler = uyeler
        self.baskan = baskan

    def header(self):
        # Her sayfanın başında çıkacak başlık
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.rapor_basligi, 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Sayfa numarası
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

    def imza_blogu(self):
        self.ln(20)
        self.set_font('Arial', 'B', 10)
        
        # Komisyon Üyeleri (2 sütun halinde 6 isim)
        start_y = self.get_y()
        for i in range(0, 6, 2):
            self.cell(90, 10, self.uyeler[i], 0, 0, 'C')
            if i+1 < len(self.uyeler):
                self.cell(90, 10, self.uyeler[i+1], 0, 1, 'C')
            self.set_font('Arial', '', 9)
            self.cell(90, 5, "Komisyon Üyesi (İmza)", 0, 0, 'C')
            if i+1 < len(self.uyeler):
                self.cell(90, 5, "Komisyon Üyesi (İmza)", 0, 1, 'C')
            self.set_font('Arial', 'B', 10)
            self.ln(10)
        
        # Komisyon Başkanı (En altta ortada)
        self.ln(10)
        self.cell(0, 10, self.baskan, 0, 1, 'C')
        self.set_font('Arial', '', 9)
        self.cell(0, 5, "Komisyon Başkanı (İmza)", 0, 1, 'C')

# --- ANA EKRAN ---
st.title("📋 AH Performans İtiraz Veri ve Rapor Sistemi")

# --- SOL PANEL: KOMİSYON AYARLARI ---
st.sidebar.header("📝 Komisyon Bilgileri")
baskan_adi = st.sidebar.text_input("Komisyon Başkanı", "Dr. Ahmet YILMAZ")
uye_listesi = []
for i in range(1, 7):
    uye = st.sidebar.text_input(f"{i}. Komisyon Üyesi", f"Üye Adı {i}")
    uye_listesi.append(uye)

uploaded_file = st.sidebar.file_uploader("Excel Dosyasını Yükleyin", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    # Örnek sütunlar: 'Birim_Adi', 'Performans'
    df['Durum'] = df['Performans'].apply(classify_performance)
    
    st.success("Veri başarıyla yüklendi.")

    # --- YÖNETİCİ ÖZETİ EKRANI ---
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Birim Performans Analizi")
        st.dataframe(df.style.highlight_max(axis=0, color='#d4edda').highlight_min(axis=0, color='#f8d7da'))

    with col2:
        st.subheader("İşlemler")
        
        # --- EXCEL RAPOR ÜRETME ---
        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Performans_Raporu', startrow=2)
            workbook  = writer.book
            worksheet = writer.sheets['Performans_Raporu']
            
            # Başlık
            worksheet.write('A1', 'AH PERFORMANS İTİRAZ ÖZETİ VE KOMİSYON KARARI', workbook.add_format({'bold': True, 'size': 14}))
            
            # İmza Bloğu (Verinin bittiği yerin altına)
            last_row = len(df) + 5
            worksheet.write(last_row, 1, "Komisyon Üyeleri", workbook.add_format({'bold': True}))
            for i, name in enumerate(uye_listesi):
                worksheet.write(last_row + 1 + i, 1, name)
            
            worksheet.write(last_row + 8, 3, "Komisyon Başkanı", workbook.add_format({'bold': True}))
            worksheet.write(last_row + 9, 3, baskan_adi)

        st.download_button(
            label="📗 Excel Raporu İndir",
            data=output_excel.getvalue(),
            file_name="AH_Performans_Raporu.xlsx",
            mime="application/vnd.ms-excel"
        )

        # --- PDF RAPOR ÜRETME ---
        if st.button("📕 PDF Yönetici Özeti Hazırla"):
            pdf = RaporPDF("AILE HEKIMLIGI PERFORMANS ITIRAZ DEGERLENDIRME FORMU", uye_listesi, baskan_adi)
            pdf.add_page()
            
            # Veri Tablosu
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(80, 10, 'Birim Adi', 1)
            pdf.cell(40, 10, 'Performans', 1)
            pdf.cell(60, 10, 'Durum', 1)
            pdf.ln()
            
            pdf.set_font('Arial', '', 10)
            for _, row in df.iterrows():
                pdf.cell(80, 10, str(row['Birim_Adi']), 1)
                pdf.cell(40, 10, f"%{row['Performans']}", 1)
                pdf.cell(60, 10, str(row['Durum']), 1)
                pdf.ln()
                # Sayfa sonu kontrolü
                if pdf.get_y() > 220:
                    pdf.add_page()

            # İmza Bloğunu Ekle
            pdf.imza_blogu()
            
            pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')
            st.download_button(
                label="📥 PDF Dosyasını Kaydet",
                data=pdf_output,
                file_name="AH_Yonetici_Ozeti.pdf",
                mime="application/pdf"
            )

else:
    st.warning("Lütfen işlem yapmak için bir Excel dosyası yükleyiniz.")
    st.info("Excel dosyanız 'Birim_Adi' ve 'Performans' (sayısal) sütunlarını içermelidir.")
