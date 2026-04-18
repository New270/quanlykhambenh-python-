from models import Doctor, Patient, MedicalRecord
from datetime import datetime
import pandas as pd

class ClinicController:
    @staticmethod
    def login(db, account, password):
        doc = db.query(Doctor).filter(Doctor.Account == account).first()
        if doc and doc.Password == password: return doc
        return None

    @staticmethod
    def get_dashboard_stats(db, doctor_id):
        today = datetime.now().date()
        waiting = db.query(MedicalRecord).filter(MedicalRecord.Visit_date == today, MedicalRecord.Status == 'Chờ khám', MedicalRecord.Doctor_id == doctor_id).count()
        completed = db.query(MedicalRecord).filter(MedicalRecord.Visit_date == today, MedicalRecord.Status == 'Đã khám', MedicalRecord.Doctor_id == doctor_id).count()
        missed = db.query(MedicalRecord).filter(MedicalRecord.Visit_date < today, MedicalRecord.Status == 'Chờ khám', MedicalRecord.Doctor_id == doctor_id).count()
        return {"waiting": waiting, "completed": completed, "missed": missed}

    @staticmethod
    def get_waiting_records(db, doctor_id, visit_date):
        return db.query(MedicalRecord).filter(MedicalRecord.Visit_date == visit_date, MedicalRecord.Status == 'Chờ khám', MedicalRecord.Doctor_id == doctor_id).all()

    @staticmethod
    def complete_examine(db, record_id, diagnosis, treatment, procedures=""):
        record = db.query(MedicalRecord).filter(MedicalRecord.Record_id == record_id).first()
        if record:
            record.Diagnosis = diagnosis
            record.Treatment = treatment
            record.Notes = procedures  
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

    @staticmethod
    def search_patients(db, query=""):
        if query:
            return db.query(Patient).filter(Patient.Full_name.like(f"%{query}%") | Patient.Phone.like(f"%{query}%")).all()
        return db.query(Patient).all()

    @staticmethod
    def get_patients_dataframe(db):
        patients = db.query(Patient).all()
        # XỬ LÝ LỖI TRỐNG: Trả về bảng rỗng có cấu trúc cột nếu chưa có bệnh nhân nào
        if not patients:
            return pd.DataFrame(columns=["ID", "Họ Tên", "Ngày Sinh", "Giới Tính", "Số Điện Thoại"])
            
        data = [{"ID": p.Patient_id, "Họ Tên": p.Full_name, "Ngày Sinh": p.Dob, "Giới Tính": p.Gender, "Số Điện Thoại": p.Phone} for p in patients]
        return pd.DataFrame(data)

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
        try:
            db.query(MedicalRecord).filter(MedicalRecord.Patient_id == patient_id).delete()
            db.query(Patient).filter(Patient.Patient_id == patient_id).delete()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False

    @staticmethod
    def add_to_queue(db, patient_id, doctor_id, visit_date):
        new_r = MedicalRecord(Patient_id=patient_id, Doctor_id=doctor_id, Visit_date=visit_date, Status='Chờ khám', Symptoms='Tái khám / Định kỳ')
        db.add(new_r)
        db.commit()

    @staticmethod
    def get_patient_history(db, patient_id, exclude_record_id=None):
        query = db.query(MedicalRecord).filter(MedicalRecord.Patient_id == patient_id, MedicalRecord.Status == 'Đã khám')
        if exclude_record_id:
            query = query.filter(MedicalRecord.Record_id != exclude_record_id)
        return query.order_by(MedicalRecord.Visit_date.desc()).all()

    @staticmethod
    def get_all_doctors(db):
        return db.query(Doctor).all()
    
    @staticmethod
    def add_new_patient_and_queue(db, fullname, dob, gender, phone, address, doctor_id, visit_date):
        existing_patient = db.query(Patient).filter(
            Patient.Full_name == fullname, Patient.Dob == dob, Patient.Phone == phone
        ).first()

        if existing_patient:
            patient_id_to_use = existing_patient.Patient_id
            status_msg = "old_patient"
        else:
            new_p = Patient(Full_name=fullname, Dob=dob, Gender=gender, Phone=phone, Address=address)
            db.add(new_p)
            db.flush() 
            patient_id_to_use = new_p.Patient_id
            status_msg = "new_patient"

        existing_queue = db.query(MedicalRecord).filter(
            MedicalRecord.Patient_id == patient_id_to_use,
            MedicalRecord.Doctor_id == doctor_id,
            MedicalRecord.Visit_date == visit_date,
            MedicalRecord.Status == 'Chờ khám'
        ).first()

        if existing_queue:
            return "already_in_queue"

        new_r = MedicalRecord(
            Patient_id = patient_id_to_use, 
            Doctor_id = doctor_id, 
            Visit_date = visit_date, # Đã có tham số để sử dụng
            Status = 'Chờ khám', 
            Symptoms = 'Khám mới'
        )
        db.add(new_r)
        db.commit()
        return status_msg
    
    @staticmethod
    def get_missed_appointments(db, doctor_id):
        return db.query(MedicalRecord).filter(MedicalRecord.Visit_date < datetime.now().date(), MedicalRecord.Status == 'Chờ khám', MedicalRecord.Doctor_id == doctor_id).all()

    @staticmethod
    def reschedule_record(db, record_id, new_date):
        record = db.query(MedicalRecord).filter(MedicalRecord.Record_id == record_id).first()
        if record:
            record.Visit_date = new_date
            db.commit()
            return True
        return False
        
    @staticmethod
    def get_patient_by_id(db, patient_id):
        return db.query(Patient).filter(Patient.Patient_id == patient_id).first()

    @staticmethod
    def get_all_patients_list(db):
        return db.query(Patient).order_by(Patient.Patient_id.asc()).all()
    
    @staticmethod
    def get_all_records_by_date(db, doctor_id, visit_date):
        # Lấy tất cả hồ sơ (Chờ khám + Đã khám) của một ngày cụ thể
        return db.query(MedicalRecord).filter(
            MedicalRecord.Visit_date == visit_date,
            MedicalRecord.Doctor_id == doctor_id
        ).order_by(MedicalRecord.Status.desc()).all()
    
    @staticmethod
    def get_record_by_id(db, record_id):
        # Lấy chi tiết một ca khám dựa trên ID
        return db.query(MedicalRecord).filter(MedicalRecord.Record_id == record_id).first()