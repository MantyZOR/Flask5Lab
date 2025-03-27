# _init_.py
from flask import Flask, request, flash, redirect, url_for
from flask_login import LoginManager, current_user
# Добавляем импорты для логирования
from datetime import datetime
# Убедитесь, что импортированы ВСЕ модели
from .models import db, User, Role, VisitLog
from .config import Config
import os

login_manager = LoginManager()
login_manager.login_view = 'views.login'
# Сообщение при попытке доступа к защищенной странице без входа
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'warning' # Категория для flash сообщения

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Функция для логирования посещений
def log_visit():
    # Исключаем логирование запросов к статическим файлам и favicon
    if request.endpoint and ('static' not in request.endpoint) and request.path != '/favicon.ico':
        user_id = current_user.id if current_user.is_authenticated else None
        # Ограничим длину path, чтобы избежать ошибок БД
        path = request.path[:255] 
        visit = VisitLog(path=path, user_id=user_id)
        try:
            db.session.add(visit)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error logging visit: {e}") # Логгирование ошибки в консоль сервера

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login_manager.init_app(app)
    
    # Регистрация обработчика before_request для логирования
    app.before_request(log_visit)

    # Регистрация представлений основного модуля
    from .views import views as views_blueprint
    app.register_blueprint(views_blueprint)
    
    # Регистрация нового Blueprint'а для логов
    from .logs import logs_bp as logs_blueprint
    app.register_blueprint(logs_blueprint, url_prefix='/logs') # Добавляем префикс /logs

    # Создание таблиц в базе данных и начальные данные
    with app.app_context():
        # Проверяем существование файла БД перед созданием таблиц
        # Это важно для платформ вроде Render с эфемерной ФС
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.exists(db_path):
             print(f"Database file not found at {db_path}. Creating tables...")
             db.create_all()
             print("Tables created.")
        else:
             # Если файл есть, можно все равно вызвать create_all - она безопасна
             # но можно и пропустить для скорости
             db.create_all() # Гарантирует создание новых таблиц, если их нет
             print("Checked database schema.")


        # Создание ролей, если их нет
        if not Role.query.first():
            print("Creating default roles...")
            roles = [
                {'name': 'Admin', 'description': 'Administrator with full access'},
                {'name': 'User', 'description': 'Regular user with limited access'}
            ]
            for role_data in roles:
                role = Role(**role_data)
                db.session.add(role)
            db.session.commit()
            print("Default roles created.")
            
        # Создание первого пользователя-администратора, если НЕТ ВООБЩЕ пользователей
        if not User.query.first():
             print("Creating default admin user...")
             admin_role = Role.query.filter_by(name='Admin').first()
             if admin_role: # Убедимся, что роль Admin создана
                 admin_user = User(
                     username='admin',
                     first_name='Администратор',
                     last_name='Системы',
                     role=admin_role # Присваиваем роль
                 )
                 admin_user.password = 'Admin123!' # Используется сеттер для хеширования
                 db.session.add(admin_user)
                 db.session.commit()
                 print('--- Default Admin User Created ---')
                 print('Login: admin')
                 print('Password: Admin123!')
                 print('----------------------------------')
             else:
                 print("ERROR: Could not find 'Admin' role to create admin user.")
    
    return app