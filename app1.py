from datetime import timedelta
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
import os
import smtplib

from Model1 import *
from Queries import *

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        reg = str(user_id)
        if reg[0] == '1':
            return session.query(Nurse).get(user_id)
        elif reg[0] == '2':
            return session.query(Doctor).get(user_id)
        elif reg[0] == '3':
            return session.query(Kitchen_Manager).get(user_id)
        elif reg[0] == '4':
            return session.query(Laboratorist).get(user_id)
        elif reg[0] == '5':
            return session.query(Patient).get(user_id)
        elif reg[0] == 'A':
            return session.query(Admin).get(user_id)
    return None


@app.route('/')
def index():
    contact = "Contact Us"
    about = "About"
    return render_template('home_page.html', contact=contact, about=about)


@app.route('/log_in', methods=["POST", "GET"])
def log_in():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        registration_no = request.form['reg-number']
        password_candidate = request.form['password']
        remember_me = 'remember-me' in request.form

        reg = str(registration_no)

        if reg[0] == '1':
            result = session.query(Nurse).filter_by(reg_no=registration_no).first()
        elif reg[0] == '2':
            result = session.query(Doctor).filter_by(reg_no=registration_no).first()
        elif reg[0] == '3':
            result = session.query(Kitchen_Manager).filter_by(reg_no=registration_no).first()
        elif reg[0] == '4':
            result = session.query(Laboratorist).filter_by(reg_no=registration_no).first()
        elif reg[0] == '5':
            result = session.query(Patient).filter_by(reg_no=registration_no).first()
        elif reg[0] == 'A':
            result = session.query(Admin).filter_by(reg_no=registration_no).first()
            if result is not None:
                if str(result.password) == password_candidate:
                    login_user(result, remember=remember_me)
                    flash("Logged in successfully", "success")
                    return redirect(request.args.get('next') or url_for('dashboard'))
                else:
                    flash("Wrong Password", "danger")
                    return redirect(url_for("log_in"))
        else:
            flash("Invalid Credentials", 'danger')
            return redirect(url_for('log_in'))
        if result is not None:

            if check_password_hash(str(result.password), password_candidate):
                login_user(result, remember=remember_me)
                flash("Logged in successfully", "success")
                return redirect(request.args.get('next') or url_for('dashboard'))
            else:
                flash("Wrong Password", "danger")

        else:
            flash("No User Exists For This Registration No.", "danger")

    return render_template('log_in.html')


