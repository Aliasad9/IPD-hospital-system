from sqlalchemy import Table, Column, Integer, ForeignKey, VARCHAR, SmallInteger, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from datetime import datetime


Base = declarative_base()

engine = create_engine("mysql+pymysql://root:root@localhost:3306/flaskapp",
                       encoding='latin1', echo=True)


def create_tables():
    Base.metadata.create_all(engine)


nurse_ward_association = Table('nurse_ward_association', Base.metadata,
                               Column('nurse_id', Integer, ForeignKey('nurse.reg_no')),
                               Column('ward_id', Integer, ForeignKey('wards.ward_no'))
                               )
doctor_ward_association = Table('doctor_ward_association', Base.metadata,
                                Column('doctor_id', Integer, ForeignKey('doctor.reg_no')),
                                Column('ward_id', Integer, ForeignKey('wards.ward_no'))
                                )
class Admin(Base):
    __tablename__ = 'admin'
    reg_no = Column('reg_no', VARCHAR(length=128), primary_key=True)
    password = Column('password', VARCHAR(length=128))
    fname = Column('fname', VARCHAR(length=100))
    lname = Column('lname', VARCHAR(length=100))
    gender = Column('gender', VARCHAR(length=6))
    date_of_birth = Column('date_of_birth', DateTime)
    email = Column('email', VARCHAR(length=100))
    cnic = Column('cnic', VARCHAR(length=13))
    contact_no = Column('contact_no', VARCHAR(length=12))
    address1 = Column('address1', VARCHAR(length=100))
    address2 = Column('address2', VARCHAR(length=100))
    account_no = Column('account_no', VARCHAR(length=16))

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return (self.reg_no)

class Ward_Type_Bill(Base):
    __tablename__ = 'ward_type_bill'
    ward_type = Column('ward_type', VARCHAR(length=100), primary_key=True)
    food_bill_per_day = Column('food_bill_per_day', Integer)
    room_bill_per_day = Column('room_bill_per_day', Integer)


class Department(Base):
    __tablename__ = 'department'
    department_id = Column('department_id', Integer, unique=True, primary_key=True, autoincrement=True)
    name = Column('name', VARCHAR(length=100))

    # One Department can have many wards,lab,patient,nurse

    ward = relationship('Wards', backref='dep', lazy='dynamic')
    lab = relationship('Lab', backref='dep', lazy='dynamic')
    laboratorist = relationship('Laboratorist', backref='dep', lazy='dynamic')
    patient = relationship('Patient', backref='dep', lazy='dynamic')
    nurse = relationship('Nurse', backref='dep', lazy='dynamic')
    doctor = relationship('Doctor', backref='dep', lazy='dynamic')


#
class Patient_Medicine(Base):
    __tablename__ = 'patient_medicine'
    medicine_id = Column('medicine_id', Integer, autoincrement=True, primary_key=True)
    name = Column('name', VARCHAR(length=100), nullable=False)
    mg = Column('mg', Integer, nullable=False)
    price = Column('price', Integer, nullable=False)

    # One patient can have many patient_medicine
    patient_id = Column(Integer, ForeignKey('patients.reg_no'), nullable=False)


class Pending_Lab_Test(Base):
    __tablename__ = 'pending_lab_test'
    lab_test_no = Column('lab_test_no', Integer, autoincrement=True, primary_key=True)
    test_name = Column('test_name', VARCHAR(length=100))

    laboratorist_id = Column(Integer, ForeignKey('laboratorist.reg_no'), nullable=False)

    ward_no = Column(Integer, ForeignKey('wards.ward_no'), nullable=False)


class Lab(Base):
    __tablename__ = 'lab'
    lab_no = Column('lab_no', Integer, primary_key=True, autoincrement=True, unique=True)
    type = Column('lab_type', VARCHAR(length=100))
    department_id = Column(Integer, ForeignKey('department.department_id'), nullable=False)

    # One Lab can have many laboratorists
    lab = relationship('Laboratorist', backref='lab', lazy='dynamic')


