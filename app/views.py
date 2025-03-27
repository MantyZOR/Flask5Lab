# views.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from .models import db, User, Role, VisitLog 
from .forms import LoginForm, UserForm, EditUserForm, ChangePasswordForm
from .decorators import check_rights

views = Blueprint('views', __name__)

@views.route('/')
# @login_required # Главная страница доступна всем, но список будет пуст без входа
def index():
    # Показываем всех пользователей только админу
    users = []
    if current_user.is_authenticated and current_user.is_admin():
        users = User.query.order_by(User.last_name, User.first_name).all()
    elif current_user.is_authenticated:
        # Обычный пользователь видит только себя в списке (или пустой список)
        users = User.query.filter_by(id=current_user.id).all()
        
    return render_template('index.html', users=users)

@views.route('/login', methods=['GET', 'POST'])
def login():
    
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # Сначала проверяем, что пользователь найден
        if user is None:
            flash('Пользователь с таким логином не найден.', 'warning')
        # Затем проверяем пароль
        elif not user.verify_password(form.password.data):
            flash('Неверный пароль.', 'warning')
        # Если все ОК
        else:
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('views.index')
            flash(f'Добро пожаловать, {user.full_name()}!', 'success')
            return redirect(next_page)
            
    return render_template('login.html', form=form)


@views.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('views.login')) # Перенаправляем на страницу входа

# Просмотр профиля: Админ видит всех, Пользователь только себя
@views.route('/user/<int:id>')
@login_required
# @check_rights('User') # Проверку сделаем внутри для гибкости
def user_view(id):
    user = User.query.get_or_404(id)
    # Админ может смотреть любой профиль
    if current_user.is_admin():
        return render_template('user_view.html', user=user)
    # Пользователь может смотреть только свой профиль
    elif current_user.id == user.id:
        return render_template('user_view.html', user=user)
    else:
        flash('У вас недостаточно прав для просмотра этого профиля.', 'danger')
        return redirect(url_for('views.index'))

