# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError, EqualTo
from .models import User, Role

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=5)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class UserForm(FlaskForm):
    username = StringField('Логин', validators=[
        DataRequired(), 
        Length(min=5),
        Regexp('^[A-Za-z0-9]+$', message='Логин должен состоять только из латинских букв и цифр')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=8, max=128),
        Regexp(r'^(?=.*[a-zа-я])(?=.*[A-ZА-Я])(?=.*\d)(?!.*\s)[\w~!?@#$%^&*_\-+(){}\[\]><\\/|"\'.,;:]+$',
              message='Пароль должен содержать как минимум одну заглавную букву, одну строчную букву, одну цифру и не содержать пробелов')
    ])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    middle_name = StringField('Отчество')
    role = SelectField('Роль', coerce=int)
    submit = SubmitField('Сохранить')
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.role.choices = [(0, 'Не выбрано')] + [(role.id, role.name) for role in Role.query.all()]

class EditUserForm(FlaskForm):
    last_name = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    middle_name = StringField('Отчество')
    role = SelectField('Роль', coerce=int)
    submit = SubmitField('Сохранить')
    
    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.role.choices = [(0, 'Не выбрано')] + [(role.id, role.name) for role in Role.query.all()]

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Старый пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[
        DataRequired(),
        Length(min=8, max=128),
        Regexp(r'^(?=.*[a-zа-я])(?=.*[A-ZА-Я])(?=.*\d)(?!.*\s)[\w~!?@#$%^&*_\-+(){}\[\]><\\/|"\'.,;:]+$',
              message='Пароль должен содержать как минимум одну заглавную букву, одну строчную букву, одну цифру и не содержать пробелов')
    ])
    confirm_password = PasswordField('Повторите новый пароль', validators=[
        DataRequired(),
        EqualTo('new_password', message='Пароли не совпадают')
    ])
    submit = SubmitField('Изменить пароль')