class Wards(Base):
    __tablename__ = 'wards'
    ward_no = Column('ward_no', Integer, primary_key=True, autoincrement=True, unique=True)
    type = Column('ward_type', VARCHAR(length=100))
    occupy_status = Column('occupy_status', SmallInteger, default=0)

    lab_test_bill = Column('lab_test_bill', Integer, default=0)

    # One ward can have many pending lab tests
    pending_lab_tests = relationship('Pending_Lab_Test', backref='ward', lazy='dynamic')

    # One patient can stay in one ward
    patient = relationship('Patient', uselist=False, back_populates="wards")

    # Many wards can belong to one department
    department_id = Column(Integer, ForeignKey('department.department_id'), nullable=False)

    kitchen_manager = Column(Integer, ForeignKey('kitchen_manager.reg_no'), nullable=False)


class Patient(Base):
    __tablename__ = 'patients'
    reg_no = Column('reg_no', Integer, primary_key=True, autoincrement=True)
    fname = Column('fname', VARCHAR(length=100), nullable=False)
    lname = Column('lname', VARCHAR(length=100), nullable=False)
    email = Column('email', VARCHAR(length=100), nullable=False)
    address1 = Column('address1', VARCHAR(length=100))
    address2 = Column('address2', VARCHAR(length=100))
    blood_group = Column('blood_group', VARCHAR(length=4), nullable=False)
    weight = Column('weight', Integer, nullable=False)
    contact_no = Column('contact_no', VARCHAR(length=12), nullable=False)
    date_of_birth = Column('date_of_birth', DateTime, nullable=False)
    cnic = Column('cnic', VARCHAR(length=13), unique=True, nullable=False)
    password = Column('password', VARCHAR(length=128), nullable=False)
    gender = Column('gender', VARCHAR(length=50), nullable=False)
    reg_date = Column('reg_date', DateTime, nullable=False, default=datetime.utcnow)
    remarks = Column('remarks', VARCHAR(length=100))
    disease = Column('disease', VARCHAR(length=100))
    allergies = Column('allergies', VARCHAR(length=100))

    ward_id = Column(Integer, ForeignKey('wards.ward_no'))
    wards = relationship("Wards", back_populates="patient")

    # one patient can have many patient_medicine
    patient_medicine = relationship('Patient_Medicine', backref='patient', lazy='dynamic')

    department_id = Column(Integer, ForeignKey('department.department_id'), nullable=False)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return (self.reg_no)


class Nurse(Base):
    __tablename__ = 'nurse'
    reg_no = Column('reg_no', Integer, primary_key=True, autoincrement=True)
    fname = Column('fname', VARCHAR(length=100), nullable=False)
    lname = Column('lname', VARCHAR(length=100), nullable=False)
    gender = Column('gender', VARCHAR(length=6), nullable=False)
    date_of_birth = Column('date_of_birth', DateTime)
    email = Column('email', VARCHAR(length=100))
    cnic = Column('cnic', VARCHAR(length=13))
    password = Column('password', VARCHAR(length=128))
    contact_no = Column('contact_no', VARCHAR(length=12))
    address1 = Column('address1', VARCHAR(length=100))
    address2 = Column('address2', VARCHAR(length=100))
    rank = Column('rank', VARCHAR(length=50))
    shift = Column('shift', VARCHAR(length=50))
    account_no = Column('account_no', VARCHAR(length=16))
    # One department can have many nurses
    department_id = Column(Integer, ForeignKey('department.department_id'), nullable=False)
    # Many nurses can belong to many list[wards]
    wards_list = relationship("Wards", secondary=nurse_ward_association, backref="nurses", lazy='select')

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return (self.reg_no)


