# modules-import
import classes
import hashlib

# flask-import
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

# sqlalchemy-import
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

# other-import
from datetime import datetime, timedelta

# Parametri applicazione
app = Flask(__name__)
engine = create_engine('postgresql://postgres:postgres@localhost:5432/progetto_palestra', echo=True)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost:5432/progetto_palestra"
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Secret key
# app.config['SECRET_KEY'] = 'secret11'
app.secret_key = 'secret14'

# Gestione login
login_manager = LoginManager()
login_manager.init_app(app)

#Session
Session = sessionmaker(bind=engine)
Session.close_all()
session = Session()


# Variabili e costanti globali
first_id_client = 100


# Functions
def create_admin():
    exists = session.query(classes.Other).filter(classes.Other.id == 0).first()
    if not exists:
        new_id = 0
        pw = 'admin' + 'admin@palestra.it'
        user = classes.User(id=new_id, username="admin", password=hashlib.md5(pw.encode()).hexdigest(),
                            nome="admin", cognome="admin", email="admin@palestra.it",
                            datanascita='1000-01-01')
        admin = classes.Other(new_id)
        session.add(user)
        session.add(admin)
        session.commit()


# Getters
def get_user_by_email(email):
    user = session.query(classes.User).filter(classes.User.email == email).first()
    return classes.User(user.id, user.username, user.password, user.nome, user.cognome, user.email, user.datanascita)


# Funzioni per incrementare l'ultimo id utile
def get_id_increment():
    user = session.query(classes.User).filter(classes.User.id >= 100).order_by(classes.User.id.desc()).first()
    if user:
        return user.id + 1
    else:
        return first_id_client


def get_id_staff_increment():
    user = session.query(classes.User).filter(classes.User.id < 100).order_by(classes.User.id.desc()).first()
    if user:
        return user.id + 1
    else:
        return first_id_client


def get_course_id_increment():
    course = session.query(classes.Course).order_by(classes.Course.id.desc()).first()
    if course:
        return course.id + 1
    else:
        return 0


def get_room_id_increment():
    room = session.query(classes.Room).order_by(classes.Room.id.desc()).first()
    if room:
        return room.id + 1
    else:
        return 0


def get_weight_room_id_increment():
    weight_room = session.query(classes.WeightRoom).order_by(classes.WeightRoom.id.desc()).first()
    if weight_room:
        return weight_room.id + 1
    else:
        return 0


# Funzione per tornare l'utente amministratore
def get_admin_user():
    user = session.query(classes.User).filter(classes.User.id == 0).first()
    return classes.User(user.id, user.username, user.password, user.nome, user.cognome, user.email, user.datanascita)


# Funzione per tornare la data corrente
def get_current_date():
    now = datetime.now()
    return now.strftime("%Y-%m-%d")


# Funzione per incrementare la data di tot giorni
def get_increment_date(giorni):
    data = datetime.now() + timedelta(days=giorni)
    return data.strftime("%Y-%m-%d")


def get_subscription(subscription):
    sub = session.query(classes.Subscription).filter(classes.Subscription.tipo == subscription).first()
    return classes.Subscription(sub.id, sub.tipo, sub.costo)


def get_subscription_by_id(id):
    sub = session.query(classes.Subscription.tipo).filter(classes.Subscription.id == id).first()
    return sub


def get_subscriber_by_id(id):
    subscriber = session.query(classes.Subscriber).filter(classes.Subscriber.id == id).first()
    if subscriber:
        return classes.Subscriber(subscriber.id, subscriber.abbonamento, subscriber.datafineabbonamento,
                                  subscriber.datafineabbonamento, subscriber.durata)
    else:
        return None


def get_courses():
    courses = session.query(classes.Course).order_by(classes.Course.id.asc()).all()
    return courses


def get_course(idCorso):
    course = session.query(classes.Course).filter(classes.Course.id == idCorso).first()
    return classes.Course(course.id, course.nome, course.iscrittimax, course.istruttore, course.stanza)


def get_last_id_course():
    course = session.query(classes.Course).order_by(classes.Course.id.desc()).first()
    return course.id


def get_rooms():
    rooms = session.query(classes.Room).order_by(classes.Room.id.asc()).all()
    return rooms


def get_weight_rooms():
    weight_rooms = session.query(classes.WeightRoom).order_by(classes.WeightRoom.id.asc()).all()
    return weight_rooms


def get_trainers():
    trainers = session.query(classes.User).filter(classes.Trainer.id == classes.User.id).\
        order_by(classes.Trainer.id.asc()).all()
    return trainers


