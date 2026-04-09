from fpdf import FPDF
import os
from datetime import datetime

# ==========================================
# KONFIGURASI DESAIN (Elegan)
# ==========================================
COLOR_NAVY = (0, 31, 63)  
COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_CONTENT = (50, 50, 50) 

FONT_DIR = "fonts"
POPPINS_REG = os.path.join(FONT_DIR, "Poppins-Regular.ttf")
POPPINS_BOLD = os.path.join(FONT_DIR, "Poppins-Bold.ttf")

class LaporanPDFElegant(FPDF):
    def add_custom_fonts(self):
        if os.path.exists(POPPINS_REG) and os.path.exists(POPPINS_BOLD):
            self.add_font('Poppins', '', POPPINS_REG)
            self.add_font('Poppins', 'B', POPPINS_BOLD)
            self.has_poppins = True
        else:
            self.has_poppins = False

    def header(self):
        path_logo = "logo.png"
        font_style = 'Poppins' if self.has_poppins else 'helvetica'

        self.set_fill_color(*COLOR_NAVY)
        self.rect(0, 0, 210, 35, style='F') 
        
        if os.path.exists(path_logo):
            self.image(path_logo, x=15, y=8, w=18)
        else:
            self.set_text_color(*COLOR_WHITE)
            self.set_font(font_style, 'B', 16)
            self.text(x=17, y=23, txt="LOGO")

        self.set_text_color(*COLOR_WHITE)
        self.set_font(font_style, 'B', 18)
        self.set_xy(45, 12) 
        self.cell(0, 10, "Laporan Ringkasan UNRAV.ID", border=0, ln=0, align="L")
        
        self.set_font(font_style, '', 10)
        self.set_xy(45, 20)
        self.cell(0, 10, "Unravel, Focus, and Productive.", border=0, ln=0, align="L")
        
        self.set_text_color(*COLOR_TEXT_CONTENT)
        self.ln(25) 

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(230, 230, 230)
        self.line(10, 282, 200, 282)
        
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        
        formatted_date = datetime.now().strftime("%d %b %Y, %H:%M WIB")
        self.cell(100, 10, f"Dicetak pada: {formatted_date}", align='L')
        
        teks_halaman = f"Halaman {self.page_no()} / {{nb}}"
        self.cell(90, 10, teks_halaman, align='R')
        self.set_text_color(*COLOR_TEXT_CONTENT)

