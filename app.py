import streamlit as st
from streamlit_option_menu import option_menu
from models import SessionLocal
from controllers import ClinicController as ctrl
from datetime import datetime
import time, io
import pandas as pd
from utils import generate_prescription_pdf

st.set_page_config(page_title="Phòng Khám Bác Sĩ 3T", page_icon="🩺", layout="wide")

st.markdown("""
<style>
    .metric-container {
        border-radius: 12px; padding: 25px 20px; color: white; text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-bottom: 1rem;
    }
    .bg-blue { background: linear-gradient(135deg, #0284c7, #0369a1); border-left: 5px solid #38bdf8;}
    .bg-green { background: linear-gradient(135deg, #16a34a, #15803d); border-left: 5px solid #4ade80;}
    .bg-red { background: linear-gradient(135deg, #dc2626, #b91c1c); border-left: 5px solid #f87171;}
    .metric-value { font-size: 3.5rem; font-weight: 800; line-height: 1; }
    .metric-label { font-size: 1rem; font-weight: 500; opacity: 0.9; text-transform: uppercase; }
    .history-box {
        background-color: #1e293b; border-radius: 8px; padding: 12px;
        border: 1px solid #334155; margin-bottom: 10px; font-size: 0.9rem;
    }
    .modal-box {
        border: 2px solid #38bdf8; border-radius: 10px; padding: 20px;
        background-color: #0f172a; margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

if 'doctor_id' not in st.session_state: st.session_state['doctor_id'] = None
if 'action_type' not in st.session_state: st.session_state['action_type'] = None
if 'action_p_id' not in st.session_state: st.session_state['action_p_id'] = None
if 'action_step' not in st.session_state: st.session_state['action_step'] = 1
if 'temp_data' not in st.session_state: st.session_state['temp_data'] = {}

def close_action_panel():
    st.session_state.action_type = None
    st.session_state.action_p_id = None
    st.session_state.action_step = 1
    st.session_state.temp_data = {}
    st.rerun()

def login_view():
    st.markdown("<br><br><h2 style='text-align: center; color: #38bdf8;'>🩺 HỆ THỐNG QUẢN LÝ PHÒNG KHÁM</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.form("login"):
            acc = st.text_input("Tài khoản bác sĩ")
            pw = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Đăng Nhập Nhận Ca", use_container_width=True, type="primary"):
                db = SessionLocal()
                doc = ctrl.login(db, acc, pw)
                if doc:
                    st.session_state['doctor_id'] = doc.Doctor_id
                    st.session_state['doctor_name'] = doc.Full_name
                    st.rerun()
                else: 
                    st.error("Tài khoản hoặc mật khẩu không chính xác!")
                db.close()

def main_view():
    db = SessionLocal()
    with st.sidebar:
        name_display = st.session_state['doctor_name'].replace("BS. ", "")
        st.markdown(f"""
        <div style='text-align:center; padding-bottom:15px; border-bottom:1px solid #334155; margin-bottom:15px;'>
            <img src='https://cdn-icons-png.flaticon.com/512/3774/3774299.png' width='100' style='margin-bottom:10px;'>
            <h3 style='color:#38bdf8; margin:0;'>BS. {name_display}</h3>
        </div>
        """, unsafe_allow_html=True)
        menu = option_menu(None, ["Tổng Quan", "Khám Bệnh", "Hồ Sơ Bệnh Nhân", "Đăng Xuất"], 
            icons=["grid-fill", "heart-pulse-fill", "folder-fill", "box-arrow-right"], default_index=0,
            styles={"nav-link-selected": {"background-color": "#0284c7"}})

    if menu == "Đăng Xuất": 
        st.session_state['doctor_id'] = None
        st.rerun()

    elif menu == "Tổng Quan":
        st.subheader("📊 Bảng Điều Khiển")
        stats = ctrl.get_dashboard_stats(db, st.session_state['doctor_id'])
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-container bg-blue"><div class="metric-value">{stats["waiting"]}</div><div class="metric-label">⏳ Ca chờ khám</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-container bg-green"><div class="metric-value">{stats["completed"]}</div><div class="metric-label">✅ Đã hoàn thành</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-container bg-red"><div class="metric-value">{stats["missed"]}</div><div class="metric-label">⚠️ Ca lỡ hẹn</div></div>', unsafe_allow_html=True)

    elif menu == "Khám Bệnh":
        st.subheader("📋 Không Gian Khám Bệnh")
        
        # 1. BỘ CHỌN NGÀY (Để xem lịch hôm qua, hôm nay, ngày mai)
        c_date, c_empty = st.columns([3, 7])
        with c_date:
            sel_date = st.date_input("📅 Chọn ngày xem lịch", value=datetime.now().date())
        
        date_str = sel_date.strftime('%d/%m/%Y')
        t1, t2 = st.tabs([f"📅 Danh sách ca ngày {date_str}", "⚠️ Bệnh nhân lỡ hẹn"])
        
        with t1:
            # Thông báo in PDF (Giữ nguyên logic của bạn)
            if 'recent_pdf_bytes' in st.session_state:
                st.success(f"✅ Đã khám xong cho: **{st.session_state['recent_patient_name']}**")
                cb1, _ = st.columns([3, 7])
                with cb1:
                    st.download_button("🖨️ In Phiếu Khám (PDF)", data=bytes(st.session_state['recent_pdf_bytes']), 
                        file_name=f"PhieuKham_{st.session_state['recent_patient_name']}.pdf", mime="application/pdf", type="primary", use_container_width=True)
                    if st.button("Đóng thông báo"): 
                        del st.session_state['recent_pdf_bytes']
                        st.rerun()
                st.markdown("---")

            # GỌI HÀM MỚI TỪ CONTROLLER
            records = ctrl.get_all_records_by_date(db, st.session_state['doctor_id'], sel_date)
            
            if not records: 
                st.info(f"Hiện không có bệnh nhân nào trong ngày {date_str}.")
            else:
                # Hiện thống kê nhanh
                waiting_count = len([x for x in records if x.Status == 'Chờ khám'])
                done_count = len([x for x in records if x.Status == 'Đã khám'])
                st.write(f"📊 **Thống kê:** {len(records)} ca (⏳ Chờ: {waiting_count} | ✅ Xong: {done_count})")
                
                for idx, r in enumerate(records):
                    icon = "🔴" if r.Status == 'Chờ khám' else "🟢"
                    with st.expander(f"{icon} Ca #{idx+1}: {r.patient.Full_name} ({r.Status})", expanded=(idx==0 and r.Status=='Chờ khám')):
                        if r.Status == 'Chờ khám':
                            # --- ĐÂY LÀ NƠI KHÔI PHỤC CÁI FORM KHÁM BỆNH ---
                            col_ex, col_hi = st.columns([6, 4])
                            with col_ex:
                                with st.form(f"f_{r.Record_id}"):
                                    st.write(f"**Lý do khám:** {r.Symptoms}")
                                    diag = st.text_area("Chẩn đoán (*)", height=80)
                                    proc = st.text_area("Thủ thuật điều trị (Nếu có)", height=80, placeholder="- Lấy cao răng / Cắt chỉ...")
                                    treat = st.text_area("Đơn thuốc (mỗi loại 1 dòng)", height=100)
                                    st.markdown("---")
                                    re_ex = st.checkbox("Hẹn tái khám")
                                    re_date = st.date_input("Ngày hẹn", value=datetime.now().date())
                                    
                                    cs, cd = st.columns([7, 3])
                                    with cs:
                                        if st.form_submit_button("Lưu & Xuất PDF", type="primary", use_container_width=True):
                                            if diag:
                                                ctrl.complete_examine(db, r.Record_id, diag, treat, proc)
                                                # Dùng hàm export từ utils
                                                st.session_state['recent_pdf_bytes'] = generate_prescription_pdf(
                                                    r.patient.Full_name, r.patient.Dob, r.patient.Gender, r.patient.Phone, r.patient.Address, 
                                                    diag, proc, treat, name_display)
                                                st.session_state['recent_patient_name'] = r.patient.Full_name
                                                if re_ex: ctrl.add_to_queue(db, r.patient.Patient_id, st.session_state['doctor_id'], re_date)
                                                st.rerun()
                                            else: st.error("Thiếu chẩn đoán!")
                                    with cd:
                                        if st.form_submit_button("Hủy ca", use_container_width=True): 
                                            ctrl.cancel_record(db, r.Record_id)
                                            st.rerun()
                            with col_hi:
                                st.write("📂 **Lịch sử cũ của BN này**")
                                history = ctrl.get_patient_history(db, r.Patient_id, r.Record_id)
                                for h in history[:3]:
                                    st.markdown(f'<div class="history-box"><b style="color:#38bdf8;">{h.Visit_date.strftime("%d/%m/%Y")}</b><br>Bệnh: {h.Diagnosis}</div>', unsafe_allow_html=True)
                        else:
                            # HIỂN THỊ NẾU CA ĐÃ KHÁM XONG (Chế độ xem lại)
                            st.success(f"**Kết quả chẩn đoán:** {r.Diagnosis}")
                            st.info(f"**Đơn thuốc:** {r.Treatment}")
                            if r.Notes: st.write(f"**Thủ thuật:** {r.Notes}")
                            # Thêm nút in lại PDF nhanh nếu bác sĩ cần
                            if st.button("🖨️ In lại phiếu khám", key=f"reprint_{r.Record_id}"):
                                st.session_state['recent_pdf_bytes'] = generate_prescription_pdf(
                                    r.patient.Full_name, r.patient.Dob, r.patient.Gender, r.patient.Phone, r.patient.Address, 
                                    r.Diagnosis, r.Notes if r.Notes else "", r.Treatment, name_display)
                                st.session_state['recent_patient_name'] = r.patient.Full_name
                                st.rerun()

        with t2:
            missed = ctrl.get_missed_appointments(db, st.session_state['doctor_id'])
            for r in missed:
                with st.expander(f"⚠️ {r.patient.Full_name} (Ngày lỡ hẹn: {r.Visit_date})"):
                    with st.form(f"res_{r.Record_id}"):
                        nd = st.date_input("Dời sang ngày mới")
                        c1, c2 = st.columns(2)
                        with c1: 
                            if st.form_submit_button("Xác nhận Dời", type="primary", use_container_width=True): 
                                ctrl.reschedule_record(db, r.Record_id, nd)
                                st.rerun()
                        with c2: 
                            if st.form_submit_button("Hủy ca này", use_container_width=True): 
                                ctrl.cancel_record(db, r.Record_id)
                                st.rerun()

    elif menu == "Hồ Sơ Bệnh Nhân":
        st.subheader("👥 Quản Lý Bệnh Án")
        t1, t2 = st.tabs(["📇 Tra cứu hệ thống", "➕ Mở hồ sơ mới"])
        
        with t1:
            if st.session_state.action_type:
                p_id = st.session_state.action_p_id
                p_obj = ctrl.get_patient_by_id(db, p_id)
                
                st.markdown(f"<div class='modal-box'>", unsafe_allow_html=True)
                col_title, col_close = st.columns([8, 2])
                
                if st.session_state.action_type == 'view':
                    col_title.markdown(f"<h3 style='margin-top:0;'>👁️ Chi Tiết: {p_obj.Full_name}</h3>", unsafe_allow_html=True)
                    if col_close.button("❌ Đóng bảng", use_container_width=True): close_action_panel()
                    
                    st.write(f"**Ngày sinh:** {p_obj.Dob.strftime('%d/%m/%Y') if p_obj.Dob else 'N/A'} | **Giới tính:** {p_obj.Gender} | **SĐT:** {p_obj.Phone}")
                    st.write(f"**Địa chỉ:** {p_obj.Address}")
                    st.markdown("---")
                    with st.form("book_now"):
                        d_kham = st.date_input("📅 Đưa bệnh nhân này vào hàng chờ khám")
                        if st.form_submit_button("Xác nhận Xếp Lịch", type="primary"):
                            res = ctrl.add_to_queue(db, p_id, st.session_state['doctor_id'], d_kham)
                            st.success("Đã xếp lịch!")
                            time.sleep(1); close_action_panel()
                            
                    st.write("📂 **Lịch sử khám (Nhấn để xem chi tiết):**")
                    history = ctrl.get_patient_history(db, p_id)
                    if not history: 
                        st.info("Bệnh nhân chưa có lịch sử.")
                    for h in history:
                        # Tạo các dòng lịch sử có nút bấm
                        col_h1, col_h2 = st.columns([8, 2])
                        col_h1.markdown(f"📅 **Ngày {h.Visit_date.strftime('%d/%m/%Y')}**: {h.Diagnosis[:40]}...")
                        if col_h2.button("Xem 👁️", key=f"rec_{h.Record_id}", use_container_width=True):
                            st.session_state.action_type = 'view_record'
                            st.session_state.action_record_id = h.Record_id
                            st.rerun()
                
                elif st.session_state.action_type == 'view_record':
                    r_obj = ctrl.get_record_by_id(db, st.session_state.action_record_id)
                    col_title.markdown(f"<h3 style='margin-top:0;'>📜 Chi Tiết Ca Khám: {r_obj.Visit_date.strftime('%d/%m/%Y')}</h3>", unsafe_allow_html=True)
                    
                    # Nút quay lại hồ sơ bệnh nhân
                    if col_close.button("⬅️ Quay lại", use_container_width=True): 
                        st.session_state.action_type = 'view'
                        st.rerun()
                    
                    # Hiển thị nội dung đầy đủ
                    st.markdown(f"**Bác sĩ khám:** {r_obj.doctor.Full_name}")
                    st.info(f"**1. Chẩn đoán:**\n\n{r_obj.Diagnosis}")
                    st.warning(f"**2. Thủ thuật điều trị:**\n\n{r_obj.Notes if r_obj.Notes else 'Không có'}")
                    st.success(f"**3. Đơn thuốc & Dặn dò:**\n\n{r_obj.Treatment}")
                    
                    st.markdown("---")
                    # Cho phép in luôn PDF tại đây nếu cần
                    if st.button("🖨️ Xuất lại phiếu PDF này", type="primary"):
                        st.session_state['recent_pdf_bytes'] = generate_prescription_pdf(
                            p_obj.Full_name, p_obj.Dob, p_obj.Gender, p_obj.Phone, p_obj.Address, 
                            r_obj.Diagnosis, r_obj.Notes if r_obj.Notes else "", r_obj.Treatment, r_obj.doctor.Full_name)
                        st.session_state['recent_patient_name'] = p_obj.Full_name
                        st.rerun()

                elif st.session_state.action_type == 'edit':
                    col_title.markdown(f"<h3 style='margin-top:0;'>✏️ Sửa Hồ Sơ: {p_obj.Full_name}</h3>", unsafe_allow_html=True)
                    if col_close.button("❌ Hủy thao tác", use_container_width=True): close_action_panel()
                    
                    if st.session_state.action_step == 1:
                        with st.form("edit_form"):
                            en = st.text_input("Họ Tên", p_obj.Full_name)
                            ep = st.text_input("Số điện thoại", p_obj.Phone)
                            ea = st.text_area("Địa chỉ", p_obj.Address)
                            if st.form_submit_button("Lưu Thay Đổi", type="primary"):
                                st.session_state.temp_data = {'n': en, 'p': ep, 'a': ea}
                                st.session_state.action_step = 2
                                st.rerun()
                                
                    elif st.session_state.action_step == 2:
                        st.warning("⚠️ BẢNG XÁC NHẬN: Bạn có chắc chắn muốn ghi đè thông tin mới vào cơ sở dữ liệu không?")
                        c_y, c_n = st.columns(2)
                        if c_y.button("✅ CÓ, TÔI CHẮC CHẮN", use_container_width=True):
                            td = st.session_state.temp_data
                            ctrl.update_patient(db, p_id, td['n'], td['p'], td['a'])
                            st.toast("Đã cập nhật dữ liệu thành công!")
                            time.sleep(1); close_action_panel()
                        if c_n.button("❌ KHÔNG, QUAY LẠI", use_container_width=True):
                            st.session_state.action_step = 1; st.rerun()

                elif st.session_state.action_type == 'delete':
                    col_title.markdown(f"<h3 style='margin-top:0; color:#ef4444;'>🗑️ Xóa Hồ Sơ: {p_obj.Full_name}</h3>", unsafe_allow_html=True)
                    if col_close.button("❌ Hủy thao tác", use_container_width=True): close_action_panel()
                    
                    if st.session_state.action_step == 1:
                        st.error("LƯU Ý: Thao tác này sẽ xóa sạch thông tin người bệnh, lịch sử khám và các đơn thuốc liên quan.")
                        if st.button("Tiếp tục Xóa", type="primary"):
                            st.session_state.action_step = 2; st.rerun()
                            
                    elif st.session_state.action_step == 2:
                        st.warning("⚠️ CẢNH BÁO CUỐI CÙNG: Hành động này KHÔNG THỂ HOÀN TÁC. Bạn có chắc chắn 100%?")
                        c_y, c_n = st.columns(2)
                        if c_y.button("🔥 CHẮC CHẮN XÓA VĨNH VIỄN", use_container_width=True):
                            ctrl.delete_patient(db, p_id)
                            st.toast("Đã xóa dọn dẹp sạch sẽ!")
                            time.sleep(1.5); close_action_panel()
                        if c_n.button("❌ HỦY BỎ LỆNH XÓA", use_container_width=True):
                            close_action_panel()
                            
                st.markdown("</div>", unsafe_allow_html=True)

            else:
                cs1, cs2 = st.columns([7, 3])
                with cs2: 
                    search = st.text_input("Tìm kiếm", placeholder="🔍 Tên / SĐT...", label_visibility="collapsed")
                
                df = ctrl.get_patients_dataframe(db)
                col_ex, _ = st.columns([3.5, 6.5])
                with col_ex:
                    try:
                        import openpyxl 
                        output = io.BytesIO()
                        df_export = df.copy()
                        if not df_export.empty:
                            df_export['Ngày Sinh'] = pd.to_datetime(df_export['Ngày Sinh']).dt.strftime('%d/%m/%Y')
                        with pd.ExcelWriter(output, engine='openpyxl') as writer: 
                            df_export.to_excel(writer, index=False)
                        st.download_button("📥 Xuất File Excel (.xlsx)", data=output.getvalue(), file_name="DSHoSo_BenhNhan.xlsx", type="secondary", use_container_width=True)
                    except ImportError: pass

                st.markdown("---")
                
                if search: patients_list = ctrl.search_patients(db, search)
                else: patients_list = ctrl.get_all_patients_list(db)
                
                if not patients_list:
                    st.info("Không tìm thấy dữ liệu.")
                else:
                    c1, c2, c3, c4, c5 = st.columns([1, 2.5, 1.5, 2, 2])
                    c1.write("**Mã BN**"); c2.write("**Họ Tên**"); c3.write("**Ngày Sinh**"); c4.write("**Số Điện Thoại**"); c5.write("**Thao Tác**")
                    st.markdown("<hr style='margin:0; padding:0; margin-bottom: 10px;'>", unsafe_allow_html=True)
                    
                    for p in patients_list:
                        c1, c2, c3, c4, c5 = st.columns([1, 2.5, 1.5, 2, 2])
                        c1.write(str(p.Patient_id))
                        c2.write(p.Full_name)
                        c3.write(p.Dob.strftime("%d/%m/%Y") if p.Dob else "N/A")
                        c4.write(p.Phone if p.Phone else "")
                        with c5:
                            b1, b2, b3 = st.columns(3)
                            if b1.button("👁️", key=f"v_{p.Patient_id}", help="Xem chi tiết & Xếp lịch"): 
                                st.session_state.action_type = 'view'
                                st.session_state.action_p_id = p.Patient_id
                                st.rerun()
                            if b2.button("✏️", key=f"e_{p.Patient_id}", help="Sửa thông tin"): 
                                st.session_state.action_type = 'edit'
                                st.session_state.action_p_id = p.Patient_id
                                st.rerun()
                            if b3.button("🗑️", key=f"d_{p.Patient_id}", help="Xóa hồ sơ"): 
                                st.session_state.action_type = 'delete'
                                st.session_state.action_p_id = p.Patient_id
                                st.rerun()
                        st.markdown("<hr style='margin:0; padding:0; margin-bottom: 5px; opacity: 0.2'>", unsafe_allow_html=True)

        with t2:
            with st.form("add", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1: 
                    n = st.text_input("Họ tên (*)")
                    d = st.date_input("Ngày sinh", min_value=datetime(1900,1,1), value=datetime(1995,1,1))
                    g = st.selectbox("Giới tính", ["Nam", "Nữ"])
                with c2: 
                    ph = st.text_input("SĐT")
                    # Lấy danh sách bác sĩ để chọn
                    docs = ctrl.get_all_doctors(db) if hasattr(ctrl, 'get_all_doctors') else []
                    doc_dict = {f"BS. {doc.Full_name}": doc.Doctor_id for doc in docs}
                    doc_sel = st.selectbox("Bác sĩ phụ trách", list(doc_dict.keys()))
                    
                    v_date = st.date_input("Ngày khám", value=datetime.now().date())
                
                ad = st.text_area("Địa chỉ")
                
                if st.form_submit_button("Tạo Hồ Sơ & Đăng Ký Khám", type="primary"):
                    if n: 
                        # Truyền thêm v_date và ID bác sĩ được chọn vào
                        res = ctrl.add_new_patient_and_queue(db, n, d, g, ph, ad, doc_dict[doc_sel], v_date)
                        if res == "already_in_queue": st.warning("⚠️ Bệnh nhân đã có trong hàng chờ!")
                        else:
                            st.success(f"✅ Đã tạo hồ sơ cho {n} và xếp lịch khám ngày {v_date.strftime('%d/%m/%Y')}!")
                            time.sleep(1); st.rerun()
                    else: st.error("Tên không được để trống!")
    db.close()

if st.session_state['doctor_id'] is None: login_view()
else: main_view()