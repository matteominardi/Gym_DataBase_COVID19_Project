# modules-import
import classes
import functions
import hashlib

# flask-import
from flask import Flask, render_template, request, url_for, make_response
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from flask_migrate import Migrate

# sqlalchemy-import
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *

# other-import
from werkzeug.utils import redirect
from datetime import datetime
from functools import wraps


# Parametri applicazione
app = Flask(__name__)
engine = create_engine('postgresql://postgres:postgres@localhost:5432/progetto_palestra', echo=True)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost:5432/progetto_palestra"
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Secret key
app.secret_key = 'secret14'

# Gestione login
login_manager = LoginManager()
login_manager.init_app(app)

# Sessione
session = functions.session


# Variabili e costanti globali
first_id_client = 100
admin_email = 'admin@palestra.it'
admin_pwd = hashlib.md5(("admin" + admin_email).encode()).hexdigest()


# Decoratore admin_required
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user == functions.get_admin_user():
            return redirect(url_for('wrong'))
        return f(*args, **kwargs)

    return decorated_function


# user_loader
@login_manager.user_loader
def load_user(user_id):
    user = session.query(classes.User).filter(classes.User.id == user_id).first()
    return classes.User(user.id, user.username, user.password, user.nome, user.cognome, user.email, user.datanascita)


# Routes
@app.route('/')
def home():
    functions.create_admin()
    i = datetime.now()
    mydate = classes.MyDate(i.year, i.month, i.day)
    return render_template("index.html", month=i.month, year=i.year, day=i.day, first_column=mydate.first_column,
                           last_day=mydate.last_day)


@app.route('/confirm')
def confirm():
    return render_template("confirm.html")


@app.route('/wrong')
def wrong():
    return render_template("wrong.html")


@app.route('/signin')
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('private'))
    else:
        return render_template("signin.html")


@app.route('/signup')
def signup():
    return render_template("signup.html")