def get_others():
    others = session.query(classes.User).\
        filter(and_(classes.Other.id == classes.User.id, classes.User.id != 0)).order_by(classes.Other.id.asc()).all()
    return others


def get_clients():
    clients = session.query(classes.User).\
        filter(classes.Client.id == classes.User.id).order_by(classes.Client.id.asc()).all()
    return clients


def get_information():
    info = session.query(classes.Information).first()
    return classes.Information(info.accessisettimana, info.slotgiorno, info.personemaxslot, info.personemq)


def get_checks():
    checks = session.query(classes.Checks).first()
    return classes.Checks(checks.controllo)


# Funzione per prendere gli slot rispetto ad un giorno
def get_slot_from_date(data):
    slots = session.query(classes.Slot).filter(classes.Slot.giorno == data).order_by(classes.Slot.orainizio).all()
    return slots


# Funzione per prendere le sale pesi presenti in un certo slot
def get_slot_weight_rooms(idSlot, subscription):
    if subscription == 'corsi':
        return []
    else:
        weightrooms = session.query(classes.WeightRoom).filter(classes.WeightRoom.id.in_(
            session.query(classes.WeightRoomSlot.salapesi).filter(classes.WeightRoomSlot.slot == idSlot)
        )).all()
        return weightrooms


# Funzione per prendere i corsi presenti in un certo slot
def get_slot_courses(idSlot, subscription):
    if subscription == 'sala_pesi':
        return []
    else:
        courses = session.query(classes.Course).filter(classes.Course.id.in_(
            session.query(classes.CourseSlot.corso).filter(classes.CourseSlot.slot == idSlot)
        )).all()
        return courses


# Funzione per prendere l'id della seduta del corso in un determinato slot
def get_coursesitting_id(idSlot, idCorso):
    giorno = session.query(classes.Slot.giorno).filter(classes.Slot.id == idSlot)
    id_sitting = session.query(classes.CourseSitting.id).\
        filter(and_(func.DATE(classes.CourseSitting.dataseduta) == giorno, classes.CourseSitting.corso == idCorso)).\
        first()
    return id_sitting


# Funzione per prendere l'id della seduta di una sala pesi in un determinato slot
def get_weightroomsitting_id(idSlot, idSala):
    giorno = session.query(classes.Slot.giorno).filter(classes.Slot.id == idSlot)
    id_sitting = session.query(classes.WeightRoomSitting.id).\
        filter(and_(func.DATE(classes.WeightRoomSitting.dataseduta) == giorno,
                    classes.WeightRoomSitting.salapesi == idSala)).first()
    return id_sitting


# Funzione per ottenere le prenotazioni cancellabili
def get_reservations(idSub):
    reservations = session.query(classes.Reservation.slot, classes.Slot.giorno, classes.Slot.orainizio,
                                 classes.Slot.orafine).\
        filter(and_(classes.Reservation.slot == classes.Slot.id, classes.Reservation.abbonato == idSub,
                    classes.Slot.giorno > func.current_date())).\
        order_by(classes.Slot.giorno, classes.Slot.orainizio).all()
    return reservations


# Funzione per ottenere le prenotazioni di un abbonato
def get_all_reservations(idSub):
    reservations = session.query(classes.Reservation.slot, classes.Slot.giorno, classes.Slot.orainizio,
                                 classes.Slot.orafine).\
        filter(and_(classes.Reservation.slot == classes.Slot.id, classes.Reservation.abbonato == idSub)).\
        order_by(classes.Slot.giorno, classes.Slot.orainizio).all()
    return reservations


# Funzione per ottenere le prenotazioni di un non abbonato
def get_all_ns_reservations(idNSub):
    nsreservations = session.query(classes.NSReservation.slot, classes.Slot.giorno, classes.Slot.orainizio,
                                 classes.Slot.orafine).\
        filter(and_(classes.NSReservation.slot == classes.Slot.id, classes.NSReservation.nonabbonato == idNSub,
                    classes.Slot.giorno <= func.current_date())).\
        order_by(classes.Slot.giorno, classes.Slot.orainizio).all()
    return nsreservations


def get_last_seven_days():
    days = session.query(classes.Day).\
        filter(and_(classes.Day.data > func.current_date() - 7, classes.Day.data <= func.current_date()))
    return days