# @app.route('/doctor_page')
# def doctor():
#     patients_list = retrievePatientsAgainstDoctors(20004)
#     age = []
#     for i in patients_list:
#         now = datetime.utcnow()
#         duration = now - i.date_of_birth
#         duration_in_s = duration.total_seconds()
#         years = divmod(duration_in_s, 31536000)[0]
#         age.append(years)
#     list_m = []
#     for p in patients_list:
#         med = session.query(Patient_Medicine).filter_by(patient_id=p.reg_no).all()
#         list_m.append(med)
#
#     return render_template('doctor_page.html', pat_age_listm=zip(patients_list, age, list_m))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    reg = str(current_user.reg_no)

    if reg[0] == '1':
        patients_list = retrievePatientsAgainstNurse(current_user.reg_no)
        laboratorists = session.query(Laboratorist).all()
        entity = Nurse
        personal_info = session.query(entity).filter_by(reg_no=current_user.reg_no).first()


        if request.method == 'POST':
            patient_id = request.form['patient-id']
            med_name = request.form["med-name"]
            med_mg = request.form["med-strength"]
            med_price = request.form["med-price"]
            pat = session.query(Patient).filter_by(reg_no=patient_id).first()

            medicine = Patient_Medicine(name=med_name, mg=med_mg, price=med_price, patient=pat)
            try:

                add_to_db(medicine)
                flash("Medicine Assigned to Patient Successully", "success")
            except:
                session.rollback()
                flash("Medicine not Assigned to Patient", "warning")

        return render_template('nurse_page.html',entity=str(entity), personal_info=personal_info, patients_list=patients_list,
                               laboratorists=laboratorists)
    elif reg[0] == '2':
        patients_list = retrievePatientsAgainstDoctors(current_user.reg_no)
        age = []
        entity = Doctor
        personal_info = session.query(entity).filter_by(reg_no=current_user.reg_no).first()

        for i in patients_list:
            now = datetime.utcnow()
            duration = now - i.date_of_birth
            duration_in_s = duration.total_seconds()
            years = divmod(duration_in_s, 31536000)[0]
            age.append(years)
        list_m = []
        for p in patients_list:
            med = session.query(Patient_Medicine).filter_by(patient_id=p.reg_no).all()
            list_m.append(med)

        return render_template('doctor_page.html',entity=str(entity),  personal_info=personal_info,
                               pat_age_listm=zip(patients_list, age, list_m))
    elif reg[0] == '3':
        entity = Kitchen_Manager
        personal_info = session.query(entity).filter_by(reg_no=current_user.reg_no).first()

        patients_list = retrieveRoomsAgainstKM(current_user.reg_no)

        return render_template('kitchen_manager_page.html', entity=str(entity), personal_info=personal_info, patients_list=patients_list)
    elif reg[0] == '4':
        tests = retrieveLabTests(current_user.reg_no)
        entity = Laboratorist
        personal_info = session.query(entity).filter_by(reg_no=current_user.reg_no).first()

        if request.method == "POST":
            bill = request.form['bill-amount']
            ward_id = request.form['room-no']
            test_id = request.form['test-id']

            done_test = session.query(Pending_Lab_Test).filter_by(lab_test_no=test_id).first()
            try:
                session.delete(done_test)
                session.commit()
                ward = session.query(Wards).filter_by(ward_no=ward_id).first()
                ward.lab_test_bill = int(ward.lab_test_bill) + int(bill)
                session.commit()
                flash("Bill Generated Successfully", "success")
                return redirect(url_for('dashboard'))
            except:
                session.rollback()
                flash('Bill not generated successfully', "warning")
            return redirect(url_for('dashboard'))

        return render_template('laboratorist_page.html', entity=str(entity), personal_info=personal_info, tests=tests)
    elif reg[0] == '5':
        entity = Patient
        personal_info = session.query(entity).filter_by(reg_no=current_user.reg_no).first()

        food = getFoodBill(current_user.reg_no)
        room = getRoomBill(current_user.reg_no)
        lab = getLabTestBill(current_user.reg_no)
        med = getMedicineBill(current_user.reg_no)
        total = 0
        if food is not None:
            total += food
        if room is not None:
            total += room
        if lab is not None:
            total += lab
        if med is not None:
            total += med

        return render_template('patient_page.html',entity=str(entity),  personal_info=personal_info, food=food, room=room, lab=lab, med=med,
                               total=total)
    elif reg[0] == 'A':
        entity = Admin
        if request.method == 'POST':
            if request.form['form-id'] == '1':
                department = request.form['add_dept']
                dept = Department(name=department)
                try:
                    add_to_db(dept)
                    flash("New Department Added Successfully", "success")
                except:
                    session.rollback()
                    flash("New Department Was Not Added", "warning")

            elif request.form['form-id'] == '2':
                department_id = request.form['department']
                type = request.form["type_lab"]
                department = session.query(Department).filter_by(department_id=department_id).first()
                lab = Lab(type=type, dep=department)
                try:
                    add_to_db(lab)
                    flash("New Lab Added Successfully", "success")
                except:
                    session.rollback()
                    flash("New Lab Was Not Added", "warning")
            elif request.form['form-id'] == '3':
                department_id = request.form['department']
                department = session.query(Department).filter_by(department_id=department_id).first()
                type = request.form["type_room"]
                km_id = request.form['kitchen_manager']
                km = session.query(Kitchen_Manager).filter_by(reg_no=km_id).first()
                l = Wards(type=type, dep=department, kitchen_manager_id=km)
                try:
                    add_to_db(l)
                    flash("New Room Added Successfully", "success")
                except:
                    session.rollback()
                    flash("New Room Was Not Added", "warning")

        kitchen_manager = session.query(Kitchen_Manager).all()
        departments_list = session.query(Department).all()
        ward_list = session.query(Ward_Type_Bill).all()
        personal_info = session.query(entity).filter_by(reg_no=current_user.reg_no).first()
        return render_template('admin_dashboard.html', departments_list=departments_list,
                               kitchen_manager=kitchen_manager,
                               ward_list=ward_list,entity=str(entity),  personal_info=personal_info)

    return render_template('log_in.html', current_user=current_user)


