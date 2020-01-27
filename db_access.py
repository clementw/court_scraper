import datetime

from sqlalchemy import Column, Integer, Boolean, Text, ForeignKey
from sqlalchemy import create_engine, exists
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    id_card = Column(Text)
    name = Column(Text)
    shixinStatus = Column(Boolean, default=False)
    shixinRecords = relationship("shixinRecord", backref='person')
    zhixingStatus = Column(Boolean, default=False)
    zhixingRecords = relationship("zhixingRecord", backref='person')


class shixinRecord(Base):
    __tablename__ = 'sxrecord'
    id_card = Column(Text, ForeignKey('person.id_card'))
    caseCode = Column(Text)
    age = Column(Integer)
    sexy = Column(Text)
    id = Column(Integer, primary_key=True)
    courtName = Column(Text)
    areaName = Column(Text)
    gistId = Column(Text)
    gistUnit = Column(Text)
    regDate = Column(Text)
    duty = Column(Text)
    performance = Column(Text)
    disruptTypeName = Column(Text)
    publishDate = Column(Text)
    businessEntity = Column(Text)
    unperformPart = Column(Text)
    performedPart = Column(Text)
    name = Column(Text)


class zhixingRecord(Base):
    __tablename__ = 'zxrecord'
    id_card = Column(Text, ForeignKey('person.id_card'))
    id = Column(Integer, primary_key=True)
    caseCode = Column(Text)
    execCourtName = Column(Text)
    execMoney = Column(Integer)
    caseCreateTime = Column(Text)
    name = Column(Text)


engine = create_engine('sqlite:///crawler_{}.db'.format(datetime.date.today()))

# create db
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()


def adduser(name, id_card):
    if id_card == '' and not session.query(exists().where(Person.name == name)).scalar():
        session.add(Person(name=name, id_card=None))
        session.commit()
    elif id_card and not session.query(exists().where(Person.id_card == id_card)).scalar():
        session.add(Person(name=name, id_card=id_card))
        session.commit()
    else:
        print('此人/公司已在数据库')


def add_sxrecord(d):
    if d['id_card'] != '':
        person = session.query(Person).filter_by(id_card=d['id_card']).first()
    else:
        person = session.query(Person).filter_by(name=d['name']).first()

    person.shixinStatus = True
    r = shixinRecord

    if not session.query(exists().where(r.id == d['id'])).scalar():
        session.add(r(**d))
        session.commit()
    else:
        print('记录已在数据库')


def add_zxrecord(d):
    if d['id_card'] != '':
        person = session.query(Person).filter_by(id_card=d['id_card']).first()
    else:
        person = session.query(Person).filter_by(name=d['name']).first()

    person.zhixingStatus = True
    r = zhixingRecord

    if not session.query(exists().where(r.id == d['id'])).scalar():
        session.add(r(**d))
        session.commit()
    else:
        print('记录已在数据库')


def check_record_sx(id_card, name):
    tmp = []

    if id_card == '':
        for row in session.query(shixinRecord).filter_by(name=name).all():
            d = row.__dict__
            d.pop('_sa_instance_state')
            tmp.append(d)
    else:
        for row in session.query(shixinRecord).filter_by(id_card=id_card).all():
            d = row.__dict__
            d.pop('_sa_instance_state')
            tmp.append(d)
    return tmp


def check_record_zx(id_card, name):
    tmp = []

    if id_card == '':
        for row in session.query(zhixingRecord).filter_by(name=name).all():
            d = row.__dict__
            d.pop('_sa_instance_state')
            tmp.append(d)
    else:
        for row in session.query(zhixingRecord).filter_by(id_card=id_card).all():
            d = row.__dict__
            d.pop('_sa_instance_state')
            tmp.append(d)
    return tmp


def check_name(id_card):
    person = session.query(Person).filter_by(id_card=id_card).first()
    return person.name
