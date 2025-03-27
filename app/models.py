# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255))
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(64))
    first_name = db.Column(db.String(64), nullable=False)
    middle_name = db.Column(db.String(64))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def full_name(self):
        if self.last_name:
            return f"{self.last_name} {self.first_name} {self.middle_name or ''}"
        return f"{self.first_name} {self.middle_name or ''}"
    
    # Проверка роли
    def is_admin(self):
        return self.role and self.role.name == 'Admin'

    def __repr__(self):
        return f'<User {self.username}>'

# Новая модель для логирования посещений
class VisitLog(db.Model):
    __tablename__ = 'visit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Может быть NULL для неаутентифицированных
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True) # Индекс для сортировки

    def __repr__(self):
        return f'<VisitLog {self.path} by User ID:{self.user_id} at {self.created_at}>'