# Funzione per ottenere i possibili contagiati da un infetto
def get_infected(giorno, infetto):
    slots1 = session.query(classes.Reservation.slot).\
        filter(and_(classes.Reservation.abbonato == infetto, classes.Reservation.slot == classes.Slot.id,
                    classes.Slot.giorno >= giorno))
    slots2 = session.query(classes.NSReservation.slot).\
        filter(and_(classes.NSReservation.nonabbonato == infetto, classes.NSReservation.slot == classes.Slot.id,
                    classes.Slot.giorno >= giorno))
    slots = slots1.union(slots2)
    sub_infected = session.query(classes.User).\
        filter(and_(classes.User.id != infetto, classes.User.id == classes.Subscriber.id,
                    classes.User.id == classes.Reservation.abbonato, classes.Reservation.slot.in_(slots)))
    notsub_infected = session.query(classes.User).\
        filter(and_(classes.User.id != infetto, classes.User.id == classes.NotSubscriber.id,
                    classes.User.id == classes.NSReservation.nonabbonato, classes.NSReservation.slot.in_(slots)))
    infected = sub_infected.union(notsub_infected).all()
    return infected


# Booleans
def is_subscriber(user_id):
    p_query = session.query(classes.Subscriber).filter(classes.Subscriber.id == user_id).first()
    if p_query:
        return True
    else:
        return False


def is_reserved(user_id, idSlot):
    res = session.query(classes.Reservation).\
        filter(and_(classes.Reservation.abbonato == user_id, classes.Reservation.slot == idSlot)).first()
    if res:
        return True
    else:
        return False


# Funzione per controllare se è possibile prenotarsi in un certo slot
def is_available_slot(idSlot):
    res = session.query(func.count(classes.Reservation.abbonato)).filter(classes.Reservation.slot == idSlot).first()
    personemax = session.query(classes.Slot.personemax).filter(classes.Slot.id == idSlot).first()
    if res < personemax:
        return True
    else:
        return False


# Funzione per controllare se è possibile prenotarsi per un certo corso in un determinato slot
def is_available_course(idSeduta, idSlot):
    res = session.query(func.count()).filter(classes.SubscriberCourseSession.seduta == idSeduta).first()
    corso = session.query(classes.CourseSitting.corso).filter(classes.CourseSitting.id == idSeduta)
    iscrittimax_corso = session.query(classes.Course.iscrittimax).filter(classes.Course.id == corso).first()
    iscrittimax_corsislot = session.query(classes.CourseSlot.iscrittimax).\
        filter(and_(classes.CourseSlot.corso == corso, classes.CourseSlot.slot == idSlot)).first()
    if res < iscrittimax_corso and res < iscrittimax_corsislot:
        return True
    else:
        return False


# Funzione per controllare se è possibile prenotarsi per una certa sala pesi in un determinato slot
def is_available_weight_room(idSeduta, idSlot):
    res = session.query(func.count()).filter(classes.SubscriberWeightRoomSession.seduta == idSeduta).first()
    sala = session.query(classes.WeightRoomSitting.salapesi).filter(classes.WeightRoomSitting.id == idSeduta)
    iscrittimax_sala = session.query(classes.WeightRoom.iscrittimax).filter(classes.WeightRoom.id == sala).first()
    iscrittimax_salapesislot = session.query(classes.WeightRoomSlot.iscrittimax).\
        filter(and_(classes.WeightRoomSlot.salapesi == sala, classes.WeightRoomSlot.slot == idSlot)).first()
    if res < iscrittimax_sala and res < iscrittimax_salapesislot:
        return True
    else:
        return False


# Funzione per controllare si ha sforato il numero di accessi settimanali
def has_exceeded_accessisettimana(user_id, giorno):
    res1 = session.query(func.extract('dow', func.DATE(giorno))).first()
    res1 = int(str(res1)[1:2])
    if res1 > 0:
        res2 = session.query(func.count(classes.Slot.giorno.distinct())).\
            filter(and_(classes.Reservation.slot == classes.Slot.id, classes.Reservation.abbonato == user_id,
                        classes.Slot.giorno > func.DATE(giorno) - res1,
                        classes.Slot.giorno <= func.DATE(giorno) + (7 - res1),
                        classes.Slot.giorno != func.DATE(giorno))).first()
    else:
        res2 = session.query(func.count(classes.Slot.giorno.distinct())).\
            filter(and_(classes.Reservation.slot == classes.Slot.id, classes.Reservation.abbonato == user_id,
                        classes.Slot.giorno >= func.DATE(giorno) - 6, classes.Slot.giorno <= func.DATE(giorno),
                        classes.Slot.giorno != func.DATE(giorno))).first()
    res3 = session.query(classes.Information.accessisettimana).first()
    if res2 < res3:
        return False
    else:
        return True


