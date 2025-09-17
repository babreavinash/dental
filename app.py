from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient, Appointment, Treatment, Invoice
from forms import LoginForm, PatientForm, AppointmentForm, TreatmentForm, InvoiceForm
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///practice.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create DB tables
with app.app_context():
    db.create_all()
    # create default admin if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', name='Administrator', role='admin') 
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

# Auth
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# ---- Public routes ----
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('home'))

# ---- Dashboard ----
@app.route('/dashboard')
@login_required
def dashboard():
    # summary stats
    patients_count = Patient.query.count()
    upcoming = Appointment.query.order_by(Appointment.date_time).limit(6).all()
    unpaid = Invoice.query.filter_by(status='Unpaid').count()
    return render_template('dashboard.html', patients_count=patients_count, upcoming=upcoming, unpaid=unpaid)

# ---- Patients CRUD ----
@app.route('/patients')
@login_required
def patients():
    q = request.args.get('q','')
    if q:
        items = Patient.query.filter(Patient.name.contains(q) | Patient.email.contains(q)).all()
    else:
        items = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template('patients/list.html', patients=items, q=q)

@app.route('/patients/new', methods=['GET','POST'])
@login_required
def patient_new():
    form = PatientForm()
    if form.validate_on_submit():
        p = Patient(name=form.name.data, email=form.email.data, phone=form.phone.data, notes=form.notes.data)
        db.session.add(p)
        db.session.commit()
        flash('Patient created', 'success')
        return redirect(url_for('patients'))
    return render_template('patients/form.html', form=form, action='New')

@app.route('/patients/<int:pid>/edit', methods=['GET','POST'])
@login_required
def patient_edit(pid):
    p = Patient.query.get_or_404(pid)
    form = PatientForm(obj=p)
    if form.validate_on_submit():
        form.populate_obj(p)
        db.session.commit()
        flash('Patient updated', 'success')
        return redirect(url_for('patients'))
    return render_template('patients/form.html', form=form, action='Edit')

@app.route('/patients/<int:pid>/delete', methods=['POST'])
@login_required
def patient_delete(pid):
    p = Patient.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash('Patient deleted', 'info')
    return redirect(url_for('patients'))

@app.route('/patients/<int:pid>')
@login_required
def patient_view(pid):
    p = Patient.query.get_or_404(pid)
    treatments = Treatment.query.filter_by(patient_id=p.id).order_by(Treatment.date.desc()).all()
    invoices = Invoice.query.filter(Invoice.patient_name==p.name).order_by(Invoice.created_at.desc()).all()
    return render_template('patients/view.html', patient=p, treatments=treatments, invoices=invoices)

# ---- Appointments ----
@app.route('/appointments')
@login_required
def appointments():
    items = Appointment.query.order_by(Appointment.date_time.desc()).all()
    return render_template('appointments/list.html', appointments=items)

@app.route('/appointments/new', methods=['GET','POST'])
@login_required
def appointment_new():
    form = AppointmentForm()
    if form.validate_on_submit():
        # ensure patient exists or create
        patient = Patient.query.filter_by(email=form.email.data).first()
        if not patient:
            patient = Patient(name=form.name.data, email=form.email.data, phone=form.phone.data)
            db.session.add(patient); db.session.flush()
        appt = Appointment(patient_id=patient.id, date_time=form.date.data, service=form.service.data, dentist=form.dentist.data, notes=form.notes.data)
        db.session.add(appt); db.session.commit()
        flash('Appointment created', 'success')
        return redirect(url_for('appointments'))
    return render_template('appointments/form.html', form=form)

@app.route('/appointments/<int:aid>/delete', methods=['POST'])
@login_required
def appointment_delete(aid):
    a = Appointment.query.get_or_404(aid)
    db.session.delete(a); db.session.commit()
    flash('Appointment removed', 'info')
    return redirect(url_for('appointments'))

# ---- Treatments ----
@app.route('/treatments', methods=['GET','POST'])
@login_required
def treatments():
    items = Treatment.query.order_by(Treatment.date.desc()).all()
    return render_template('treatments/list.html', treatments=items)

@app.route('/treatments/new', methods=['GET','POST'])
@login_required
def treatment_new():
    form = TreatmentForm()
    if form.validate_on_submit():
        t = Treatment(name=form.name.data, description=form.description.data, price=float(form.price.data))
        db.session.add(t); db.session.commit()
        flash('Treatment saved', 'success')
        return redirect(url_for('treatments'))
    return render_template('treatments/form.html', form=form)

# ---- Invoices ----
@app.route('/invoices')
@login_required
def invoices():
    items = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template('invoices/list.html', invoices=items)

@app.route('/invoices/new', methods=['GET','POST'])
@login_required
def invoice_new():
    form = InvoiceForm()
    if form.validate_on_submit():
        inv = Invoice(patient_name=form.patient_name.data, amount=float(form.amount.data), description=form.description.data, status=form.status.data)
        db.session.add(inv); db.session.commit()
        flash('Invoice created', 'success')
        return redirect(url_for('invoices'))
    return render_template('invoices/form.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
