# app/logs/routes.py
from flask import render_template, request, abort, Response, stream_with_context
from flask_login import current_user, login_required
from sqlalchemy import func, desc
from . import logs_bp # Импорт Blueprint из текущего пакета (__init__.py)
from ..models import db, VisitLog, User # Импорт моделей из родительского пакета
from ..decorators import check_rights # Импорт декоратора
import csv
import io
from datetime import datetime

# Константа для количества записей на странице
LOGS_PER_PAGE = 15

# 1. Главная страница журнала посещений (с пагинацией)
@logs_bp.route('/')
@login_required
# @check_rights('User') # Доступен всем залогиненным, но фильтрация ниже
def visit_log_index():
    page = request.args.get('page', 1, type=int)
    query = VisitLog.query.order_by(VisitLog.created_at.desc())

    # Фильтрация для роли 'User': видит только свои логи
    if not current_user.is_admin():
        query = query.filter(VisitLog.user_id == current_user.id)

    # Выполняем запрос с пагинацией
    pagination = query.paginate(page=page, per_page=LOGS_PER_PAGE, error_out=False)
    logs = pagination.items

    # Получаем пользователей для отображения имен (оптимизируем запрос)
    user_ids = {log.user_id for log in logs if log.user_id}
    users = User.query.filter(User.id.in_(user_ids)).all()
    users_map = {user.id: user for user in users}

    return render_template('logs/visit_log_index.html', 
                           logs=logs, 
                           users_map=users_map, 
                           pagination=pagination,
                           is_admin=current_user.is_admin()) # Передаем флаг админа

# 2. Отчет по страницам
@logs_bp.route('/pages')
@login_required
@check_rights('Admin') # Только админ может смотреть статистику
def page_stats():
    stats = db.session.query(
        VisitLog.path,
        func.count(VisitLog.id).label('visit_count')
    ).group_by(VisitLog.path)\
     .order_by(desc('visit_count'))\
     .all()
    
    return render_template('logs/page_stats.html', stats=stats)

# 3. Экспорт отчета по страницам в CSV
@logs_bp.route('/pages/export')
@login_required
@check_rights('Admin')
def export_page_stats_csv():
    stats = db.session.query(
        VisitLog.path,
        func.count(VisitLog.id).label('visit_count')
    ).group_by(VisitLog.path)\
     .order_by(desc('visit_count'))\
     .all()

    # Используем stream_with_context для генерации больших файлов без хранения в памяти
    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        
        # Заголовок CSV
        writer.writerow(['Страница', 'Количество посещений'])
        yield data.getvalue() # Отправляем заголовок
        data.seek(0)
        data.truncate(0)
        
        # Строки данных
        for i, record in enumerate(stats):
            writer.writerow([record.path, record.visit_count])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(stream_with_context(generate()), mimetype='text/csv')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response.headers['Content-Disposition'] = f'attachment; filename=page_stats_{timestamp}.csv'
    return response

# 4. Отчет по пользователям
@logs_bp.route('/users')
@login_required
@check_rights('Admin')
def user_stats():
    stats = db.session.query(
        VisitLog.user_id,
        User.last_name,
        User.first_name,
        User.middle_name,
        User.username, # На случай если ФИО нет
        func.count(VisitLog.id).label('visit_count')
    ).outerjoin(User, VisitLog.user_id == User.id)\
     .group_by(VisitLog.user_id, User.last_name, User.first_name, User.middle_name, User.username)\
     .order_by(desc('visit_count'))\
     .all()

    # Формируем данные для шаблона, обрабатывая неаутентифицированных пользователей
    processed_stats = []
    for record in stats:
        if record.user_id is None:
            user_name = "Неаутентифицированный пользователь"
        else:
             parts = [record.last_name, record.first_name, record.middle_name]
             user_name = " ".join(filter(None, parts)) or record.username # Используем username если ФИО пустое
        processed_stats.append({
            'user_name': user_name,
            'visit_count': record.visit_count,
            'user_id': record.user_id # Может понадобиться для ссылки на профиль
        })

    return render_template('logs/user_stats.html', stats=processed_stats)

# 5. Экспорт отчета по пользователям в CSV
@logs_bp.route('/users/export')
@login_required
@check_rights('Admin')
def export_user_stats_csv():
    stats = db.session.query(
        VisitLog.user_id,
        User.last_name,
        User.first_name,
        User.middle_name,
        User.username, 
        func.count(VisitLog.id).label('visit_count')
    ).outerjoin(User, VisitLog.user_id == User.id)\
     .group_by(VisitLog.user_id, User.last_name, User.first_name, User.middle_name, User.username)\
     .order_by(desc('visit_count'))\
     .all()

    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        
        writer.writerow(['Пользователь', 'Количество посещений'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        
        for record in stats:
            if record.user_id is None:
                user_name = "Неаутентифицированный пользователь"
            else:
                 parts = [record.last_name, record.first_name, record.middle_name]
                 user_name = " ".join(filter(None, parts)) or record.username
            writer.writerow([user_name, record.visit_count])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(stream_with_context(generate()), mimetype='text/csv')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response.headers['Content-Disposition'] = f'attachment; filename=user_stats_{timestamp}.csv'
    return response