# Funzione per controllare si ha sforato il numero di slot prenotabili al giorno
def has_exceeded_slotgiorno(user_id, giorno):
    res1 = session.query(func.count()).\
        filter(and_(classes.Reservation.slot == classes.Slot.id, classes.Reservation.abbonato == user_id,
                    classes.Slot.giorno == func.DATE(giorno))).first()
    res2 = session.query(classes.Information.slotgiorno).first()
    if res1 >= res2:
        return True
    else:
        return False


# Update
def set_checks(controlliGiornalieri):
    session.query(classes.Checks).update({"controllo": controlliGiornalieri})


def set_information_accessisettimana(accessiSettimana):
    session.query(classes.Information).update({"accessisettimana": accessiSettimana})


def set_information_slotgiorno(slotGiorno):
    session.query(classes.Information).update({"slotgiorno": slotGiorno})


def set_information_personemaxslot(personeMax):
    session.query(classes.Information).update({"personemaxslot": personeMax})


def set_information_personemq(personeMq):
    session.query(classes.Information).update({"personemq": personeMq})


def update_weight_room(idSala, dimensione):
    pmq = get_information().personemq
    session.query(classes.WeightRoom).\
        filter(classes.WeightRoom.id == idSala).update({"dimensione": dimensione, "iscrittimax": int(dimensione)/pmq})


def update_room(idStanza, nome, dimensione):
    session.query(classes.Room).filter(classes.Room.id == idStanza).update({"nome": nome, "dimensione": dimensione})


def update_course(idCorso, nome, iscrittiMax, idIstruttore, idStanza):
    session.query(classes.Course).\
        filter(classes.Course.id == idCorso).update({"nome": nome, "iscrittimax": iscrittiMax,
                                                     "istruttore": idIstruttore, "stanza": idStanza})


# Remove
def remove_room(idStanza):
    session.query(classes.Room).filter(classes.Room.id == idStanza).delete()


def remove_weight_room(idSala):
    session.query(classes.WeightRoom).filter(classes.WeightRoom.id == idSala).delete()


def remove_course(idCorso):
    session.query(classes.Course).filter(classes.Course.id == idCorso).delete()


def remove_user(idUser):
    session.query(classes.User).filter(classes.User.id == idUser).delete()


def remove_not_subscriber(idCliente):
    session.query(classes.NotSubscriber).filter(classes.NotSubscriber.id == idCliente).delete()


def is_reserved_course(idSub, idSlot):
    res = session.query(classes.SubscriberCourseSession.abbonato).\
        filter(and_(classes.SubscriberCourseSession.abbonato == idSub,
                    classes.SubscriberCourseSession.seduta == classes.CourseSitting.id,
                    classes.CourseSitting.corso == classes.Course.id, classes.Course.id == classes.CourseSlot.corso,
                    classes.CourseSlot.slot == idSlot)).first()
    if res is not None:
        return True
    else:
        return False


# Funzione per rimuovere la prenotazione di un certo abbonato in un determinato slot
def remove_reservation(idSub, idSlot):
    session.query(classes.Reservation).\
        filter(and_(classes.Reservation.abbonato == idSub, classes.Reservation.slot == idSlot)).delete()
    if is_reserved_course(idSub, idSlot):
        session.query(classes.SubscriberCourseSession).\
            filter(and_(classes.SubscriberCourseSession.abbonato == idSub,
                        classes.SubscriberCourseSession.seduta == classes.CourseSitting.id,
                        classes.CourseSitting.corso == classes.Course.id, classes.Course.id == classes.CourseSlot.corso,
                        classes.CourseSlot.slot == idSlot)).delete(synchronize_session='fetch')
    else:
        session.query(classes.SubscriberWeightRoomSession).\
            filter(and_(classes.SubscriberWeightRoomSession.abbonato == idSub,
                        classes.SubscriberWeightRoomSession.seduta == classes.WeightRoomSitting.id,
                        classes.WeightRoomSitting.salapesi == classes.WeightRoom.id,
                        classes.WeightRoom.id == classes.WeightRoomSlot.salapesi,
                        classes.WeightRoomSlot.slot == idSlot)).delete(synchronize_session='fetch')


# Add
def add_course_slot(idCorso, giorno, orario):
    p_query = "CALL aggiungi_corsi_slot(" + str(idCorso) + ", " + str(giorno) + ", TIME '" + str(orario) + "')"
    session.execute(p_query)
    session.commit()
    session.close()


def add_weight_room_slot(idSala):
    p_query = "CALL aggiungi_salapesi_slot(" + str(idSala) + ")"
    session.execute(p_query)
    session.commit()
    session.close()