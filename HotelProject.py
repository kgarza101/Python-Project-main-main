from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = '4321'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
db = SQLAlchemy(app)

class CustomerBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(80), nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    check_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    check_out = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    housekeeping = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<CustomerBooking %r>' % self.guest_name

USERNAME = 'Admin'
PASSWORD = 'password123'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'is_authenticated' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def base():
    is_authenticated = session.get('is_authenticated', False)
    return render_template('base.html', is_authenticated=is_authenticated)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['is_authenticated'] = True
            next_page = request.args.get('next')
            return redirect(next_page or url_for('base'))
        else:
            return 'Login Failed'
    return render_template("login.html")

@app.route('/Bookings')
@login_required
def bookings():
    all_bookings = CustomerBooking.query.all()
    return render_template('Bookings.html', bookings=all_bookings)

@app.route('/CustomerBookings', methods=['GET', 'POST'])
@login_required
def customer_bookings():
    error_message = None

    if request.method == 'POST':
        guest_name = request.form['guest_name']
        room_number = int(request.form['room_number'])
        check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%dT%H:%M')
        check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%dT%H:%M')

        if check_in < datetime.now() or check_out < datetime.now():
            error_message = 'Cannot book dates in the past.'
        elif check_in >= check_out:
            error_message = 'Check-in date must be before check-out date.'

        if not error_message:
            existing_bookings = CustomerBooking.query.filter_by(room_number=room_number).all()
            for booking in existing_bookings:
                if check_in < booking.check_out and check_out > booking.check_in:
                    error_message = 'This room is already booked for the selected dates.'
                    break

        if not error_message:
            housekeeping = 'housekeeping' in request.form
            new_booking = CustomerBooking(
                guest_name=guest_name,
                room_number=room_number,
                check_in=check_in,
                check_out=check_out,
                housekeeping=housekeeping
            )
            db.session.add(new_booking)
            db.session.commit()
            return redirect(url_for('payment'))

    all_customer_bookings = CustomerBooking.query.all()
    return render_template('CustomerBookings.html', bookings=all_customer_bookings, error_message=error_message)

@app.route('/payment')
@login_required
def payment():
    return render_template('payment.html')

@app.route('/confirm_payment', methods=['POST'])
@login_required
def confirm_payment():
    card_number = request.form.get('card_number')
    if card_number.isdigit():  # Checks if the input is a number
        return 'Payment Successful! Your booking is confirmed.'
    else:
        return 'Invalid card number. Please enter a valid number.', 400


@app.route('/logout')
def logout():
    session.pop('is_authenticated', None)
    return redirect(url_for('base'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
