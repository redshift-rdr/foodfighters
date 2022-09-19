from app import db
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import backref
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), index=True, unique=True, default=generate_uuid)
    name = db.Column(db.String(32), index=True)

    recurring = db.relationship('RecurringRecord', back_populates='profile')
    ledgers = db.relationship('Ledger', back_populates='profile')

    def __repr__(self):
        return f'Profile<{self.name}>'

class RecurringRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), index=True, unique=True, default=generate_uuid)
    amount = db.Column(db.Integer)
    name = db.Column(db.String(64), index=True)
    description = db.Column(db.String(512))
    recurring_dom = db.Column(db.Integer, default=1)
    payment_method = db.Column(db.String(12), default='manual')

    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'))
    profile = db.relationship('Profile', back_populates='recurring')

    def __repr__(self):
        return f'RecurringRecord<{self.name}>'

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    description = db.Column(db.String(512))
    uuid = db.Column(db.String(36), index=True, unique=True, default=generate_uuid)
    amount = db.Column(db.Integer)
    recurring_dom = db.Column(db.Integer, default=1)
    payment_method = db.Column(db.String(12), default='manual')
    paid = db.Column(db.Boolean, default=False)

    ledger_id = db.Column(db.Integer, db.ForeignKey('ledger.id'))
    ledger = db.relationship('Ledger', back_populates='records')

    def __repr__(self):
        return f'Record<{self.name}>'

class Ledger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), index=True, unique=True, default=generate_uuid)
    month = db.Column(db.Date)

    records = db.relationship('Record', back_populates='ledger')
    profile_id = db.Column(db.Integer, db.ForeignKey('profile.id'))
    profile = db.relationship('Profile', back_populates='ledgers')

    def __repr__(self):
        return f'Ledger<{self.month}>'

"""
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), index=True, unique=True, default=generate_uuid)
    amount = db.Column(db.Integer)
    recurring = db.Column(db.Boolean, default=False)
    recurring_dom = db.Column(db.Integer)
    name = db.Column(db.String(64), index=True)
    description = db.Column(db.String(512))
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    end_month = db.Column(db.Date, index=True)
    active = db.Column(db.Boolean, default=True)
    type = db.Column(db.Integer)
    period = db.Column(db.Float)
    month = db.Column(db.Date)

    def __repr__(self):
        return f'Item<{self.name}>'

    def _update_month(self):
        self.month += relativedelta(months=self.period)

class LedgerEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    description = db.Column(db.String(512))
    amount = db.Column(db.Integer)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    item = db.relationship("Item")

    ledger_id = db.Column(db.Integer, db.ForeignKey('ledger.id'))

    def __repr__(self):
        return f'LedgerEntry<ledger: {self.ledger_id}, item: {self.item_id}>'

class Ledger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Date)
    entries = db.relationship('LedgerEntry', backref='ledger', lazy='dynamic')
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))

    def __repr__(self):
        return f'Ledger<{self.month}>'
"""