@app.route('/lab_test', methods=['GET', 'POST'])
@login_required
def gen_lab_test():
    reg = str(current_user.reg_no)
    if reg[0] == '1':
        patients_list = retrievePatientsAgainstNurse(current_user.reg_no)
        laboratorists = session.query(Laboratorist).all()
        entity = Nurse
        personal_info = session.query(entity).filter_by(reg_no=current_user.reg_no).first()
        if request.method == 'POST':
            room_id = request.form["room-id"]
            room = session.query(Wards).filter_by(ward_no=room_id).first()
            test_name = request.form["test-name"]
            laboratorist_id = request.form["laboratorist"]
            laboratorist = session.query(Laboratorist).filter_by(reg_no=laboratorist_id).first()

            lab_test = Pending_Lab_Test(test_name=test_name, laboratorist=laboratorist, ward=room)
            try:
                add_to_db(lab_test)
                flash("New Lab Test Added Successfully", "success")
            except:
                session.rollback()
                flash("New Lab Test Was Not Added", "warning")
            return render_template('nurse_page.html',personal_info=personal_info,entity=str(entity), patients_list=patients_list, laboratorists=laboratorists)
        return render_template('nurse_page.html',personal_info=personal_info,entity=str(entity), patients_list=patients_list, laboratorists=laboratorists)
    return redirect(url_for('log_in'))


@app.route('/register_patient', methods=["POST", "GET"])
@login_required
def register_patient():
    reg = str(current_user.reg_no)
    if reg[0] == '1':
        if request.method == "POST":
            firstname = request.form["firstname"]
            lastname = request.form["lastname"]
            cnic = request.form["cnic"]
            email = request.form["email"]
            contact_no = request.form["contact-no"]
            dob = request.form["dob"]
            blood_group = request.form["blood-group"]
            gender = request.form["gender"]
            weight = request.form["weight"]
            address1 = request.form["address"]
            address2 = request.form["address2"]
            ward_no = request.form["ward"]
            ward = session.query(Wards).filter_by(ward_no=ward_no).first()
            department_id = request.form["department"]
            department = session.query(Department).filter_by(department_id=department_id).first()
            remarks = request.form["remarks"]
            disease = request.form["disease"]
            allergies = request.form["allergies"]

            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(9))

            old_patient = session.query(Patient).filter_by(cnic=cnic).first()

            if old_patient is not None:
                flash("User with this CNIC alread exists", "danger")
                return redirect(url_for("register_patient"))

            pat = Patient(fname=firstname, lname=lastname, email=email, address1=address1,
                          address2=address2, blood_group=blood_group, weight=weight, contact_no=contact_no,
                          date_of_birth=dob, cnic=cnic, password=generate_password_hash(password), gender=gender,
                          reg_date=datetime.utcnow(),
                          remarks=remarks,
                          disease=disease, allergies=allergies, wards=ward,
                          dep=department)
            try:

                add_to_db(pat)
                getPat = session.query(Patient).filter_by(fname=firstname, lname=lastname, email=email,
                                                          date_of_birth=dob, cnic=cnic).first()

                nurse = session.query(Nurse).filter_by(reg_no=current_user.reg_no).first()
                nurse.wards_list.append(ward)
                add_to_db(nurse)
                ward.occupy_status = 1
                session.commit()
                send_email(getPat.reg_no, password, email)
                flash("New Patient Registered Successfully","success")
                return redirect(url_for("dashboard"))
            except:
                session.rollback()
                flash("Patient was not Registered", "warning")
                return redirect(url_for("register_patient"))
        dept = session.query(Department).all()
        wards = session.query(Wards).filter_by(occupy_status=0).all()
        entity = Nurse
        personal_info = session.query(entity).filter_by(reg_no=current_user.reg_no).first()

        return render_template('register_patient.html',personal_info=personal_info, dept=dept, wards=wards)
    else:
        return redirect(url_for('log_in'))


