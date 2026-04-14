from models import Doctor, Patient, MedicalRecord
from datetime import datetime

class ClinicController:
    # --- XỬ LÝ ĐĂNG NHẬP ---
    @staticmethod
    def login(db, account, password):
        doc = db.query(Doctor).filter(Doctor.Account == account).first()
        if doc and doc.Password == password:
            return doc
        return None

    # --- XỬ LÝ HÀNG ĐỢI KHÁM ---
    @staticmethod
    def get_waiting_records(db, doctor_id, visit_date):
        return db.query(MedicalRecord).filter(
            MedicalRecord.Visit_date == visit_date,
            MedicalRecord.Status == 'Chờ khám',
            MedicalRecord.Doctor_id == doctor_id
        ).all()

    @staticmethod
    def complete_examine(db, record_id, diagnosis, treatment):
        record = db.query(MedicalRecord).filter(MedicalRecord.Record_id == record_id).first()
        if record:
            record.Diagnosis = diagnosis
            record.Treatment = treatment
            record.Status = 'Đã khám'
            db.commit()
            return True
        return False

    @staticmethod
    def cancel_record(db, record_id):
        record = db.query(MedicalRecord).filter(MedicalRecord.Record_id == record_id).first()
        if record:
            db.delete(record)
            db.commit()

    # --- XỬ LÝ BỆNH NHÂN ---
    @staticmethod
    def search_patients(db, query=""):
        if query:
            return db.query(Patient).filter(
                Patient.Full_name.like(f"%{query}%") | 
                Patient.Phone.like(f"%{query}%")
            ).all()
        return db.query(Patient).all()

    @staticmethod
    def update_patient(db, patient_id, name, phone, address):
        p = db.query(Patient).filter(Patient.Patient_id == patient_id).first()
        if p:
            p.Full_name = name
            p.Phone = phone
            p.Address = address
            db.commit()

    @staticmethod
    def delete_patient(db, patient_id):
        db.query(MedicalRecord).filter_by(Patient_id=patient_id).delete()
        p = db.query(Patient).filter_by(Patient_id=patient_id).first()
        if p:
            db.delete(p)
            db.commit()

    @staticmethod
    @staticmethod
    def add_to_queue(db, patient_id, doctor_id, visit_date):
        new_r = MedicalRecord(Patient_id=patient_id, Doctor_id=doctor_id, Visit_date=visit_date, Status='Chờ khám', Symptoms='Khám trực tiếp/Tái khám')
        db.add(new_r)
        db.commit()

    # --- XỬ LÝ LỊCH SỬ KHÁM ---
    @staticmethod
    def get_patient_history(db, patient_id):
        return db.query(MedicalRecord).filter_by(Patient_id=patient_id).order_by(MedicalRecord.Visit_date.desc()).all()

    @staticmethod
    def delete_history_record(db, record_id):
        record = db.query(MedicalRecord).filter(MedicalRecord.Record_id == record_id).first()
        if record:
            db.delete(record)
            db.commit()

    # --- XỬ LÝ THÊM MỚI ---
    @staticmethod
    def get_all_doctors(db):
        return db.query(Doctor).all()

    @staticmethod
    def add_new_patient_and_queue(db, fullname, dob, gender, phone, address, doctor_id):
        new_p = Patient(Full_name=fullname, Dob=dob, Gender=gender, Phone=phone, Address=address)
        db.add(new_p)
        db.flush() # Lấy ID bệnh nhân vừa tạo
        new_r = MedicalRecord(Patient_id=new_p.Patient_id, Doctor_id=doctor_id, Visit_date=datetime.now().date(), Status='Chờ khám', Symptoms='Chưa ghi nhận')
        db.add(new_r)
        db.commit()
    
    # --- XỬ LÝ BỆNH NHÂN CHƯA KHÁM ---
    @staticmethod
    def get_missed_appointments(db, doctor_id):
        # Lọc những lịch 'Chờ khám' có ngày nhỏ hơn ngày hôm nay
        return db.query(MedicalRecord).filter(
            MedicalRecord.Visit_date < datetime.now().date(),
            MedicalRecord.Status == 'Chờ khám',
            MedicalRecord.Doctor_id == doctor_id
        ).all()

    @staticmethod
    def reschedule_record(db, record_id, new_date):
        record = db.query(MedicalRecord).filter(MedicalRecord.Record_id == record_id).first()
        if record:
            record.Visit_date = new_date
            db.commit()
            return True
        return False