from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField, MultipleFileField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from models import User

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован.')

class UserCreateForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    is_admin = BooleanField('Администратор')
    storage_limit = IntegerField('Лимит хранилища (МБ)', validators=[DataRequired(), NumberRange(min=1, max=100000)])
    submit = SubmitField('Создать пользователя')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован.')

class UserEditForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    is_admin = BooleanField('Администратор')
    is_active = BooleanField('Активен')
    storage_limit = IntegerField('Лимит хранилища (МБ)', validators=[DataRequired(), NumberRange(min=1, max=100000)])
    submit = SubmitField('Сохранить изменения')
    
    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Это имя пользователя уже занято.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Этот email уже зарегистрирован.')

class FileUploadForm(FlaskForm):
    files = MultipleFileField('Выберите файлы', validators=[DataRequired()])
    folder_id = SelectField('Папка', coerce=int, choices=[(0, 'Корневая папка')])
    is_public = BooleanField('Публичный доступ')
    submit = SubmitField('Загрузить')

class FolderCreateForm(FlaskForm):
    name = StringField('Название папки', validators=[DataRequired(), Length(min=1, max=255)])
    parent_id = SelectField('Родительская папка', coerce=int, choices=[(0, 'Корневая папка')])
    submit = SubmitField('Создать папку')

class FileShareForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    permission = SelectField('Разрешения', choices=[
        ('read', 'Только чтение'),
        ('write', 'Чтение и запись'),
        ('admin', 'Полный доступ')
    ])
    expires_at = StringField('Истекает (YYYY-MM-DD)', validators=[])
    submit = SubmitField('Поделиться')

class SearchForm(FlaskForm):
    query = StringField('Поиск', validators=[DataRequired()])
    search_type = SelectField('Тип', choices=[
        ('all', 'Все'),
        ('files', 'Файлы'),
        ('folders', 'Папки')
    ])
    submit = SubmitField('Найти')

class SettingsForm(FlaskForm):
    current_password = PasswordField('Текущий пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[Length(min=6)])
    new_password2 = PasswordField('Подтвердите новый пароль', validators=[EqualTo('new_password')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Сохранить изменения')

class AdminSettingsForm(FlaskForm):
    database_type = SelectField('Тип базы данных', choices=[
        ('sqlite', 'SQLite'),
        ('mysql', 'MySQL'),
        ('postgresql', 'PostgreSQL'),
        ('mariadb', 'MariaDB')
    ])
    max_file_size = IntegerField('Максимальный размер файла (МБ)', validators=[DataRequired(), NumberRange(min=1, max=100000)])
    storage_limit_default = IntegerField('Лимит хранилища по умолчанию (МБ)', validators=[DataRequired(), NumberRange(min=1, max=100000)])
    submit = SubmitField('Сохранить настройки')