@app.route('/add_doctor', methods=['GET', 'POST'])
@login_required
def add_doctor():
    reg = str(current_user.reg_no)
    if reg[0] == 'A':
        if request.method == 'POST':
            firstname = request.form["firstname"]
            lastname = request.form["lastname"]
            cnic = request.form["cnic"]
            email = request.form["email"]
            contact_no = request.form["contact-no"]
            dob = request.form['dob']
            gender = request.form['gender']
            acc_no = request.form['acc-no']
            address1 = request.form['address']
            address2 = request.form['address2']
            ward_id = request.form['room-no']
            ward = session.query(Wards).filter_by(ward_no=ward_id).first()
            rank = request.form['rank']
            shift = request.form['shift-time']
            department_id = request.form['department']
            department = session.query(Department).filter_by(department_id=department_id).first()

            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(9))

            old_doc = session.query(Doctor).filter_by(cnic=cnic).first()
            if old_doc is not None:
                flash("User with CNIC already exists","danger")
                return redirect(url_for("add_doctor"))
            doc = Doctor(fname=firstname, lname=lastname, gender=gender, date_of_birth=dob, email=email,
                         password=generate_password_hash(password), cnic=cnic,
                         contact_no=contact_no, address1=address1, address2=address2, rank=rank, shift=shift,
                         account_no=acc_no, dep=department)
            try:

                add_to_db(doc)

                doc = session.query(Doctor).filter_by(fname=firstname, lname=lastname, date_of_birth=dob).first()
                doc.wards_list.append(ward)
                add_to_db(doc)
                send_email(doc.reg_no, password, email)
                flash('New Doctor Added Successfully', "success")
                return redirect(url_for('dashboard'))
            except:
                session.rollback()
                flash("New Doctor was not added", "warning")
        wards_list = session.query(Wards).all()
        departments_list = session.query(Department).all()
        return render_template('add_doctor.html', departments_list=departments_list, wards_list=wards_list)
    return redirect(url_for('log_in'))


@app.route('/add_nurse', methods=['GET', 'POST'])
@login_required
def add_nurse():
    reg = str(current_user.reg_no)
    if reg[0] == 'A':
        if request.method == 'POST':
            firstname = request.form["firstname"]
            lastname = request.form["lastname"]
            cnic = request.form["cnic"]
            email = request.form["email"]
            contact_no = request.form["contact-no"]
            dob = request.form['dob']
            gender = request.form['gender']
            acc_no = request.form['acc-no']
            address1 = request.form['address']
            address2 = request.form['address2']
            ward_id = request.form['room-no']
            ward = session.query(Wards).filter_by(ward_no=ward_id).first()
            rank = request.form['rank']
            shift = request.form['shift-time']
            department_id = request.form['department']
            department = session.query(Department).filter_by(department_id=department_id).first()

            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(9))

            old_nur = session.query(Nurse).filter_by(cnic=cnic).first()
            if old_nur is not None:
                flash('User with CNIC Already Exists',"danger")
                return redirect(url_for("add_nurse"))
            nurse = Nurse(fname=firstname, lname=lastname, gender=gender, date_of_birth=dob, email=email,
                          password=generate_password_hash(password), cnic=cnic,
                          contact_no=contact_no, address1=address1, address2=address2, rank=rank, shift=shift,
                          account_no=acc_no, dep=department)
            try:
                add_to_db(nurse)

                nur = session.query(Nurse).filter_by(fname=firstname, lname=lastname, date_of_birth=dob).first()
                nur.wards_list.append(ward)
                add_to_db(nur)
                send_email(nur.reg_no, password, email)

                flash('New Nurse Added Successfully', "success")
                return redirect(url_for('dashboard'))
            except:
                session.rollback()
                flash("New Nurse was not Added", "warning")

        wards_list = session.query(Wards).all()
        departments_list = session.query(Department).all()
        return render_template('add_nurse.html', departments_list=departments_list, wards_list=wards_list)
    return redirect(url_for('log_in'))


