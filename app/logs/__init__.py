# app/logs/__init__.py
from flask import Blueprint

# Создаем Blueprint 'logs'
# template_folder='templates' указывает, что шаблоны для этого блюпринта 
# будут искаться в папке templates ВНУТРИ папки logs (т.е. app/logs/templates)
logs_bp = Blueprint('logs', __name__, template_folder='templates')

# Импортируем маршруты после создания Blueprint, чтобы избежать циклических импортов
from . import routes 