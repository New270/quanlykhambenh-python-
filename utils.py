import os
import urllib.request
from fpdf import FPDF
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_REG_URL = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
FONT_BOLD_URL = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Medium.ttf"
FONT_ITALIC_URL = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Italic.ttf"
FONT_REG_PATH = os.path.join(CURRENT_DIR, "Roboto-Regular.ttf")
FONT_BOLD_PATH = os.path.join(CURRENT_DIR, "Roboto-Medium.ttf")
FONT_ITALIC_PATH = os.path.join(CURRENT_DIR, "Roboto-Italic.ttf")

def download_font(url, path):
    if not os.path.exists(path):
        try: urllib.request.urlretrieve(url, path)
        except: pass

download_font(FONT_REG_URL, FONT_REG_PATH)
download_font(FONT_BOLD_URL, FONT_BOLD_PATH)
download_font(FONT_ITALIC_URL, FONT_ITALIC_PATH)

class PrescriptionPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if os.path.exists(FONT_REG_PATH) and os.path.exists(FONT_BOLD_PATH):
            try:
                self.add_font("Roboto", "", FONT_REG_PATH, uni=True)
                self.add_font("Roboto-Bold", "", FONT_BOLD_PATH, uni=True)
                self.add_font("Roboto-Italic", "", FONT_ITALIC_PATH, uni=True)
                self.has_font = True
            except TypeError:
                self.add_font("Roboto", "", FONT_REG_PATH)
                self.add_font("Roboto-Bold", "", FONT_BOLD_PATH)
                self.add_font("Roboto-Italic", "", FONT_ITALIC_PATH)
                self.has_font = True
            except: self.has_font = False
        else: self.has_font = False

    def header(self):
        if self.has_font: self.set_font("Roboto-Bold", "", 14)
        else: self.set_font("helvetica", "B", 14)
        
        self.set_text_color(0, 80, 155) 
        self.cell(0, 6, "PHÒNG KHÁM ĐA KHOA 3T" if self.has_font else "PHONG KHAM DA KHOA 3T", ln=1)
        
        if self.has_font: self.set_font("Roboto", "", 10)
        else: self.set_font("helvetica", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 5, "Địa chỉ: Số 123 Đường ABC, Quận Y, Hà Nội" if self.has_font else "Dia chi: So 123 Duong ABC, Ha Noi", ln=1)
        self.cell(0, 5, "Điện thoại: 1900 xxxx   -   Email: contact@phongkham3t.vn", ln=1)
        
        now = datetime.now()
        current_date = f"Ngày {now.day:02d} tháng {now.month:02d} năm {now.year}"
        
        self.set_xy(110, 15)
        if self.has_font: self.set_font("Roboto-Italic", "", 10)
        else: self.set_font("helvetica", "I", 10)
        self.set_text_color(0, 0, 0)
        self.cell(90, 5, f"Hà Nội, {current_date}" if self.has_font else f"Ha Noi, {current_date}", align="R", ln=1)

        self.set_draw_color(150, 150, 150)
        self.line(10, 32, 200, 32); self.ln(12)