@app.route('/add_kitchen_manager', methods=['GET', 'POST'])
@login_required
def add_kitchen_manager():
    reg = str(current_user.reg_no)
    if reg[0] == 'A':
        if request.method == 'POST':
            firstname = request.form["firstname"]
            lastname = request.form["lastname"]
            cnic = request.form["cnic"]
            email = request.form["email"]
            contact_no = request.form["contact-no"]
            dob = request.form['dob']
            gender = request.form['gender']
            acc_no = request.form['acc-no']
            address1 = request.form['address']
            address2 = request.form['address2']
            shift = request.form['shift-time']

            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(9))

            old_km = session.query(Kitchen_Manager).filter_by(cnic=cnic).first()
            if old_km is not None:
                flash('User with CNIC Already Exists',"danger")
                return redirect(url_for('add_kitchen_manager'))
            nurse = Kitchen_Manager(fname=firstname, lname=lastname, gender=gender, date_of_birth=dob, email=email,
                                    password=generate_password_hash(password), cnic=cnic,
                                    contact_no=contact_no, address1=address1, address2=address2, shift=shift,
                                    account_no=acc_no)
            try:
                add_to_db(nurse)
                km = session.query(Kitchen_Manager).filter_by(fname=firstname, lname=lastname, gender=gender,
                                                              date_of_birth=dob, email=email, cnic=cnic).first()
                send_email(km.reg_no, password, email)
                flash('New Kitchen Manager Added Successfully', 'success')
                return redirect(url_for('dashboard'))
            except:
                session.rollback()
                flash("Kitchen Manager was not Added Successfully", "warning")

        return render_template('add_kitchen_manager.html')
    return redirect(url_for('log_in'))


@app.route('/add_laboratorist', methods=['GET', 'POST'])
@login_required
def add_laboratorist():
    reg = str(current_user.reg_no)
    if reg[0] == 'A':
        if request.method == 'POST':
            firstname = request.form["firstname"]
            lastname = request.form["lastname"]
            cnic = request.form["cnic"]
            email = request.form["email"]
            contact_no = request.form["contact-no"]
            dob = request.form['dob']
            gender = request.form['gender']
            acc_no = request.form['acc-no']
            address1 = request.form['address']
            address2 = request.form['address2']
            lab_id = request.form['lab-no']
            lab = session.query(Lab).filter_by(lab_no=lab_id).first()
            rank = request.form['rank']
            shift = request.form['shift-time']
            department_id = request.form['department']
            department = session.query(Department).filter_by(department_id=department_id).first()

            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(9))

            old_nur = session.query(Laboratorist).filter_by(cnic=cnic).first()
            if old_nur is not None:
                flash('User with CNIC Already Exists',"danger")
                return redirect(url_for("add_laboratorist"))
            laboratorist = Laboratorist(fname=firstname, lname=lastname, gender=gender, date_of_birth=dob, email=email,
                                        password=generate_password_hash(password), cnic=cnic,
                                        contact_no=contact_no, address1=address1, address2=address2, rank=rank,
                                        shift=shift,
                                        account_no=acc_no, dep=department, lab=lab)
            try:
                add_to_db(laboratorist)
                labo = session.query(Laboratorist).filter_by(fname=firstname, lname=lastname, gender=gender,
                                                             date_of_birth=dob, email=email, cnic=cnic).first()
                send_email(labo.reg_no, password, email)
                flash('New Laboratorist Added Successfully',"success")
                return redirect(url_for('dashboard'))
            except:
                session.rollback()
                flash("Laboartorist was not added successfully")
        labs_list = session.query(Lab).all()
        departments_list = session.query(Department).all()
        return render_template('add_laboratorist.html', departments_list=departments_list, labs_list=labs_list)
    return redirect(url_for('log_in'))


