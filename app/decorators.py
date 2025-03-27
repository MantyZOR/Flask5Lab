# app/decorators.py
from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user

def check_rights(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Проверка аутентификации (хотя обычно @login_required идет первым)
            if not current_user.is_authenticated:
                flash('Пожалуйста, войдите в систему для доступа к этой странице.', 'warning')
                return redirect(url_for('views.login', next=request.url))

            # 2. Проверка роли
            user_role = current_user.role.name if current_user.role else None

            # Админ имеет доступ ко всему, что требует роли 'Admin' или 'User'
            if user_role == 'Admin':
                return func(*args, **kwargs)
            
            # Если требуется роль 'Admin', а у пользователя ее нет
            if required_role == 'Admin' and user_role != 'Admin':
                flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
                return redirect(url_for('views.index'))

            # Если требуется роль 'User', а пользователь 'User' (или 'Admin', уже проверено выше)
            if required_role == 'User' and user_role in ['User', 'Admin']:
                 # Дополнительные проверки для конкретных действий (например, редактирование себя)
                 # могут быть внутри view function, т.к. декоратору сложнее получить контекст (id и т.д.)
                return func(*args, **kwargs)

            # Во всех остальных случаях (например, нет роли или роль не подходит)
            flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
            return redirect(url_for('views.index'))
        return wrapper
    return decorator