from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DecimalField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class PatientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Email()])
    phone = StringField('Phone')
    notes = TextAreaField('Notes')
    submit = SubmitField('Save')

class AppointmentForm(FlaskForm):
    name = StringField('Patient name', validators=[DataRequired()])
    email = StringField('Email', validators=[Email()])
    phone = StringField('Phone')
    date = StringField('Date & time (YYYY-MM-DD HH:MM)', validators=[DataRequired()])
    service = SelectField('Service', choices=[('Cleaning','Cleaning'),('Filling','Filling'),('Whitening','Whitening'),('Braces','Braces')])
    dentist = StringField('Dentist (optional)')
    notes = TextAreaField('Notes')
    submit = SubmitField('Save Appointment')

class TreatmentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price = DecimalField('Price', validators=[DataRequired()])
    submit = SubmitField('Save Treatment')

class InvoiceForm(FlaskForm):
    patient_name = StringField('Patient name', validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired()])
    description = TextAreaField('Description')
    status = SelectField('Status', choices=[('Unpaid','Unpaid'),('Paid','Paid')])
    submit = SubmitField('Create Invoice')
