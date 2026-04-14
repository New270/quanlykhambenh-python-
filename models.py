from sqlalchemy import create_engine, Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Doctor(Base):
    __tablename__ = 'Doctors'
    Doctor_id = Column(Integer, primary_key=True, autoincrement=True)
    Full_name = Column(String(255), nullable=False)
    Specialization = Column(String(255), nullable=False)
    Account = Column(String(255), unique=True, nullable=False)
    Password = Column(String(255), nullable=False)
    Phone = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class Patient(Base):
    __tablename__ = 'Patients'
    Patient_id = Column(Integer, primary_key=True, autoincrement=True)
    Full_name = Column(String(255), nullable=False)
    Dob = Column(Date)
    Gender = Column(String(10), nullable=False)
    Phone = Column(String(20))
    Address = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class MedicalRecord(Base):
    __tablename__ = 'MedicalRecords'
    Record_id = Column(Integer, primary_key=True, autoincrement=True)
    Patient_id = Column(Integer, ForeignKey('Patients.Patient_id'), nullable=False)
    Doctor_id = Column(Integer, ForeignKey('Doctors.Doctor_id'), nullable=False)
    Visit_date = Column(Date, default=datetime.now)
    Symptoms = Column(Text)
    Diagnosis = Column(Text)
    Treatment = Column(Text)
    Notes = Column(Text)
    Status = Column(String(50), default='Chờ khám')
    created_at = Column(DateTime, default=datetime.now)
    
    patient = relationship("Patient")
    doctor = relationship("Doctor")

# Kết nối CSDL MySQL
engine = create_engine('mysql+mysqlconnector://root:@localhost:3306/hospital_db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)