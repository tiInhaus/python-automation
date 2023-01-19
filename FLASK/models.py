from unittest import result
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import datetime

db = SQLAlchemy()

class RASP_NAMES(db.Model):
    __tablename__ = "RASP_NAMES"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    descricao = db.Column(db.String(200))
    date_updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __init__(self, name, descricao, date_updated):
        self.name = name
        self.descricao = descricao
        self.date_updated = date_updated

    def __repr__(self):
            return f'{self.name}>'



class RASP_URLS(db.Model):
    __tablename__ = "RASP_URLS"
    id = db.Column(db.Integer, primary_key=True)
    rasp_id = db.Column(db.Integer, db.ForeignKey('RASP_NAMES.id'))
    url = db.Column(db.String(500))
    ordem = db.Column(db.Integer)
    tempo = db.Column(db.Integer)
    date_updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __init__(self, rasp_id, url, ordem, tempo, date_update):
        self.rasp_id = rasp_id
        self.url = url
        self.ordem = ordem
        self.tempo = tempo
        self.date_update = date_update

    def __repr__(self):
            return f'{self.rasp_id}>'




class VISTA_USER_ALERTS(db.Model):
    __tablename__ = "VISTA_USER_ALERTS"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    telegram_id = db.Column(db.String(20))
    cr_list = db.Column(db.String(100))
    alerta1 = db.Column(db.Boolean)
    alerta2 = db.Column(db.Boolean)
    alerta3 = db.Column(db.Boolean)
    alerta4 = db.Column(db.Boolean)
    date_updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __init__(self, name, telegram_id,alerta1, alerta2,alerta3,alerta4, cr_list, date_updated):
        self.name = name
        self.telegram_id = telegram_id
        self.cr_list = cr_list
        self.alerta1 = alerta1
        self.alerta2 = alerta2
        self.alerta3 = alerta3
        self.alerta4 = alerta4
        self.date_updated = date_updated

    def __repr__(self):
            return f'{self.name}>'