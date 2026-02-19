from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    document_status = db.Column(db.String(50), default='접수완료')
    call_status = db.Column(db.String(20), default='대기')
    assigned_agent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submissions = db.relationship('Submission', backref='customer', lazy=True)
    assigned_agent = db.relationship('User', backref='assigned_customers')


class Script(db.Model):
    __tablename__ = 'scripts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default='기본 해피콜 스크립트')
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recording_file = db.Column(db.String(200))
    check_installment = db.Column(db.Boolean, default=True)
    check_penalty = db.Column(db.Boolean, default=True)
    check_rate_plan = db.Column(db.Boolean, default=True)
    check_retention = db.Column(db.Boolean, default=True)
    check_monthly_fee = db.Column(db.Boolean, default=True)
    check_used_phone = db.Column(db.Boolean, default=True)
    check_store_complaint = db.Column(db.Boolean, default=True)
    memo_check_installment = db.Column(db.String(500), default='')
    memo_check_penalty = db.Column(db.String(500), default='')
    memo_check_rate_plan = db.Column(db.String(500), default='')
    memo_check_retention = db.Column(db.String(500), default='')
    memo_check_monthly_fee = db.Column(db.String(500), default='')
    memo_check_used_phone = db.Column(db.String(500), default='')
    store_complaint_memo = db.Column(db.String(500), default='')
    agent_opinion = db.Column(db.String(500), default='')
    raw_customer_data = db.Column(db.Text, default='')
    final_status = db.Column(db.String(20), default='정상')
    admin_status = db.Column(db.String(20), default='대기중')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    agent = db.relationship('User', backref='submissions')