@app.route('/create', methods=['GET', 'POST'])
def create_user():
    new_id = functions.get_id_increment()
    pw = request.form['password'] + request.form['email']
    user = classes.User(id=new_id, username=request.form['username'], password=hashlib.md5(pw.encode()).hexdigest(),
                        nome=request.form['nome'], cognome=request.form['cognome'], email=request.form['email'],
                        datanascita=request.form['dataNascita'])
    client = classes.Client(id=new_id)
    session.add(user)
    session.add(client)
    if request.form['abb'] != "null":  # controllo se è stato scelto oppure no un abbonamento
        sub = functions.get_subscription(request.form['abb'])
        if request.form['abb'] == 'prova':
            subscriber = classes.Subscriber(id=new_id, abbonamento=sub.id,
                                            datainizioabbonamento=functions.get_current_date(),
                                            datafineabbonamento=functions.get_increment_date(7),
                                            durata=7)
            session.add(subscriber)
        else:
            subscriber = classes.Subscriber(id=new_id, abbonamento=sub.id,
                                            datainizioabbonamento=functions.get_current_date(),
                                            datafineabbonamento=functions.get_increment_date(int(request.form['durata'])),
                                            durata=request.form['durata'])
            session.add(subscriber)
    else:
        not_subscriber = classes.NotSubscriber(id=new_id)
        session.add(not_subscriber)
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/reserved_private')
def reserved():
    if current_user.is_authenticated:
        return redirect(url_for('private'))
    return redirect(url_for('signin'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        p_email = request.form['user']
        p_pass = hashlib.md5((request.form['pass'] + p_email).encode()).hexdigest()
        real_pwd = session.query(classes.User.password).filter(classes.User.email == p_email).first()
        if p_email == admin_email:  # controllo se l'utente è l'admin
            real_pwd = real_pwd['password']
            if real_pwd is not None and p_pass == real_pwd:
                user = functions.get_user_by_email(request.form['user'])
                login_user(user)
                return redirect(url_for('administration'))
            else:
                return redirect(url_for('wrong'))
        elif real_pwd is not None:
            real_pwd = real_pwd['password']
            if p_pass == real_pwd:
                user = functions.get_user_by_email(request.form['user'])
                login_user(user)
                return redirect(url_for('private'))
            else:
                return redirect(url_for('wrong'))
        else:
            return redirect(url_for('wrong'))
    else:
        return redirect(url_for('wrong'))


@app.route('/private')
@login_required
def private():
    if current_user == functions.get_admin_user():
        return redirect(url_for('administration'))
    else:
        sub = functions.is_subscriber(current_user.id)
        resp = make_response(render_template("private.html", current_user=current_user, sub=sub))
        return resp


@app.route('/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe():
    user_id = current_user.id
    if not functions.is_subscriber(user_id) and request.form['abb'] != 'null':  # controllo che non sia abbonato
        sub = functions.get_subscription(request.form['abb'])
        if request.form['abb'] == 'prova':
            subscriber = classes.Subscriber(id=user_id, abbonamento=sub.id,
                                            datainizioabbonamento=functions.get_current_date(),
                                            datafineabbonamento=functions.get_increment_date(7),
                                            durata=7)
            session.add(subscriber)
        else:
            subscriber = classes.Subscriber(id=user_id, abbonamento=sub.id,
                                            datainizioabbonamento=functions.get_current_date(),
                                            datafineabbonamento=functions.get_increment_date(int(request.form['durata'])),
                                            durata=request.form['durata'])
            session.add(subscriber)
        functions.remove_not_subscriber(user_id)
        session.commit()
        return redirect(url_for('confirm'))
    else:
        return redirect(url_for('wrong'))


@app.route('/info_user', methods=['GET', 'POST'])
@login_required
def info_user():
    subscriber = functions.get_subscriber_by_id(current_user.id)
    if subscriber is not None:
        reservations = functions.get_all_reservations(current_user.id)
        subscription = functions.get_subscription_by_id(subscriber.abbonamento)
        return render_template("info_user.html", subscription=subscription['tipo'], subscriber=subscriber,
                               reservations=reservations)
    else:
        reservations = functions.get_all_ns_reservations(current_user.id)
        subscription = None
        return render_template("info_user.html", subscription=subscription, subscriber=subscriber,
                               reservations=reservations)


@app.route('/calendar', methods=['GET', 'POST'])
@login_required
def calendar():
    if functions.is_subscriber(current_user.id):
        mydate = classes.MyDate(request.form['anno'], request.form['mese'], request.form['giorno'])
        return render_template("calendar.html", year=request.form['anno'], month=request.form['mese'],
                               day=request.form['giorno'], first_column=mydate.first_column, last_day=mydate.last_day)
    else:
        return redirect(url_for('wrong'))


@app.route('/book_day', methods=['GET', 'POST'])
@login_required
def book_day():
    if (not functions.has_exceeded_accessisettimana(current_user.id, request.form['datapassata'])) and \
            (not functions.has_exceeded_slotgiorno(current_user.id, request.form['datapassata'])):
        slots = functions.get_slot_from_date(request.form['datapassata'])
        return render_template("book_day.html", slots=slots, data=request.form['datapassata'])
    else:
        return redirect(url_for('wrong'))


@app.route('/book_slot', methods=['GET', 'POST'])
@login_required
def book_slot():
    idSlot = request.form['idSlot']
    if functions.is_available_slot(idSlot) and (not functions.is_reserved(current_user.id, idSlot)):
        sub = functions.get_subscriber_by_id(current_user.id)
        if sub is not None:
            subscription = functions.get_subscription_by_id(sub.abbonamento)
            weight_rooms = functions.get_slot_weight_rooms(idSlot, subscription['tipo'])
            courses = functions.get_slot_courses(idSlot, subscription['tipo'])
            return render_template("book_slot.html", idSlot=idSlot, weight_rooms=weight_rooms, courses=courses)
    else:
        return redirect(url_for('wrong'))


@app.route('/book_weight_room', methods=['GET', 'POST'])
@login_required
def book_weight_room():
    idSlot = request.form['idSlot']
    idSeduta = functions.get_weightroomsitting_id(idSlot, request.form['idSala'])
    idSeduta = idSeduta['id']
    if functions.is_available_weight_room(idSeduta, idSlot):  # controllo che la prenotazione si possa effettuare
        reservation = classes.Reservation(abbonato=current_user.id, slot=idSlot)
        subscriber_session = classes.SubscriberWeightRoomSession(abbonato=current_user.id, seduta=idSeduta)
        session.add(subscriber_session)
        session.add(reservation)
        session.commit()
        return redirect(url_for('confirm'))
    else:
        return redirect(url_for('wrong'))


@app.route('/cancel_reservation', methods=['GET', 'POST'])
@login_required
def cancel_reservation():
    reservations = functions.get_reservations(current_user.id)
    return render_template("cancel_reservation.html", reservations=reservations)


@app.route('/cancel_reservation_conf', methods=['GET', 'POST'])
@login_required
def cancel_reservation_conf():
    if functions.is_reserved(current_user.id, request.form['idSlot']):
        functions.remove_reservation(current_user.id, request.form['idSlot'])
        session.commit()
        return redirect(url_for('confirm'))
    else:
        return redirect(url_for('wrong'))


@app.route('/book_course', methods=['GET', 'POST'])
@login_required
def book_course():
    idSlot = request.form['idSlot']
    idSeduta = functions.get_coursesitting_id(idSlot, request.form['idCorso'])
    idSeduta = idSeduta['id']
    if functions.is_available_course(idSeduta, idSlot):  # controllo che la prenotazione si possa effettuare
        reservation = classes.Reservation(abbonato=current_user.id, slot=idSlot)
        subscriber_session = classes.SubscriberCourseSession(abbonato=current_user.id, seduta=idSeduta)
        session.add(subscriber_session)
        session.add(reservation)
        session.commit()
        return redirect(url_for('confirm'))
    else:
        return redirect(url_for('wrong'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/info')
def info():
    return render_template("info.html", courses=functions.get_courses(), rooms=functions.get_rooms(),
                           weight_rooms=functions.get_weight_rooms(), trainers=functions.get_trainers())


@app.route('/administration')
@login_required
def administration():
    if current_user == functions.get_admin_user():
        info = functions.get_information()
        checks = functions.get_checks()
        resp = make_response(render_template("administration.html", current_user=current_user,
                                             controllo=checks.controllo, accessi_settimana=info.accessisettimana,
                                             slot_giorno=info.slotgiorno, persone_max=info.personemaxslot,
                                             personemq=info.personemq))
        return resp
    else:
        return redirect(url_for('private'))


@app.route('/edit_checks', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_checks():
    functions.set_checks(request.form['controlliGiornalieri'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/edit_information_accessi', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_information_accessi():
    functions.set_information_accessisettimana(request.form['accessiSettimana'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/edit_information_tempo', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_information_tempo():
    functions.set_information_slotgiorno(request.form['tempoAllenamento'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/edit_information_personemax', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_information_personemax():
    functions.set_information_personemaxslot(request.form['personeMassime'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/edit_information_personemq', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_information_personemq():
    functions.set_information_personemq(request.form['personeMq'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/edit_courses', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_courses():
    trainers = functions.get_trainers()
    rooms = functions.get_rooms()
    courses = functions.get_courses()
    courses2 = functions.get_courses()
    return render_template("edit_courses.html", trainers=trainers, rooms=rooms, courses=courses, courses2=courses2)


@app.route('/edit_trainers', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_trainers():
    trainers = functions.get_trainers()
    return render_template("edit_trainers.html", trainers=trainers)


@app.route('/edit_others', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_others():
    others = functions.get_others()
    return render_template("edit_others.html", others=others)


@app.route('/add_trainer', methods=['GET', 'POST'])
@login_required
@admin_required
def add_trainer():
    return render_template("add_trainer.html")


@app.route('/add_trainer_conf', methods=['GET', 'POST'])
@login_required
@admin_required
def add_trainer_conf():
    new_id = functions.get_id_staff_increment()
    pw = request.form['password'] + request.form['email']
    user = classes.User(id=new_id, username=request.form['username'], password=hashlib.md5(pw.encode()).hexdigest(),
                        nome=request.form['nome'], cognome=request.form['cognome'], email=request.form['email'],
                        datanascita=request.form['dataNascita'])
    trainer = classes.Trainer(id=new_id)
    session.add(user)
    session.add(trainer)
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/remove_trainer', methods=['GET', 'POST'])
@login_required
@admin_required
def remove_trainer():
    functions.remove_user(request.form['idIstruttore'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/add_other', methods=['GET', 'POST'])
@login_required
@admin_required
def add_other():
    return render_template("add_other.html")


@app.route('/add_other_conf', methods=['GET', 'POST'])
@login_required
@admin_required
def add_other_conf():
    new_id = functions.get_id_staff_increment()
    pw = request.form['password'] + request.form['email']
    user = classes.User(id=new_id, username=request.form['username'], password=hashlib.md5(pw.encode()).hexdigest(),
                        nome=request.form['nome'], cognome=request.form['cognome'], email=request.form['email'],
                        datanascita=request.form['dataNascita'])
    other = classes.Other(id=new_id)
    session.add(user)
    session.add(other)
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/remove_other', methods=['GET', 'POST'])
@login_required
@admin_required
def remove_other():
    functions.remove_user(request.form['idAltro'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/add_course', methods=['GET', 'POST'])
@login_required
@admin_required
def add_course():
    new_id = functions.get_course_id_increment()
    course = classes.Course(id=new_id, nome=request.form['nome'], iscrittimax=request.form['iscrittimax'],
                            istruttore=request.form['idIstruttore'], stanza=request.form['idStanza'])
    session.add(course)
    session.commit()
    functions.add_course_slot(new_id, request.form['primoGiorno'], request.form['slot'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/remove_course', methods=['GET', 'POST'])
@login_required
@admin_required
def remove_course():
    functions.remove_course(request.form['idCorso'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/update_course', methods=['GET', 'POST'])
@login_required
@admin_required
def update_course():
    course = functions.get_course(request.form['idCorso'])
    trainers = functions.get_trainers()
    rooms = functions.get_rooms()
    return render_template("update_course.html", course=course, trainers=trainers, rooms=rooms)


@app.route('/update_course_conf', methods=['GET', 'POST'])
@login_required
@admin_required
def update_course_conf():
    functions.update_course(request.form['sCorso'], request.form['nome'], request.form['iscrittiMax'],
                            request.form['idIstruttore'], request.form['idStanza'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/edit_rooms', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_rooms():
    rooms = functions.get_rooms()
    rooms2 = functions.get_rooms()
    return render_template("edit_rooms.html", rooms=rooms, rooms2=rooms2)


@app.route('/add_room', methods=['GET', 'POST'])
@login_required
@admin_required
def add_room():
    new_id = functions.get_room_id_increment()
    room = classes.Room(id=new_id, nome=request.form['nome'], dimensione=request.form['dim'])
    session.add(room)
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/remove_room', methods=['GET', 'POST'])
@login_required
@admin_required
def remove_room():
    functions.remove_room(request.form['idStanza'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/update_room', methods=['GET', 'POST'])
@login_required
@admin_required
def update_room():
    functions.update_room(request.form['idStanza'], request.form['nome'], request.form['dim'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/edit_weight_rooms', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_weight_rooms():
    weight_rooms = functions.get_weight_rooms()
    weight_rooms2 = functions.get_weight_rooms()
    return render_template("edit_weight_rooms.html", weight_rooms=weight_rooms, weight_rooms2=weight_rooms2)


@app.route('/add_weight_room', methods=['GET', 'POST'])
@login_required
@admin_required
def add_weight_room():
    new_id = functions.get_weight_room_id_increment()
    pmq = functions.get_information().personemq
    dimensione = request.form['dim']
    iscrittimax = int(dimensione)/pmq
    weight_room = classes.WeightRoom(id=new_id, dimensione=dimensione, iscrittimax=iscrittimax)
    session.add(weight_room)
    session.commit()
    functions.add_weight_room_slot(new_id)
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/remove_weight_room', methods=['GET', 'POST'])
@login_required
@admin_required
def remove_weight_room():
    functions.remove_weight_room(request.form['idSala'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/update_weight_room', methods=['GET', 'POST'])
@login_required
@admin_required
def update_weight_room():
    functions.update_weight_room(request.form['idSala'], request.form['dim'])
    session.commit()
    return redirect(url_for('confirm'))


@app.route('/contact_tracing', methods=['GET', 'POST'])
@login_required
@admin_required
def contact_tracing():
    giorni = functions.get_last_seven_days()
    clienti = functions.get_clients()
    return render_template("contact_tracing.html", days=giorni, clients=clienti)


@app.route('/contact_tracing_result', methods=['GET', 'POST'])
@login_required
@admin_required
def contact_tracing_result():
    giorno = request.form['data']
    infetto = request.form['idCliente']
    contagiati = functions.get_infected(giorno, infetto)
    return render_template("contact_tracing_result.html", contagiati=contagiati)