# --- 1. FUNGSI LAPORAN TUGAS ---
def generate_unrav_report(user_dict, tasks_list, chart_images=None, output_filename="Laporan_Tugas_UNRAV.pdf"):
    try:
        pdf = LaporanPDFElegant(orientation='P', unit='mm', format='A4')
        pdf.add_custom_fonts()
        pdf.alias_nb_pages() 
        pdf.add_page()
        
        pdf.set_font("helvetica", size=11)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "LAPORAN EVALUASI KEGIATAN", border=0, ln=1, align="C")
        pdf.ln(5)
        
        pdf.set_font("helvetica", size=9) # Font diperkecil
        html_string = f"""
        <br>
        <h3>Ringkasan Informasi Pengguna</h3>
        <ul>
            <li><b>Nama Lengkap:</b> {user_dict.get('nama_lengkap', '-')}</li>
            <li><b>Username:</b> {user_dict.get('username', '-')}</li>
            <li><b>Kontak (Email/HP):</b> {user_dict.get('kontak', '-')}</li>
        </ul>
        <br>
        <h3>Daftar Tugas Pending</h3>
        <table border="1" width="100%">
            <thead>
                <tr>
                    <th width="5%">No</th>
                    <th width="35%">Nama Tugas</th>
                    <th width="25%">Deadline</th>
                    <th width="15%">Prioritas</th>
                    <th width="20%">Status</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for task in tasks_list:
            html_string += f"""
                <tr>
                    <td align="center">{task.get('no', '')}</td>
                    <td>{task.get('nama', '')}</td>
                    <td align="center">{task.get('deadline', '-')}</td>
                    <td align="center">{task.get('prioritas', '')}</td>
                    <td align="center">{task.get('status', '')}</td>
                </tr>
            """
            
        html_string += """
            </tbody>
        </table>
        """
        
        pdf.write_html(html_string)

        if chart_images and len(chart_images) > 0:
            pdf.add_page() 
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "VISUALISASI DATA KEGIATAN", border=0, ln=1, align="C")
            pdf.ln(5)
            for img_path in chart_images:
                if os.path.exists(img_path):
                    pdf.image(img_path, x='C', w=160)
                    pdf.ln(10) 
                    
        pdf.output(output_filename)
        return output_filename
        
    except Exception as e:
        print(f"⚠️ Gagal generate PDF: {e}")
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("GAGAL MEMBUAT PDF!\n\n")
            f.write(f"Detail Error:\n{str(e)}\n\n")
        return output_filename


# --- 2. FUNGSI LAPORAN KEUANGAN ---
def generate_finance_report(user_dict, fin_summary, fin_list, chart_images=None, output_filename="Laporan_Keuangan_UNRAV.pdf"):
    try:
        pdf = LaporanPDFElegant(orientation='P', unit='mm', format='A4')
        pdf.add_custom_fonts()
        pdf.alias_nb_pages() 
        pdf.add_page()
        
        pdf.set_font("helvetica", size=11)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "LAPORAN REKAPITULASI KEUANGAN", border=0, ln=1, align="C")
        pdf.ln(5)

        # Font dikecilkan agar tabel lebih muat
        pdf.set_font("helvetica", size=9)

        html_string = f"""
        <br>
        <h3>Informasi Pengguna</h3>
        <ul>
            <li><b>Nama Lengkap:</b> {user_dict.get('nama_lengkap', '-')} ({user_dict.get('username', '-')})</li>
            <li><b>Kontak (Email/HP):</b> {user_dict.get('kontak', '-')}</li>
        </ul>
        <br>
        <h3>Ringkasan Portofolio & Keuangan</h3>
        <ul>
            <li><b>Total Pemasukan:</b> Rp {fin_summary.get('pemasukan', 0):,.0f}</li>
            <li><b>Total Pengeluaran:</b> Rp {fin_summary.get('pengeluaran', 0):,.0f}</li>
            <li><b>Saldo Kas:</b> Rp {fin_summary.get('saldo', 0):,.0f}</li>
            <li><b>Total Aset (Rumah, Emas, dll):</b> Rp {fin_summary.get('aset', 0):,.0f}</li>
            <li><b>Total Hutang / Tunggakan Tersisa:</b> Rp {fin_summary.get('hutang_tunggakan', 0):,.0f}</li>
            <li><b style="color: blue;">ESTIMASI KEKAYAAN BERSIH: Rp {fin_summary.get('kekayaan_bersih', 0):,.0f}</b></li>
        </ul>
        <br>
        <h3>Riwayat Transaksi Terbaru (Max 30)</h3>
        <table border="1" width="100%">
            <thead>
                <tr>
                    <th width="15%">Tanggal</th>
                    <th width="15%">Tipe</th>
                    <th width="30%">Deskripsi</th>
                    <th width="20%">Kategori</th>
                    <th width="20%">Nominal (Rp)</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in fin_list:
            html_string += f"""
                <tr>
                    <td align="center">{item.get('date', '')}</td>
                    <td align="center">{item.get('type', '')}</td>
                    <td>{item.get('description', '')}</td>
                    <td align="center">{item.get('category', '')}</td>
                    <td align="right">Rp {item.get('amount', 0):,.0f}</td>
                </tr>
            """
            
        html_string += """
            </tbody>
        </table>
        """
        
        pdf.write_html(html_string)

        if chart_images and len(chart_images) > 0:
            pdf.add_page() 
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "VISUALISASI DATA KEUANGAN", border=0, ln=1, align="C")
            pdf.ln(5)
            for img_path in chart_images:
                if os.path.exists(img_path):
                    pdf.image(img_path, x='C', w=140)
                    pdf.ln(8) 
                    
        pdf.output(output_filename)
        return output_filename
        
    except Exception as e:
        print(f"⚠️ Gagal generate PDF Keuangan: {e}")
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("GAGAL MEMBUAT PDF KEUANGAN!\n\n")
            f.write(f"Detail Error:\n{str(e)}\n\n")
        return output_filename