def retrievePatientsAgainstNurse(nurse_id):
    nurse = session.query(Nurse).get(nurse_id)
    wards = session.query(Wards).with_parent(nurse).join(Patient).all()
    p = []
    for i in wards:
        p.append(session.query(Patient).filter_by(ward_id=i.ward_no).first())
    for x in p:
        print(x.fname)
    return p


def retrievePatientsAgainstDoctors(doctor_id):
    doc = session.query(Doctor).get(doctor_id)
    wards = session.query(Wards).with_parent(doc).join(Patient).all()
    p = []
    for i in wards:
        p.append(session.query(Patient).filter_by(ward_id=i.ward_no).first())


    return p


def retrieveRoomsAgainstKM(km_id):
    wards = session.query(Wards).filter_by(kitchen_manager=km_id).all()
    p = []
    b = []
    for i in wards:
        if i is not None:
            p.append(session.query(Patient).filter_by(ward_id=i.ward_no).first())
    for c in p:
        if c is not None:
            b.append(c)
    return b


def retrieveLabTests(id):
    pend = session.query(Pending_Lab_Test).filter_by(laboratorist_id=id).all()
    return pend


def getLabTestBill(pat_id):
    patient = session.query(Patient).filter_by(reg_no=pat_id).first()
    ward = session.query(Wards).filter_by(ward_no=patient.ward_id).first()

    return ward.lab_test_bill


def getMedicineBill(pat_id):
    med = session.query(Patient_Medicine, func.sum(Patient_Medicine.price).label("pr")).group_by(
        Patient_Medicine.patient_id).all()
    tot = 0
    for i in med:
        if i.Patient_Medicine.patient_id == pat_id:
            med_bill = i.pr
            tot += med_bill

    return tot


def getFoodBill(pat_id):
    patient = session.query(Patient).filter_by(reg_no=pat_id).first()

    now = datetime.now()  # Now
    duration = now - patient.reg_date  # For build-in functions
    days = duration.days

    ward = session.query(Wards).filter_by(ward_no=patient.ward_id).first()
    fBill = session.query(Ward_Type_Bill).filter_by(ward_type=ward.type).first()

    return int(fBill.food_bill_per_day) * days


def getRoomBill(pat_id):
    patient = session.query(Patient).filter_by(reg_no=pat_id).first()
    now = datetime.now()  # Now
    duration = now - patient.reg_date  # For build-in functions
    days = duration.days

    ward = session.query(Wards).filter_by(ward_no=patient.ward_id).first()
    rBill = session.query(Ward_Type_Bill).filter_by(ward_type=ward.type).first()

    return int(rBill.room_bill_per_day) * days


def send_email(reg_id, pwd, receiver):
    sender = "email@example.com"
    password = "strong_password"

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)

        server.ehlo()
        server.starttls()
        server.login(sender, password)

        msg = """Subject:Credentials For HMS IPD"""
        message = "\nWelcome to HMS IPD\nYour profile has been successfully created." \
                  "\nYour Login Credentials are as follows\n\nRegistration No.:\t{}\nPassword:\t\t{}\n \nDon't reply to this email".format(
            reg_id, pwd)
        msg += message
        server.sendmail(sender, receiver, msg)

        print("success")
    except smtplib.SMTPConnectError:
        flash("Unable to Connect To Server")
        return redirect(url_for('dashboard'))