class Doctor(Base):
    __tablename__ = 'doctor'
    reg_no = Column('reg_no', Integer, primary_key=True, autoincrement=True)
    fname = Column('fname', VARCHAR(length=100))
    lname = Column('lname', VARCHAR(length=100))
    gender = Column('gender', VARCHAR(length=6))
    date_of_birth = Column('date_of_birth', DateTime)
    email = Column('email', VARCHAR(length=100))
    cnic = Column('cnic', VARCHAR(length=13))
    password = Column('password', VARCHAR(length=128))
    contact_no = Column('contact_no', VARCHAR(length=12))
    address1 = Column('address1', VARCHAR(length=100))
    address2 = Column('address2', VARCHAR(length=100))
    rank = Column('rank', VARCHAR(length=50))
    shift = Column('shift', VARCHAR(length=50))
    account_no = Column('account_no', VARCHAR(length=16))

    wards_list = relationship("Wards", secondary=doctor_ward_association, backref="doctors", lazy='dynamic')

    # One-to-one relation between the doctor and the department it belongs to
    department_id = Column(Integer, ForeignKey('department.department_id'), nullable=False)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return (self.reg_no)


class Laboratorist(Base):
    __tablename__ = 'laboratorist'
    reg_no = Column('reg_no', Integer, primary_key=True, autoincrement=True)
    fname = Column('fname', VARCHAR(length=100))
    lname = Column('lname', VARCHAR(length=100))
    gender = Column('gender', VARCHAR(length=6))
    date_of_birth = Column('date_of_birth', DateTime)
    email = Column('email', VARCHAR(length=100))
    cnic = Column('cnic', VARCHAR(length=13))
    password = Column('password', VARCHAR(length=128))
    contact_no = Column('contact_no', VARCHAR(length=12))
    address1 = Column('address1', VARCHAR(length=100))
    address2 = Column('address2', VARCHAR(length=100))
    rank = Column('rank', VARCHAR(length=50))
    shift = Column('shift', VARCHAR(length=50))
    account_no = Column('account_no', VARCHAR(length=16))

    pending_lab_tests = relationship('Pending_Lab_Test', backref='laboratorist', lazy='dynamic')

    # One Department can have many laboratorists
    department_id = Column(Integer, ForeignKey('department.department_id'), nullable=False)

    # One Lab can have many Laboratorists
    lab_no = Column('lab_no', ForeignKey('lab.lab_no'), nullable=False)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return (self.reg_no)


class Kitchen_Manager(Base):
    __tablename__ = 'kitchen_manager'
    reg_no = Column('reg_no', Integer, primary_key=True, autoincrement=True)
    fname = Column('fname', VARCHAR(length=100), nullable=False)
    lname = Column('lname', VARCHAR(length=100), nullable=False)
    gender = Column('gender', VARCHAR(length=6), nullable=False)
    date_of_birth = Column('date_of_birth', DateTime)
    email = Column('email', VARCHAR(length=100))
    cnic = Column('cnic', VARCHAR(length=13))
    password = Column('password', VARCHAR(length=128))
    contact_no = Column('contact_no', VARCHAR(length=12))
    address1 = Column('address1', VARCHAR(length=100))
    address2 = Column('address2', VARCHAR(length=100))
    shift = Column('shift', VARCHAR(length=50))
    account_no = Column('account_no', VARCHAR(length=16))

    # One Kitchen manager can have many wards
    wards = relationship('Wards', backref='kitchen_manager_id', lazy='dynamic')

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return (self.reg_no)




class Employee_Payroll_Info(Base):
    __tablename__ = 'employee_payroll_info'
    id = Column('id', Integer, autoincrement=True, primary_key=True)
    emp_type = Column('emp_type', VARCHAR(length=20))
    rank = Column('rank', VARCHAR(length=50))
    basic_pay = Column('basic_pay', Integer)
    medical_allowance = Column('medical_allowance', Integer)
    rent_allowance = Column('rent_allowance', Integer)
    deduction = Column('deduction', Integer)