def generate_prescription_pdf(patient_name, dob, gender, phone, address, diagnosis, procedures, treatment, doctor_name):
    pdf = PrescriptionPDF()
    pdf.add_page()
    
    set_reg = lambda s: pdf.set_font("Roboto" if pdf.has_font else "helvetica", "", s)
    set_bold = lambda s: pdf.set_font("Roboto-Bold" if pdf.has_font else "helvetica", "B" if not pdf.has_font else "", s)
    set_ita = lambda s: pdf.set_font("Roboto-Italic" if pdf.has_font else "helvetica", "I" if not pdf.has_font else "", s)

    set_bold(18); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "PHIẾU KHÁM BỆNH" if pdf.has_font else "PHIEU KHAM BENH", align="C", ln=1); pdf.ln(6)
    
    set_reg(11)
    tuoi = str(datetime.now().year - dob.year) if dob else "N/A"
    
    set_bold(11); pdf.cell(22, 7, "Họ và tên: " if pdf.has_font else "Ho va ten: ")
    set_reg(11); pdf.cell(80, 7, f"{patient_name}")
    set_bold(11); pdf.cell(22, 7, "Năm sinh: " if pdf.has_font else "Nam sinh: ")
    set_reg(11); pdf.cell(25, 7, str(dob.year) if dob else "N/A")
    set_bold(11); pdf.cell(20, 7, "Giới tính: " if pdf.has_font else "Gioi tinh: ")
    set_reg(11); pdf.cell(21, 7, f"{gender}", ln=1)
    
    set_bold(11); pdf.cell(18, 7, "Địa chỉ: " if pdf.has_font else "Dia chi: ")
    set_reg(11); pdf.cell(0, 7, f"{address if address else '...'}", ln=1)
    
    set_bold(11); pdf.cell(25, 7, "Điện thoại: " if pdf.has_font else "Dien thoai: ")
    set_reg(11); pdf.cell(0, 7, f"{phone if phone else '...'}", ln=1); pdf.ln(4)
    
    pdf.set_fill_color(235, 240, 245)
    pdf.set_draw_color(50, 50, 50)
    
    set_bold(10)
    pdf.cell(25, 10, "Ngày khám", border=1, align="C", fill=True)
    pdf.cell(45, 10, "Chẩn đoán", border=1, align="C", fill=True)
    pdf.cell(40, 10, "Thủ thuật", border=1, align="C", fill=True)
    pdf.cell(55, 10, "Đơn thuốc", border=1, align="C", fill=True)
    pdf.cell(25, 10, "Bác sỹ", border=1, align="C", fill=True, ln=1)
    
    set_reg(10)
    top_y = pdf.get_y()
    padding_y = 3
    line_height = 6 
    
    pdf.set_xy(10, top_y + padding_y)
    pdf.multi_cell(25, line_height, datetime.now().strftime("%d-%m-%Y"), align="C")
    h1 = pdf.get_y() - top_y
    
    pdf.set_xy(35, top_y + padding_y)
    pdf.multi_cell(45, line_height, f"{diagnosis}")
    h2 = pdf.get_y() - top_y
    
    pdf.set_xy(80, top_y + padding_y)
    proc_text = "".join([f"- {l.strip()}\n" for l in procedures.split('\n') if l.strip()])
    pdf.multi_cell(40, line_height, proc_text if proc_text else "- Không")
    h3 = pdf.get_y() - top_y
    
    pdf.set_xy(120, top_y + padding_y)
    treat_text = "".join([f"- {l.strip()}\n" for l in treatment.split('\n') if l.strip()])
    pdf.multi_cell(55, line_height, treat_text if treat_text else "- Không")
    h4 = pdf.get_y() - top_y
    
    pdf.set_xy(175, top_y + padding_y)
    pdf.multi_cell(25, line_height, f"BS. {doctor_name}", align="C")
    h5 = pdf.get_y() - top_y
    
    max_h = max(h1, h2, h3, h4, h5) + padding_y
    if max_h < 20: max_h = 20
    
    pdf.rect(10, top_y, 25, max_h)
    pdf.rect(35, top_y, 45, max_h)
    pdf.rect(80, top_y, 40, max_h)
    pdf.rect(120, top_y, 55, max_h)
    pdf.rect(175, top_y, 25, max_h)
    
    pdf.set_y(top_y + max_h + 10)
    
    set_bold(11); pdf.cell(20, 7, "Lịch hẹn: " if pdf.has_font else "Lich hen: ")
    set_reg(11); pdf.cell(0, 7, "Theo lịch tái khám của bác sĩ (Nếu có)", ln=1)
    
    set_bold(11); pdf.cell(20, 7, "Lời dặn: " if pdf.has_font else "Loi dan: ", ln=1)
    set_reg(11); pdf.cell(5, 6, "")
    pdf.multi_cell(0, 6, "- Uống thuốc đúng giờ, đúng liều lượng theo chỉ định.\n- Tái khám ngay nếu có dấu hiệu bất thường." if pdf.has_font else "- Uong thuoc dung gio, dung lieu luong.\n- Tai kham ngay neu co dau hieu bat thuong.")
    pdf.ln(15)
    
    set_bold(11)
    pdf.cell(63, 6, "KHÁCH HÀNG" if pdf.has_font else "KHACH HANG", align="C")
    pdf.cell(63, 6, "NGƯỜI LẬP PHIẾU" if pdf.has_font else "NGUOI LAP PHIEU", align="C")
    pdf.cell(64, 6, "BÁC SỸ" if pdf.has_font else "BAC SY", align="C", ln=1)
    
    set_ita(10)
    pdf.cell(63, 5, "(Ký và ghi rõ họ tên)" if pdf.has_font else "(Ky va ghi ro ho ten)", align="C")
    pdf.cell(63, 5, "(Ký và ghi rõ họ tên)" if pdf.has_font else "(Ky va ghi ro ho ten)", align="C")
    pdf.cell(64, 5, "(Ký và ghi rõ họ tên)" if pdf.has_font else "(Ky va ghi ro ho ten)", align="C", ln=1)
    
    pdf.ln(25)
    set_reg(11)
    pdf.cell(63, 6, ""); pdf.cell(63, 6, "")
    pdf.cell(64, 6, f"BS. {doctor_name}", align="C")

    return pdf.output(dest='S').encode('latin1') if isinstance(pdf.output(dest='S'), str) else pdf.output(dest='S')