@app.route('/update_password', methods=["GET", "POST"])
@login_required
def update_password():
    reg = str(current_user.reg_no)
    if reg[0] == '1':
        entity = Nurse
    elif reg[0] == '2':
        entity = Doctor
    elif reg[0] == '3':
        entity = Kitchen_Manager
    elif reg[0] == '4':
        entity = Laboratorist
    elif reg[0] == '5':
        entity = Patient
    elif reg[0] == "A":
        entity = Admin
        if request.method == 'POST':
            pat = session.query(entity).filter_by(reg_no=current_user.reg_no).first()
            oldpwd = request.form["old-password"]
            npwd = request.form["new-password"]
            cpwd = request.form["confirm-password"]
            if oldpwd != pat.password:
                flash("Incorrect Old Password", "danger")
                return render_template("change_password.html")
            elif npwd != cpwd:
                flash("Passwords do not match", "warning")
                return render_template("change_password.html")
            pat.password = npwd
            try:
                add_to_db(pat)
                flash("Password Changed Successfully","success")
                return redirect(url_for("dashboard"))
            except:
                session.rollback()
                flash("Password was not changed", "danger")
        personal = session.query(entity).filter_by(reg_no=current_user.reg_no).first()

        return render_template('change_password.html',personal_info=personal,entity=str(entity))

    else:
        return redirect(url_for("dashboard"))
    if request.method == 'POST':
        pat = session.query(entity).filter_by(reg_no=current_user.reg_no).first()
        oldpwd = request.form["old-password"]
        npwd = request.form["new-password"]
        cpwd = request.form["confirm-password"]

        if not check_password_hash(pat.password, oldpwd):
            flash("Incorrect Old Password", "danger")
            return render_template("change_password.html")
        elif npwd != cpwd:
            flash("Passwords do not match", "warning")
            return render_template("change_password.html")
        pat.password = generate_password_hash(npwd)
        try:
            add_to_db(pat)
            flash("Password Changed Successfully","success")
            return redirect(url_for("dashboard"))
        except:
            session.rollback()
            flash("Password was not changed", "danger")

    personal_info = session.query(entity).filter_by(reg_no=current_user.reg_no).first()

    return render_template('change_password.html' ,personal_info=personal_info,entity=str(entity ))


@app.route('/discharge_patient', methods=["GET", "POST"])
@login_required
def discharge_patient():
    reg = str(current_user.reg_no)
    if reg[0] == "A":
        patient_list = session.query(Patient).all()
        pending_test = []
        food_l = []
        room_l = []
        lab_l = []
        med_l = []
        total_l = []
        for x in patient_list:

            a = session.query(Pending_Lab_Test).filter_by(ward_no=x.ward_id).first()
            if a is not None:
                pending_test.append("Yes")
            else:
                pending_test.append("No")
            food = getFoodBill(x.reg_no)
            room = getRoomBill(x.reg_no)
            lab = getLabTestBill(x.reg_no)
            med = getMedicineBill(x.reg_no)
            total = 0
            if food is not None:
                total += food
                food_l.append(food)
            else:
                food_l.append(0)
            if room is not None:
                total += room
                room_l.append(room)
            else:
                room_l.append(0)
            if lab is not None:
                total += lab
                lab_l.append(lab)
            else:
                lab_l.append(0)
            if med is not None:
                total += med
                med_l.append(med)
            else:
                med_l.append(0)
            total_l.append(total)
        if request.method == 'POST':
            pid = request.form["pat_id"]
            p = session.query(Patient).filter_by(reg_no=pid).first()
            a = session.query(Pending_Lab_Test).filter_by(ward_no=p.ward_id).first()
            if a is not None:
                flash("Cannot Discharge Patient because lab test is pending", "warning")
                return redirect(url_for("discharge_patient"))
            else:
                try:
                    b = session.query(Patient).filter_by(reg_no=pid).first()
                    session.delete(b)
                    session.commit()
                    flash("Patient was discharged successfully", "success")
                except:
                    flash("Some Error occurred. Please Try again", "warning")
                    session.rollback()
                    return redirect(url_for("discharge_patient"))

            return redirect(url_for("discharge_patient"))

        return render_template("discharge_patient.html",
                               patient_pending_f_m_r_l_t=zip(patient_list, pending_test, food_l, med_l, room_l, lab_l,
                                                             total_l))
    return redirect(url_for("dashboard"))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    # flash("Logged Out Successfully", "success")
    return redirect(url_for('index'))


@login_manager.unauthorized_handler
def unauthorized():
    flash('You must be logged in to view that page', "warning")
    return redirect(url_for('log_in'))


if __name__ == '__main__':
    app.run(host = "0.0.0.0",port=5000)