# Создание пользователя: Только Админ
@views.route('/user/create', methods=['GET', 'POST'])
@login_required
@check_rights('Admin') # Только Admin может создавать пользователей
def user_create():
    form = UserForm()
    # Динамически заполняем роли в форме перед валидацией
    form.role.choices = [(0, 'Не выбрано')] + [(r.id, r.name) for r in Role.query.order_by('name').all()]

    if form.validate_on_submit():
        # ... (код создания пользователя без изменений) ...
        # Проверяем, что выбрана роль
        role_id = form.role.data
        selected_role = Role.query.get(role_id) if role_id != 0 else None
        if not selected_role:
             flash('Необходимо выбрать роль для пользователя.', 'warning')
             # Передаем текущие данные обратно в форму
             return render_template('user_create.html', form=form)

        if User.query.filter_by(username=form.username.data).first():
            flash('Пользователь с таким логином уже существует', 'warning')
            return render_template('user_create.html', form=form)
            
        user = User(
            username=form.username.data,
            last_name=form.last_name.data,
            first_name=form.first_name.data,
            middle_name=form.middle_name.data,
            role=selected_role # Присваиваем объект роли
        )
        user.password = form.password.data # Хеширование через сеттер
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Пользователь успешно создан.', 'success')
            return redirect(url_for('views.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании пользователя: {str(e)}', 'danger')

    # Если GET запрос или форма невалидна
    return render_template('user_create.html', form=form)


# Редактирование пользователя: Админ редактирует всех, Пользователь только себя (без роли)
@views.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
# @check_rights('User') # Проверку сделаем внутри
def user_edit(id):
    user_to_edit = User.query.get_or_404(id)
    
    # Проверка прав: Админ может редактировать всех, Пользователь только себя
    if not current_user.is_admin() and current_user.id != user_to_edit.id:
        flash('У вас недостаточно прав для редактирования этого пользователя.', 'danger')
        return redirect(url_for('views.index'))

    form = EditUserForm(obj=user_to_edit) # Заполняем форму данными пользователя
     # Динамически заполняем роли, даже если поле будет отключено
    form.role.choices = [(0, 'Не выбрано')] + [(r.id, r.name) for r in Role.query.order_by('name').all()]

    # Отключаем поле роли для обычного пользователя
    is_editing_self_as_user = not current_user.is_admin() and current_user.id == user_to_edit.id
    if is_editing_self_as_user:
        form.role.render_kw = {'disabled': 'disabled'}

    if form.validate_on_submit():
        # Обновляем поля из формы
        user_to_edit.last_name = form.last_name.data
        user_to_edit.first_name = form.first_name.data
        user_to_edit.middle_name = form.middle_name.data
        
        # Роль обновляем только если редактирует Админ
        if current_user.is_admin():
             role_id = form.role.data
             selected_role = Role.query.get(role_id) if role_id != 0 else None
             if not selected_role and role_id != 0: # Если выбрано что-то кроме "Не выбрано", но роль не найдена
                 flash('Выбрана неверная роль.', 'danger')
                 # Важно вернуть шаблон с текущими данными формы
                 return render_template('user_edit.html', form=form, user=user_to_edit, is_editing_self_as_user=is_editing_self_as_user)
             user_to_edit.role = selected_role
        # Если редактирует обычный пользователь, роль не меняется (поле отключено)

        try:
            db.session.commit()
            flash('Данные пользователя успешно обновлены.', 'success')
            return redirect(url_for('views.user_view', id=user_to_edit.id)) # Возврат к просмотру профиля
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении пользователя: {str(e)}', 'danger')
            
    elif request.method == 'GET':
        # При GET запросе устанавливаем текущую роль пользователя в форму
        # obj=user_to_edit в конструкторе уже должен был это сделать, но для надежности:
        form.role.data = user_to_edit.role_id or 0
        
    # Передаем флаг в шаблон, чтобы можно было скрыть/показать информацию о роли
    return render_template('user_edit.html', form=form, user=user_to_edit, is_editing_self_as_user=is_editing_self_as_user)


# Удаление пользователя: Только Админ (и не может удалить себя)
@views.route('/user/delete/<int:id>', methods=['POST'])
@login_required
@check_rights('Admin') # Только Admin может удалять
def user_delete(id):
    user_to_delete = User.query.get_or_404(id)
    
    # Запрещаем админу удалять самого себя
    if user_to_delete.id == current_user.id:
        flash('Вы не можете удалить свою учетную запись.', 'danger')
        return redirect(url_for('views.index'))
        
    try:
        # Перед удалением пользователя, возможно, нужно обработать связанные логи
        # Например, установить user_id в NULL в visit_logs
        VisitLog.query.filter_by(user_id=user_to_delete.id).update({'user_id': None})
        # Теперь можно удалять пользователя
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Пользователь "{user_to_delete.full_name()}" успешно удален.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении пользователя: {str(e)}', 'danger')
    
    return redirect(url_for('views.index'))

# Изменение пароля: Любой залогиненный пользователь для себя
@views.route('/change-password', methods=['GET', 'POST'])
@login_required # Достаточно @login_required, так как пользователь меняет свой пароль
def change_password():
    # ... (код без изменений) ...
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.verify_password(form.old_password.data):
            flash('Старый пароль введен неверно.', 'warning')
        elif form.new_password.data == form.old_password.data:
             flash('Новый пароль не должен совпадать со старым.', 'warning')
        else:
            current_user.password = form.new_password.data # Используем сеттер
            try:
                db.session.commit()
                flash('Пароль успешно изменен.', 'success')
                # После смены пароля хорошо бы перенаправить на страницу профиля или главную
                return redirect(url_for('views.user_view', id=current_user.id)) 
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при изменении пароля: {str(e)}', 'danger')

    return render_template('change_password.html', form=form)