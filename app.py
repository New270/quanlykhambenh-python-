import streamlit as st
from models import SessionLocal
from controllers import ClinicController as ctrl
from datetime import datetime

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="Phòng Khám 3T", page_icon="🏥", layout="wide")

# Khởi tạo Session đăng nhập
if 'doctor_id' not in st.session_state:
    st.session_state['doctor_id'] = None

def login_view():
    st.markdown("<h1 style='text-align: center; color: #4F46E5;'>🏥 ĐĂNG NHẬP HỆ THỐNG</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            acc = st.text_input("Tài khoản bác sĩ")
            pw = st.text_input("Mật khẩu", type="password")
            if st.form_submit_button("Đăng Nhập", use_container_width=True):
                db = SessionLocal()
                # Gọi hàm login từ Controller
                doc = ctrl.login(db, acc, pw)
                if doc:
                    st.session_state['doctor_id'] = doc.Doctor_id
                    st.session_state['doctor_name'] = doc.Full_name
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu!")
                db.close()

def main_view():
    db = SessionLocal()
    
    # Menu bên trái (Sidebar)
    st.sidebar.title(f"👨‍⚕️ BS. {st.session_state['doctor_name']}")
    menu = st.sidebar.radio("MENU", ["📋 Hàng Đợi Khám", "👥 Quản Lý Bệnh Nhân", "🚪 Đăng Xuất"])

    if menu == "🚪 Đăng Xuất":
        st.session_state['doctor_id'] = None
        st.rerun()

    # --- CHỨC NĂNG 1: HÀNG ĐỢI ---
    elif menu == "📋 Hàng Đợi Khám":
        st.header("📋 Quản Lý Hàng Đợi Khám Bệnh")
        
        # Tạo 2 Tab riêng biệt
        tab_today, tab_missed = st.tabs(["📅 Lịch khám theo ngày", "⚠️ Bệnh nhân lỡ hẹn (Quá hạn)"])
        
        # TAB 1: KHÁM THEO NGÀY (Code cũ của bạn)
        with tab_today:
            date_filter = st.date_input("Lọc theo ngày", datetime.now().date())
            
            records = ctrl.get_waiting_records(db, st.session_state['doctor_id'], date_filter)
            
            if not records:
                st.info("Hiện không có bệnh nhân nào trong hàng chờ.")
            else:
                for idx, r in enumerate(records):
                    with st.expander(f"Phòng khám - Ca #{idx+1}: {r.patient.Full_name}"):
                        st.write(f"**Triệu chứng:** {r.Symptoms} | **SĐT:** {r.patient.Phone}")
                        
                        if st.button("❌ Hủy phiếu khám này", key=f"cancel_{r.Record_id}"):
                            ctrl.cancel_record(db, r.Record_id)
                            st.warning("Đã hủy phiếu khám!")
                            st.rerun()

                        with st.form(f"exam_form_{r.Record_id}"):
                            diag = st.text_area("Chẩn đoán bệnh (*)")
                            treat = st.text_area("Phác đồ điều trị & Thuốc")
                            
                            st.markdown("---")
                            re_exam = st.checkbox("Hẹn tái khám cho bệnh nhân này")
                            re_exam_date = st.date_input("Chọn ngày tái khám", 
                                                         value=datetime.now().date(),
                                                         key=f"re_date_{r.Record_id}")

                            if st.form_submit_button("Hoàn Thành & Lưu", type="primary"):
                                if diag:
                                    ctrl.complete_examine(db, r.Record_id, diag, treat)
                                    if re_exam:
                                        ctrl.add_to_queue(db, r.patient.Patient_id, st.session_state['doctor_id'], re_exam_date)
                                        st.success(f"Đã đặt lịch tái khám ngày {re_exam_date.strftime('%d/%m/%Y')}!")
                                    else:
                                        st.success("Đã hoàn thành ca khám!")
                                    st.rerun()
                                else:
                                    st.error("Chẩn đoán không được để trống!")

        # TAB 2: XỬ LÝ BỆNH NHÂN LỠ HẸN (MỚI)
        with tab_missed:
            missed_records = ctrl.get_missed_appointments(db, st.session_state['doctor_id'])
            
            if not missed_records:
                st.success("Tuyệt vời! Không có bệnh nhân nào bị lỡ hẹn.")
            else:
                st.warning(f"Có {len(missed_records)} bệnh nhân đã bỏ lỡ lịch khám trong quá khứ!")
                for r in missed_records:
                    with st.expander(f"⚠️ {r.patient.Full_name} (Lịch cũ: {r.Visit_date.strftime('%d/%m/%Y')})"):
                        st.write(f"**SĐT:** {r.patient.Phone} | **Lý do khám:** {r.Symptoms}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("❌ Hủy lịch luôn", key=f"cancel_missed_{r.Record_id}"):
                                ctrl.cancel_record(db, r.Record_id)
                                st.error("Đã hủy lịch lỡ hẹn của bệnh nhân!")
                                st.rerun()
                        with col2:
                            with st.form(key=f"reschedule_form_{r.Record_id}"):
                                new_date = st.date_input("Chọn ngày dời lịch", value=datetime.now().date())
                                if st.form_submit_button("Dời lịch khám", type="primary"):
                                    ctrl.reschedule_record(db, r.Record_id, new_date)
                                    st.success(f"Đã dời lịch sang ngày {new_date.strftime('%d/%m/%Y')}!")
                                    st.rerun()

    # --- CHỨC NĂNG 2: BỆNH NHÂN ---
    elif menu == "👥 Quản Lý Bệnh Nhân":
        st.header("👥 Quản Lý Hồ Sơ Bệnh Nhân")
        tab_list, tab_add = st.tabs(["📇 Danh sách", "➕ Thêm mới"])
        
        with tab_list:
            search = st.text_input("🔍 Tìm kiếm tên hoặc SĐT", "")
            patients = ctrl.search_patients(db, search)
            
            for p in patients:
                with st.expander(f"👤 {p.Full_name} (ID: {p.Patient_id})"):
                    c1, c2, c3 = st.tabs(["Lịch sử", "Cập nhật", "Thao tác"])
                    
                    with c1:
                        history = ctrl.get_patient_history(db, p.Patient_id)
                        for h in history:
                            colA, colB = st.columns([5, 1])
                            with colA:
                                st.info(f"**Ngày {h.Visit_date}** - Trạng thái: {h.Status}\n\nChẩn đoán: {h.Diagnosis}\n\nĐiều trị: {h.Treatment}")
                            with colB:
                                if st.button("🗑️ Xóa", key=f"del_rec_{h.Record_id}"):
                                    ctrl.delete_history_record(db, h.Record_id)
                                    st.warning("Đã xóa lịch sử khám!")
                                    st.rerun()
                            
                    with c2:
                        with st.form(f"edit_{p.Patient_id}"):
                            e_name = st.text_input("Họ tên", p.Full_name)
                            e_phone = st.text_input("SĐT", p.Phone if p.Phone else "")
                            e_address = st.text_area("Địa chỉ", p.Address if p.Address else "")
                            if st.form_submit_button("Lưu thay đổi"):
                                ctrl.update_patient(db, p.Patient_id, e_name, e_phone, e_address)
                                st.success("Đã cập nhật!")
                                st.rerun()
                                
                    with c3:
                        st.write("**Đặt lịch khám mới**")
                        with st.form(key=f"queue_form_{p.Patient_id}"):
                            selected_date = st.date_input("Chọn ngày khám", value=datetime.now().date())
                            submit_queue = st.form_submit_button("Đăng ký khám")
                            
                            if submit_queue:
                                ctrl.add_to_queue(db, p.Patient_id, st.session_state['doctor_id'], selected_date)
                                st.success(f"Đã đưa vào hàng đợi ngày {selected_date.strftime('%d/%m/%Y')}!")
                                st.rerun()
                        
                        st.markdown("---")
                        if st.button("❌ Xóa bệnh nhân này", key=f"d_{p.Patient_id}"):
                            ctrl.delete_patient(db, p.Patient_id)
                            st.error("Đã xóa hồ sơ bệnh nhân!")
                            st.rerun()

        with tab_add:
            with st.form("add_patient_form"):
                n = st.text_input("Họ và tên (*)")
                d = st.date_input("Ngày sinh", min_value=datetime(1900,1,1))
                g = st.selectbox("Giới tính", ["Nam", "Nữ"])
                ph = st.text_input("Số điện thoại")
                a = st.text_area("Địa chỉ")
                
                docs = ctrl.get_all_doctors(db)
                doc_dict = {f"BS. {doc.Full_name}": doc.Doctor_id for doc in docs}
                doc_sel = st.selectbox("Bác sĩ phụ trách", list(doc_dict.keys()))
                
                if st.form_submit_button("Lưu Hồ Sơ", type="primary"):
                    if n:
                        ctrl.add_new_patient_and_queue(db, n, d, g, ph, a, doc_dict[doc_sel])
                        st.success("Đã thêm thành công!")
                    else:
                        st.error("Họ tên không được trống!")
    db.close()

# Trình điều hướng ứng dụng
if st.session_state['doctor_id'] is None:
    login_view()
else:
    main_view()