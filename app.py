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
    try:
        score = float(str(score).replace(',', '.')) # Virgüllü sayıları düzelt
        if score < 85: return "Acil Müdahale"
        elif score < 95: return "Geliştirilmeli"
        else: return "Başarılı"
    except:
        return "Hata"

# --- PDF SINIFI ---
class RaporPDF(FPDF):
    def __init__(self, baslik, uyeler, baskan):
        super().__init__()
        self.rapor_basligi = baslik
        self.uyeler = uyeler
        self.baskan = baskan

    def header(self):
        self.set_font('Arial', 'B', 12)
        try:
            # Türkçe karakter desteği için font eklemeyi deneyebiliriz, 
            # ancak varsayılan Arial ile devam ediyoruz.
            self.cell(0, 10, self.rapor_basligi, 0, 1, 'C')
        except:
            self.cell(0, 10, "RAPOR BASLIGI", 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

    def imza_blogu(self):
        self.ln(20)
        self.set_font('Arial', 'B', 10)
        
        # Komisyon Üyeleri
        start_y = self.get_y()
        for i in range(0, 6, 2):
            # İsimleri güvenli yazdırma (karakter hatası önlemi)
            name1 = self.uyeler[i] if i < len(self.uyeler) else ""
            name2 = self.uyeler[i+1] if i+1 < len(self.uyeler) else ""
            
            self.cell(90, 10, name1, 0, 0, 'C')
            if name2:
                self.cell(90, 10, name2, 0, 1, 'C')
            else:
                self.ln()
                
            self.set_font('Arial', '', 9)
            self.cell(90, 5, "Komisyon Uyesi (Imza)" if name1 else "", 0, 0, 'C')
            if name2:
                self.cell(90, 5, "Komisyon Uyesi (Imza)", 0, 1, 'C')
            else:
                self.ln()
            self.set_font('Arial', 'B', 10)
            self.ln(10)
        
        # Komisyon Başkanı
        self.ln(10)
        self.cell(0, 10, self.baskan, 0, 1, 'C')
        self.set_font('Arial', '', 9)
        self.cell(0, 5, "Komisyon Baskani (Imza)", 0, 1, 'C')

# --- ANA EKRAN ---
st.title("📋 AH Performans İtiraz Veri ve Rapor Sistemi")

# --- SOL PANEL: KOMİSYON AYARLARI ---
st.sidebar.header("📝 Komisyon Bilgileri")
baskan_adi = st.sidebar.text_input("Komisyon Başkanı", "Dr. Ahmet YILMAZ")
uye_listesi = []
for i in range(1, 7):
    uye = st.sidebar.text_input(f"{i}. Komisyon Üyesi", f"Uye {i}")
    uye_listesi.append(uye)

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Dosya Yükle (Excel veya CSV)", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        # Dosya türüne göre okuma
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python') # Otomatik ayırıcı tespiti
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success("Dosya başarıyla yüklendi. Lütfen sütunları eşleştirin.")
        
        # --- SÜTUN EŞLEŞTİRME (HATA ÖNLEYİCİ) ---
        col1, col2 = st.columns(2)
        with col1:
            # Birim adını içeren sütunu seçtir
            birim_col = st.selectbox("Birim Adı Hangi Sütunda?", df.columns, index=0)
        with col2:
            # Puanı içeren sütunu seçtir
            # Otomatik olarak içinde 'puan', 'performans', 'oran' geçen sütunu bulmaya çalış
            potential_score_cols = [c for c in df.columns if any(x in str(c).lower() for x in ['puan', 'performans', 'oran', 'yüzde'])]
            default_ix = df.columns.get_loc(potential_score_cols[0]) if potential_score_cols else 1
            if default_ix >= len(df.columns): default_ix = 0
            
            puan_col = st.selectbox("Performans Puanı Hangi Sütunda?", df.columns, index=default_ix)
        
        # Seçilen sütunları standart isme çevir
        df = df.rename(columns={birim_col: 'Birim_Adi', puan_col: 'Performans'})
        
        # Analizi Çalıştır
        df['Durum'] = df['Performans'].apply(classify_performance)
        
        # --- YÖNETİCİ ÖZETİ EKRANI ---
        col_main1, col_main2 = st.columns([2, 1])
        
        with col_main1:
            st.subheader("Birim Performans Analizi")
            st.dataframe(df[['Birim_Adi', 'Performans', 'Durum']].style.highlight_max(axis=0, color='#d4edda'))

        with col_main2:
            st.subheader("İşlemler")
            
            # --- EXCEL RAPOR ÜRETME ---
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Rapor', startrow=2)
                workbook  = writer.book
                worksheet = writer.sheets['Rapor']
                
                # Başlık
                worksheet.write('A1', 'PERFORMANS KOMISYON RAPORU', workbook.add_format({'bold': True, 'size': 14}))
                
                # İmza Bloğu
                last_row = len(df) + 5
                worksheet.write(last_row, 1, "Komisyon Uyeleri", workbook.add_format({'bold': True}))
                for i, name in enumerate(uye_listesi):
                    worksheet.write(last_row + 1 + i, 1, name)
                
                worksheet.write(last_row + 8, 3, "Komisyon Baskani", workbook.add_format({'bold': True}))
                worksheet.write(last_row + 9, 3, baskan_adi)

            st.download_button(
                label="📗 Excel Raporu İndir",
                data=output_excel.getvalue(),
                file_name="Performans_Komisyon_Raporu.xlsx",
                mime="application/vnd.ms-excel"
            )

            # --- PDF RAPOR ÜRETME ---
            if st.button("📕 PDF Yönetici Özeti Hazırla"):
                pdf = RaporPDF("AILE HEKIMLIGI PERFORMANS DEGERLENDIRME", uye_listesi, baskan_adi)
                pdf.add_page()
                
                # Tablo Başlıkları
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(90, 10, 'Birim Adi', 1)
                pdf.cell(40, 10, 'Puan', 1)
                pdf.cell(60, 10, 'Durum', 1)
                pdf.ln()
                
                # Tablo İçeriği
                pdf.set_font('Arial', '', 10)
                for _, row in df.iterrows():
                    # Türkçe karakter sorununu bypass etmek için basit replace veya encode
                    birim_adi = str(row['Birim_Adi']).encode('latin-1', 'ignore').decode('latin-1')
                    durum = str(row['Durum']).encode('latin-1', 'ignore').decode('latin-1')
                    
                    pdf.cell(90, 10, birim_adi[:35], 1) # Çok uzun isimleri kırp
                    pdf.cell(40, 10, str(row['Performans']), 1)
                    pdf.cell(60, 10, durum, 1)
                    pdf.ln()
                    
                    if pdf.get_y() > 220:
                        pdf.add_page()

                pdf.imza_blogu()
                
                pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')
                st.download_button(
                    label="📥 PDF Dosyasını Kaydet",
                    data=pdf_output,
                    file_name="Yonetici_Ozeti.pdf",
                    mime="application/pdf"
                )

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
        st.info("Lütfen yüklediğiniz dosyanın formatını kontrol edin.")
else:
    st.info("Lütfen analiz için sol menüden dosya yükleyiniz.")
