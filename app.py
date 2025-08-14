import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, send_from_directory, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import generate_csrf
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import mimetypes
from config import config
from models import db, User, File, Folder, FileShare, ActivityLog
from forms import (
    LoginForm, RegistrationForm, UserCreateForm, UserEditForm, FileUploadForm, 
    FolderCreateForm, FileShareForm, SearchForm, SettingsForm, AdminSettingsForm
)

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config['SQLALCHEMY_DATABASE_URI'] = config[config_name].get_database_uri()
    
    # Initialize extensions
    db.init_app(app)
    
    # Create upload folder
    upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_folder, exist_ok=True)
    print(f"DEBUG: Папка загрузок создана/найдена: {upload_folder}")
    print(f"DEBUG: Содержимое папки: {os.listdir(upload_folder) if os.path.exists(upload_folder) else 'папка не существует'}")
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Routes
    @app.route('/')
    @login_required
    def index():
        # Get user's files and folders
        current_folder_id = request.args.get('folder', 0, type=int)
        
        if current_folder_id == 0:
            folders = Folder.query.filter_by(user_id=current_user.id, parent_id=None).all()
            files = File.query.filter_by(user_id=current_user.id, folder_id=None).all()
        else:
            current_folder = Folder.query.get_or_404(current_folder_id)
            if current_folder.user_id != current_user.id:
                abort(403)
            folders = Folder.query.filter_by(user_id=current_user.id, parent_id=current_folder_id).all()
            files = File.query.filter_by(user_id=current_user.id, folder_id=current_folder_id).all()
        
        # Get breadcrumb
        breadcrumb = []
        if current_folder_id != 0:
            folder = Folder.query.get(current_folder_id)
            while folder:
                breadcrumb.insert(0, folder)
                folder = folder.parent
        
        return render_template('index.html', 
                            folders=folders, 
                            files=files, 
                            current_folder_id=current_folder_id,
                            breadcrumb=breadcrumb,
                            csrf_token=generate_csrf())
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Log activity
                log_activity(user.id, 'login', 'user', user.id)
                
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Неверное имя пользователя или пароль', 'error')
        
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        log_activity(current_user.id, 'logout', 'user', current_user.id)
        logout_user()
        return redirect(url_for('login'))
    
    @app.route('/admin/users', methods=['GET', 'POST'])
    @login_required
    def admin_users():
        if not current_user.is_admin:
            abort(403)
        
        form = UserCreateForm()
        if form.validate_on_submit():
            # Get default storage limit from config or use form value
            storage_limit_mb = form.storage_limit.data if form.storage_limit.data else (app.config.get('STORAGE_LIMIT_DEFAULT', 1024 * 1024 * 1024) // (1024 * 1024))
            user = User(
                username=form.username.data,
                email=form.email.data,
                is_admin=form.is_admin.data,
                storage_limit=storage_limit_mb * 1024 * 1024  # Convert MB to bytes
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            log_activity(current_user.id, 'create_user', 'user', user.id)
            flash('Пользователь успешно создан', 'success')
            return redirect(url_for('admin_users'))
        
        users = User.query.all()
        return render_template('admin/users.html', form=form, users=users, csrf_token=generate_csrf())
    
    @app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @login_required
    def admin_edit_user(user_id):
        if not current_user.is_admin:
            abort(403)
        
        user = User.query.get_or_404(user_id)
        
        # Нельзя редактировать самого себя через админку
        if user.id == current_user.id:
            flash('Вы не можете редактировать свой профиль через админку. Используйте страницу настроек.', 'warning')
            return redirect(url_for('admin_users'))
        
        form = UserEditForm(original_username=user.username, original_email=user.email)
        
        if request.method == 'GET':
            form.username.data = user.username
            form.email.data = user.email
            form.is_admin.data = user.is_admin
            form.is_active.data = user.is_active
            form.storage_limit.data = int(user.get_storage_limit_mb())
        
        if form.validate_on_submit():
            # Проверяем, не пытается ли пользователь убрать у себя права администратора
            if user.id == current_user.id and not form.is_admin.data:
                flash('Вы не можете убрать у себя права администратора', 'error')
                return render_template('admin/edit_user.html', form=form, user=user)
            
            user.username = form.username.data
            user.email = form.email.data
            user.is_admin = form.is_admin.data
            user.is_active = form.is_active.data
            
            # Обновляем лимит хранилища
            user.storage_limit = form.storage_limit.data * 1024 * 1024  # Convert MB to bytes
            

            
            db.session.commit()
            
            log_activity(current_user.id, 'edit_user', 'user', user.id)
            flash('Пользователь успешно обновлен', 'success')
            return redirect(url_for('admin_users'))
        
        return render_template('admin/edit_user.html', form=form, user=user)
    
    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    def admin_delete_user(user_id):
        if not current_user.is_admin:
            abort(403)
        
        user = User.query.get_or_404(user_id)
        
        # Нельзя удалить самого себя
        if user.id == current_user.id:
            flash('Вы не можете удалить свой профиль', 'error')
            return redirect(url_for('admin_users'))
        
        # Проверяем, есть ли у пользователя файлы или папки
        if user.files or user.folders:
            flash('Нельзя удалить пользователя, у которого есть файлы или папки. Сначала удалите все ресурсы.', 'error')
            return redirect(url_for('admin_users'))
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        log_activity(current_user.id, 'delete_user', 'user', user_id)
        flash(f'Пользователь "{username}" успешно удален', 'success')
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
    @login_required
    def admin_reset_user_password(user_id):
        if not current_user.is_admin:
            abort(403)
        
        user = User.query.get_or_404(user_id)
        
        # Генерируем новый пароль
        import secrets
        import string
        new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        user.set_password(new_password)
        
        db.session.commit()
        
        log_activity(current_user.id, 'reset_user_password', 'user', user.id)
        flash(f'Пароль для пользователя "{user.username}" сброшен. Новый пароль: {new_password}', 'success')
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
    @login_required
    def admin_toggle_user_status(user_id):
        if not current_user.is_admin:
            abort(403)
        
        user = User.query.get_or_404(user_id)
        
        # Нельзя изменить статус самого себя
        if user.id == current_user.id:
            flash('Вы не можете изменить свой статус', 'error')
            return redirect(url_for('admin_users'))
        
        user.is_active = not user.is_active
        status_text = 'активирован' if user.is_active else 'деактивирован'
        
        db.session.commit()
        
        log_activity(current_user.id, 'toggle_user_status', 'user', user.id)
        flash(f'Пользователь "{user.username}" {status_text}', 'success')
        return redirect(url_for('admin_users'))
    
    @app.route('/admin/users/<int:user_id>/storage')
    @login_required
    def admin_user_storage(user_id):
        if not current_user.is_admin:
            abort(403)
        
        user = User.query.get_or_404(user_id)
        files = File.query.filter_by(user_id=user_id).all()
        folders = Folder.query.filter_by(user_id=user_id).all()
        
        return render_template('admin/user_storage.html', user=user, files=files, folders=folders)
    
    @app.route('/admin/users/<int:user_id>/files')
    @login_required
    def admin_user_files(user_id):
        if not current_user.is_admin:
            abort(403)
        
        user = User.query.get_or_404(user_id)
        files = File.query.filter_by(user_id=user_id).order_by(File.created_at.desc()).all()
        
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        return render_template('admin/user_files.html', user=user, files=files, now=now, week_ago=week_ago)
    
    @app.route('/admin/users/<int:user_id>/export')
    @login_required
    def admin_export_user_data(user_id):
        if not current_user.is_admin:
            abort(403)
        
        user = User.query.get_or_404(user_id)
        
        # TODO: Реализовать экспорт данных пользователя
        flash('Экспорт данных пользователя будет доступен в следующей версии', 'info')
        return redirect(url_for('admin_users'))
    
    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload_file():
        form = FileUploadForm()
        
        # Populate folder choices
        folders = [(0, 'Корневая папка')]
        user_folders = Folder.query.filter_by(user_id=current_user.id).all()
        folders.extend([(f.id, f.name) for f in user_folders])
        form.folder_id.choices = folders
        
        print(f"DEBUG: Форма отправлена, валидна: {form.validate_on_submit()}")
        
        # Проверяем, что папка uploads существует и доступна для записи
        upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
        print(f"DEBUG: Папка загрузок: {upload_folder}")
        print(f"DEBUG: Папка существует: {os.path.exists(upload_folder)}")
        print(f"DEBUG: Папка доступна для записи: {os.access(upload_folder, os.W_OK)}")
        
        # Создаем папку, если она не существует
        if not os.path.exists(upload_folder):
            try:
                os.makedirs(upload_folder, exist_ok=True)
                print(f"DEBUG: Папка {upload_folder} создана")
            except Exception as e:
                print(f"DEBUG: Ошибка создания папки {upload_folder}: {e}")
                flash(f'Ошибка создания папки загрузок: {e}', 'error')
                return render_template('upload.html', form=form)
        
        if form.validate_on_submit():
            files = form.files.data
            print(f"DEBUG: Форма валидна, получено файлов: {len(files) if files else 0}")
            if files:
                print("DEBUG: Файлы получены, начинаю обработку")
                uploaded_count = 0
                failed_count = 0
                total_size = 0
                
                # Проверяем общий размер всех файлов
                for file in files:
                    if hasattr(file, 'content_length') and file.content_length:
                        total_size += file.content_length
                    else:
                        # Если content_length недоступен, читаем файл для определения размера
                        if hasattr(file, 'seek'):
                            file.seek(0, 2)  # Seek to end
                            total_size += file.tell()
                            file.seek(0)  # Reset to beginning
                        else:
                            # Если файл не поддерживает seek, используем len() для bytes
                            if hasattr(file, 'read'):
                                temp_content = file.read()
                                total_size += len(temp_content)
                                # Сбрасываем позицию чтения, если возможно
                                if hasattr(file, 'seek'):
                                    file.seek(0)
                            else:
                                total_size += len(file)
                
                # Проверяем лимит хранилища
                if current_user.storage_used + total_size > current_user.storage_limit:
                    flash('Недостаточно места в хранилище для всех файлов', 'error')
                    return render_template('upload.html', form=form)
                
                # Обрабатываем каждый файл
                for file in files:
                    print(f"DEBUG: Обрабатываю файл: {file.filename if hasattr(file, 'filename') else 'без имени'}")
                    try:
                        # Проверяем, что файл имеет имя
                        if not file.filename:
                            flash('Обнаружен файл без имени', 'error')
                            failed_count += 1
                            continue
                            
                        filename = secure_filename(file.filename)
                        if not filename:
                            flash('Недопустимое имя файла', 'error')
                            failed_count += 1
                            continue
                            
                        unique_filename = f"{uuid.uuid4().hex}_{filename}"
                        # Сохраняем только имя файла в БД, но физически сохраняем в папку uploads
                        file_path = unique_filename
                        full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        
                        # Проверяем размер файла
                        file_content = None
                        if hasattr(file, 'content_length') and file.content_length:
                            file_size = file.content_length
                        else:
                            if hasattr(file, 'seek'):
                                file.seek(0, 2)  # Seek to end
                                file_size = file.tell()
                                file.seek(0)  # Reset to beginning
                            else:
                                # Если файл не поддерживает seek, используем len() для bytes
                                if hasattr(file, 'read'):
                                    file_content = file.read()
                                    file_size = len(file_content)
                                    # Сбрасываем позицию чтения, если возможно
                                    if hasattr(file, 'seek'):
                                        file.seek(0)
                                else:
                                    file_size = len(file)
                        
                        # Добавляем отладочную информацию о размере файла
                        print(f"DEBUG: Размер файла {filename}: {file_size} байт")
                        print(f"DEBUG: Полный путь для сохранения: {full_file_path}")
                        
                        if file_size > app.config['MAX_CONTENT_LENGTH']:
                            flash(f'Файл "{filename}" слишком большой ({file_size / (1024*1024):.1f} МБ)', 'error')
                            failed_count += 1
                            continue
                        
                        # Сохраняем файл в папку uploads
                        print(f"DEBUG: Сохраняю файл по пути: {full_file_path}")
                        if hasattr(file, 'save'):
                            file.save(full_file_path)
                            print(f"DEBUG: Файл сохранен через метод save()")
                        else:
                            # Если у файла нет метода save, записываем содержимое напрямую
                            with open(full_file_path, 'wb') as f:
                                if hasattr(file, 'read'):
                                    # Если мы уже читали файл для определения размера, используем сохраненное содержимое
                                    if file_content is not None:
                                        f.write(file_content)
                                    else:
                                        f.write(file.read())
                                else:
                                    f.write(file)
                            print(f"DEBUG: Файл сохранен через прямой запись")
                        
                        # Проверяем размер сохраненного файла
                        actual_file_size = os.path.getsize(full_file_path)
                        print(f"DEBUG: Фактический размер сохраненного файла {filename}: {actual_file_size} байт")
                        print(f"DEBUG: Файл существует после сохранения: {os.path.exists(full_file_path)}")
                        
                        # Показываем содержимое папки после сохранения
                        try:
                            folder_contents = os.listdir(upload_folder)
                            print(f"DEBUG: Содержимое папки {upload_folder} после сохранения: {folder_contents}")
                        except Exception as e:
                            print(f"DEBUG: Не удалось получить содержимое папки: {e}")
                        
                        # Используем фактический размер файла для базы данных
                        file_size = actual_file_size
                        
                        # Создаем запись в базе данных
                        db_file = File(
                            filename=unique_filename,
                            original_filename=filename,
                            file_path=file_path,  # В БД сохраняем только имя файла
                            file_size=file_size,
                            mime_type=mimetypes.guess_type(filename)[0] or 'application/octet-stream',
                            folder_id=form.folder_id.data if form.folder_id.data != 0 else None,
                            user_id=current_user.id,
                            is_public=form.is_public.data
                        )
                        
                        if form.is_public.data:
                            db_file.public_url = f"{uuid.uuid4().hex}"
                        
                        db.session.add(db_file)
                        uploaded_count += 1
                        
                    except Exception as e:
                        print(f"DEBUG: Ошибка при загрузке файла: {str(e)}")
                        error_msg = f'Ошибка при загрузке файла "{file.filename if hasattr(file, "filename") else "неизвестный"}": {str(e)}'
                        flash(error_msg, 'error')
                        failed_count += 1
                        continue
                
                # Обновляем использованное место в хранилище
                current_user.storage_used += total_size
                db.session.commit()
                
                # Логируем активность для каждого загруженного файла
                # Получаем ID всех загруженных файлов из базы данных
                # Используем более точный способ получения последних загруженных файлов
                uploaded_files = File.query.filter_by(
                    user_id=current_user.id,
                    folder_id=form.folder_id.data if form.folder_id.data != 0 else None
                ).order_by(File.id.desc()).limit(uploaded_count).all()
                
                for db_file in uploaded_files:
                    log_activity(current_user.id, 'upload', 'file', db_file.id)
                
                # Показываем результат
                print(f"DEBUG: Результат загрузки - успешно: {uploaded_count}, неудачно: {failed_count}")
                if uploaded_count > 0:
                    if failed_count == 0:
                        flash(f'Успешно загружено {uploaded_count} файлов', 'success')
                    else:
                        flash(f'Загружено {uploaded_count} файлов, {failed_count} не удалось загрузить', 'warning')
                else:
                    flash('Не удалось загрузить ни одного файла', 'error')
                
                return redirect(url_for('index'))
            else:
                print("DEBUG: Файлы не получены")
                flash('Файлы не были получены', 'error')
                return render_template('upload.html', form=form)
        else:
            print(f"DEBUG: Ошибки валидации формы: {form.errors}")
        
        return render_template('upload.html', form=form)
    
    @app.route('/folder/create', methods=['GET', 'POST'])
    @login_required
    def create_folder():
        form = FolderCreateForm()
        
        # Populate parent folder choices
        folders = [(0, 'Корневая папка')]
        user_folders = Folder.query.filter_by(user_id=current_user.id).all()
        folders.extend([(f.id, f.name) for f in user_folders])
        form.parent_id.choices = folders
        
        if form.validate_on_submit():
            folder = Folder(
                name=form.name.data,
                path=form.name.data,
                parent_id=form.parent_id.data if form.parent_id.data != 0 else None,
                user_id=current_user.id
            )
            
            db.session.add(folder)
            db.session.commit()
            
            log_activity(current_user.id, 'create_folder', 'folder', folder.id)
            flash('Папка успешно создана', 'success')
            return redirect(url_for('index'))
        
        return render_template('create_folder.html', form=form)
    
    @app.route('/folder/<int:folder_id>/delete', methods=['POST'])
    @login_required
    def delete_folder(folder_id):
        print(f"Попытка удаления папки {folder_id} пользователем {current_user.username}")
        
        folder = Folder.query.get_or_404(folder_id)
        print(f"Папка найдена: {folder.name}, путь: {folder.path}")
        
        if folder.user_id != current_user.id:
            print(f"Отказано в доступе: папка принадлежит пользователю {folder.user_id}, текущий пользователь {current_user.id}")
            abort(403)
        
        try:
            # Check if folder has files or subfolders
            files_in_folder = File.query.filter_by(folder_id=folder.id).all()
            subfolders = Folder.query.filter_by(parent_id=folder.id).all()
            
            print(f"Проверка содержимого папки {folder_id}: файлов {len(files_in_folder)}, подпапок {len(subfolders)}")
            
            total_size_to_remove = 0
            deleted_files_count = 0
            deleted_subfolders_count = 0
            
            # Recursively delete subfolders and their contents
            def delete_subfolder_recursive(subfolder_id):
                nonlocal total_size_to_remove, deleted_files_count, deleted_subfolders_count
                
                # Get files in this subfolder
                subfolder_files = File.query.filter_by(folder_id=subfolder_id).all()
                for file in subfolder_files:
                    # Remove file from storage
                    if file.file_path.startswith('uploads\\') or file.file_path.startswith('uploads/'):
                        # Старый формат: file_path уже содержит полный путь
                        full_file_path = file.file_path
                    else:
                        # Новый формат: формируем полный путь
                        full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.file_path)
                    
                    if os.path.exists(full_file_path):
                        os.remove(full_file_path)
                        print(f"Удален файл подпапки: {full_file_path}")
                    total_size_to_remove += file.file_size
                    deleted_files_count += 1
                    # Delete file record
                    db.session.delete(file)
                
                # Get subfolders in this subfolder
                sub_subfolders = Folder.query.filter_by(parent_id=subfolder_id).all()
                for sub_subfolder in sub_subfolders:
                    delete_subfolder_recursive(sub_subfolder.id)
                    db.session.delete(sub_subfolder)
                    deleted_subfolders_count += 1
            
            # Delete subfolders first
            for subfolder in subfolders:
                delete_subfolder_recursive(subfolder.id)
                db.session.delete(subfolder)
                deleted_subfolders_count += 1
            
            # Delete files in the main folder
            for file in files_in_folder:
                # Remove file from storage
                if file.file_path.startswith('uploads\\') or file.file_path.startswith('uploads/'):
                    # Старый формат: file_path уже содержит полный путь
                    full_file_path = file.file_path
                else:
                    # Новый формат: формируем полный путь
                    full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.file_path)
                
                if os.path.exists(full_file_path):
                    os.remove(full_file_path)
                    print(f"Удален файл: {full_file_path}")
                total_size_to_remove += file.file_size
                deleted_files_count += 1
                # Delete file record
                db.session.delete(file)
            
            # Update user storage
            old_storage = current_user.storage_used
            current_user.storage_used -= total_size_to_remove
            print(f"Хранилище пользователя обновлено: {old_storage} -> {current_user.storage_used} байт")
            
            # Delete main folder record
            db.session.delete(folder)
            db.session.commit()
            print(f"Папка {folder_id} и все содержимое успешно удалены из базы данных")
            
            # Log activity
            try:
                log_activity(current_user.id, 'delete_folder', 'folder', folder_id)
                print(f"Активность залогирована для папки {folder_id}")
            except Exception as log_error:
                print(f"Ошибка при логировании активности: {str(log_error)}")
            
            # Формируем сообщение об успешном удалении
            if deleted_files_count > 0 and deleted_subfolders_count > 0:
                flash(f'Папка "{folder.name}" и все содержимое удалены. Удалено файлов: {deleted_files_count}, подпапок: {deleted_subfolders_count}', 'success')
            elif deleted_files_count > 0:
                flash(f'Папка "{folder.name}" и все файлы удалены. Удалено файлов: {deleted_files_count}', 'success')
            elif deleted_subfolders_count > 0:
                flash(f'Папка "{folder.name}" и все подпапки удалены. Удалено подпапок: {deleted_subfolders_count}', 'success')
            else:
                flash(f'Пустая папка "{folder.name}" удалена', 'success')
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при удалении папки {folder_id}: {str(e)}")
            flash(f'Ошибка при удалении папки: {str(e)}', 'error')
        
        return redirect(url_for('index'))
    
    @app.route('/file/<int:file_id>')
    @login_required
    def download_file(file_id):
        file = File.query.get_or_404(file_id)
        
        # Check permissions
        if file.user_id != current_user.id:
            # Check if file is shared with user
            share = FileShare.query.filter_by(
                file_id=file_id, 
                shared_with=current_user.id
            ).first()
            if not share:
                abort(403)
        
        try:
            log_activity(current_user.id, 'download', 'file', file_id)
            
            # Используем send_from_directory для более надежной работы с путями
            directory = os.path.abspath(app.config['UPLOAD_FOLDER'])
            
            # Обрабатываем разные форматы путей в БД
            if file.file_path.startswith('uploads\\') or file.file_path.startswith('uploads/'):
                # Старый формат: убираем 'uploads\' или 'uploads/' из начала
                filename = file.file_path.replace('uploads\\', '').replace('uploads/', '')
            else:
                # Новый формат: file_path содержит только имя файла
                filename = file.file_path
            
            print(f"DEBUG: Директория: {directory}")
            print(f"DEBUG: Исходный file_path в БД: {file.file_path}")
            print(f"DEBUG: Обработанное имя файла: {filename}")
            print(f"DEBUG: Полный путь: {os.path.join(directory, filename)}")
            print(f"DEBUG: Файл существует: {os.path.exists(os.path.join(directory, filename))}")
            
            # Проверяем, что директория существует
            if not os.path.exists(directory):
                print(f"DEBUG: Директория {directory} не существует!")
                flash(f'Папка загрузок не найдена: {directory}', 'error')
                return redirect(url_for('index'))
            
            # Проверяем, что файл существует
            full_path = os.path.join(directory, filename)
            if not os.path.exists(full_path):
                print(f"DEBUG: Файл {full_path} не существует!")
                flash(f'Файл не найден на сервере: {filename}', 'error')
                return redirect(url_for('index'))
            
            # Проверяем, что файл читается
            try:
                with open(full_path, 'rb') as test_file:
                    test_file.read(1)  # Пробуем прочитать 1 байт
                print(f"DEBUG: Файл {full_path} читается успешно")
            except Exception as read_error:
                print(f"DEBUG: Ошибка чтения файла {full_path}: {read_error}")
                flash(f'Файл не может быть прочитан: {filename}', 'error')
                return redirect(url_for('index'))
            
            # Используем send_file с полным путем, так как мы уже проверили существование файла
            print(f"DEBUG: Отправляю файл через send_file: {full_path}")
            return send_file(
                full_path,
                as_attachment=True,
                download_name=file.original_filename,
                mimetype=file.mime_type
            )
        except Exception as e:
            print(f"DEBUG: Ошибка при скачивании: {str(e)}")
            flash(f'Ошибка при скачивании файла: {str(e)}', 'error')
            return redirect(url_for('index'))

    @app.route('/view/<int:file_id>')
    @login_required
    def view_file(file_id):
        """Маршрут для просмотра файлов в браузере"""
        file = File.query.get_or_404(file_id)
        
        # Check permissions
        if file.user_id != current_user.id:
            # Check if file is shared with user
            share = FileShare.query.filter_by(
                file_id=file_id, 
                shared_with=current_user.id
            ).first()
            if not share:
                abort(403)
        
        try:
            log_activity(current_user.id, 'view', 'file', file_id)
            
            directory = os.path.abspath(app.config['UPLOAD_FOLDER'])
            
            # Обрабатываем разные форматы путей в БД
            if file.file_path.startswith('uploads\\') or file.file_path.startswith('uploads/'):
                filename = file.file_path.replace('uploads\\', '').replace('uploads/', '')
            else:
                filename = file.file_path
            
            full_path = os.path.join(directory, filename)
            
            if not os.path.exists(full_path):
                abort(404)
            
            # Проверяем, что файл читается
            try:
                with open(full_path, 'rb') as test_file:
                    test_file.read(1)
            except Exception:
                abort(404)
            
            # Отправляем файл для просмотра (без скачивания)
            return send_file(
                full_path,
                as_attachment=False,  # Важно: False для просмотра
                mimetype=file.mime_type
            )
        except Exception as e:
            print(f"DEBUG: Ошибка при просмотре файла: {str(e)}")
            abort(404)
    
    @app.route('/file/<int:file_id>/delete', methods=['POST'])
    @login_required
    def delete_file(file_id):
        print(f"Попытка удаления файла {file_id} пользователем {current_user.username}")
        
        file = File.query.get_or_404(file_id)
        print(f"Файл найден: {file.original_filename}, путь: {file.file_path}")
        
        if file.user_id != current_user.id:
            print(f"Отказано в доступе: файл принадлежит пользователю {file.user_id}, текущий пользователь {current_user.id}")
            abort(403)
        
        try:
            # Remove file from storage
            if file.file_path.startswith('uploads\\') or file.file_path.startswith('uploads/'):
                # Старый формат: file_path уже содержит полный путь
                full_file_path = file.file_path
            else:
                # Новый формат: формируем полный путь
                full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.file_path)
            
            if os.path.exists(full_file_path):
                os.remove(full_file_path)
                print(f"Файл удален физически: {full_file_path}")
            else:
                print(f"Файл не найден физически: {full_file_path}")
            
            # Update user storage
            old_storage = current_user.storage_used
            current_user.storage_used -= file.file_size
            print(f"Хранилище пользователя обновлено: {old_storage} -> {current_user.storage_used} байт")
            
            # Delete file record
            db.session.delete(file)
            db.session.commit()
            print(f"Файл {file_id} успешно удален из базы данных")
            
            # Log activity
            try:
                log_activity(current_user.id, 'delete', 'file', file_id)
                print(f"Активность залогирована для файла {file_id}")
            except Exception as log_error:
                print(f"Ошибка при логировании активности: {str(log_error)}")
            
            flash('Файл удален', 'success')
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при удалении файла {file_id}: {str(e)}")
            flash(f'Ошибка при удалении файла: {str(e)}', 'error')
        
        return redirect(url_for('index'))
    
    @app.route('/search', methods=['GET', 'POST'])
    @login_required
    def search():
        form = SearchForm()
        results = []
        
        if form.validate_on_submit():
            query = form.query.data.lower()
            search_type = form.search_type.data
            
            if search_type in ['all', 'files']:
                files = File.query.filter(
                    File.user_id == current_user.id,
                    File.original_filename.ilike(f'%{query}%')
                ).all()
                results.extend([('file', f) for f in files])
            
            if search_type in ['all', 'folders']:
                folders = Folder.query.filter(
                    Folder.user_id == current_user.id,
                    Folder.name.ilike(f'%{query}%')
                ).all()
                results.extend([('folder', f) for f in folders])
        
        return render_template('search.html', form=form, results=results)
    
    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        form = SettingsForm()
        
        if form.validate_on_submit():
            if current_user.check_password(form.current_password.data):
                if form.new_password.data:
                    current_user.set_password(form.new_password.data)
                current_user.email = form.email.data
                db.session.commit()
                
                log_activity(current_user.id, 'update_settings', 'user', current_user.id)
                flash('Настройки обновлены', 'success')
                return redirect(url_for('settings'))
            else:
                flash('Неверный текущий пароль', 'error')
        
        elif request.method == 'GET':
            form.email.data = current_user.email
        
        return render_template('settings.html', form=form)
    
    @app.route('/admin/settings', methods=['GET', 'POST'])
    @login_required
    def admin_settings():
        if not current_user.is_admin:
            abort(403)
        
        form = AdminSettingsForm()
        
        if form.validate_on_submit():
            # Update configuration
            app.config['DATABASE_TYPE'] = form.database_type.data
            app.config['MAX_CONTENT_LENGTH'] = form.max_file_size.data * 1024 * 1024
            app.config['STORAGE_LIMIT_DEFAULT'] = form.storage_limit_default.data * 1024 * 1024
            
            # Save to .env file
            env_file = '.env'
            env_content = f"""# Flask Configuration
SECRET_KEY={app.config['SECRET_KEY']}
DATABASE_TYPE={form.database_type.data}
MAX_CONTENT_LENGTH={form.max_file_size.data * 1024 * 1024}
STORAGE_LIMIT_DEFAULT={form.storage_limit_default.data * 1024 * 1024}
UPLOAD_FOLDER={app.config['UPLOAD_FOLDER']}
DEBUG={app.config['DEBUG']}
"""
            
            try:
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.write(env_content)
                flash('Настройки обновлены и сохранены в файл .env', 'success')
            except Exception as e:
                flash(f'Настройки обновлены, но не удалось сохранить в файл: {str(e)}', 'warning')
            
            return redirect(url_for('admin_settings'))
        
        elif request.method == 'GET':
            form.database_type.data = app.config.get('DATABASE_TYPE', 'sqlite')
            form.max_file_size.data = app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)
            form.storage_limit_default.data = app.config.get('STORAGE_LIMIT_DEFAULT', 1024 * 1024 * 1024) // (1024 * 1024)
        
        return render_template('admin/settings.html', form=form, config=app.config)
    
    @app.route('/public/<public_url>')
    def public_file(public_url):
        file = File.query.filter_by(public_url=public_url, is_public=True).first_or_404()
        
        # Обрабатываем разные форматы путей в БД
        if file.file_path.startswith('uploads\\') or file.file_path.startswith('uploads/'):
            # Старый формат: убираем 'uploads\' или 'uploads/' из начала
            filename = file.file_path.replace('uploads\\', '').replace('uploads/', '')
        else:
            # Новый формат: file_path содержит только имя файла
            filename = file.file_path
        
        return send_from_directory(
            os.path.abspath(app.config['UPLOAD_FOLDER']),
            filename,
            as_attachment=True, 
            download_name=file.original_filename
        )
    
    @app.route('/folder/<int:folder_id>/move', methods=['POST'])
    @login_required
    def move_folder(folder_id):
        folder = Folder.query.get_or_404(folder_id)
        if folder.user_id != current_user.id:
            abort(403)
        
        target_folder_id = request.form.get('target_folder_id', type=int)
        
        # Проверяем, что целевая папка существует и принадлежит пользователю
        if target_folder_id != 0:
            target_folder = Folder.query.get_or_404(target_folder_id)
            if target_folder.user_id != current_user.id:
                abort(403)
            
            # Проверяем, что не пытаемся переместить папку в саму себя или в её подпапку
            if target_folder_id == folder_id:
                flash('Нельзя переместить папку в саму себя', 'error')
                return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
            
            # Проверяем, что целевая папка не является подпапкой текущей
            current = target_folder
            while current.parent_id:
                if current.parent_id == folder_id:
                    flash('Нельзя переместить папку в её подпапку', 'error')
                    return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
                current = current.parent
        
        # Перемещаем папку
        old_parent_id = folder.parent_id
        folder.parent_id = target_folder_id if target_folder_id != 0 else None
        db.session.commit()
        
        log_activity(current_user.id, 'move_folder', 'folder', folder.id)
        flash('Папка успешно перемещена', 'success')
        
        return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
    
    @app.route('/file/<int:file_id>/move', methods=['POST'])
    @login_required
    def move_file(file_id):
        file = File.query.get_or_404(file_id)
        if file.user_id != current_user.id:
            abort(403)
        
        target_folder_id = request.form.get('target_folder_id', type=int)
        
        # Проверяем, что целевая папка существует и принадлежит пользователю
        if target_folder_id != 0:
            target_folder = Folder.query.get_or_404(target_folder_id)
            if target_folder.user_id != current_user.id:
                abort(403)
        
        # Перемещаем файл
        old_folder_id = file.folder_id
        file.folder_id = target_folder_id if target_folder_id != 0 else None
        db.session.commit()
        
        log_activity(current_user.id, 'move_file', 'file', file.id)
        flash('Файл успешно перемещен', 'success')
        
        return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
    
    @app.route('/file/<int:file_id>/toggle_public', methods=['POST'])
    @login_required
    def toggle_file_public(file_id):
        file = File.query.get_or_404(file_id)
        if file.user_id != current_user.id:
            abort(403)
        
        try:
            if file.is_public:
                # Делаем файл приватным
                file.is_public = False
                file.public_url = None
                action = 'make_private'
                flash('Файл стал приватным', 'success')
            else:
                # Делаем файл публичным
                file.is_public = True
                file.public_url = f"{uuid.uuid4().hex}"
                action = 'make_public'
                flash('Файл стал публичным', 'success')
            
            db.session.commit()
            log_activity(current_user.id, action, 'file', file_id)
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при изменении статуса файла: {str(e)}', 'error')
        
        return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
    
    @app.route('/folder/<int:folder_id>/rename', methods=['POST'])
    @login_required
    def rename_folder(folder_id):
        folder = Folder.query.get_or_404(folder_id)
        if folder.user_id != current_user.id:
            abort(403)
        
        new_name = request.form.get('new_name', '').strip()
        if not new_name:
            flash('Название папки не может быть пустым', 'error')
            return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
        
        # Проверяем, что папка с таким именем не существует в той же директории
        parent_id = folder.parent_id
        existing_folder = Folder.query.filter_by(
            user_id=current_user.id,
            parent_id=parent_id,
            name=new_name
        ).first()
        
        if existing_folder and existing_folder.id != folder.id:
            flash('Папка с таким именем уже существует', 'error')
            return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
        
        try:
            old_name = folder.name
            folder.name = new_name
            folder.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_activity(current_user.id, 'rename_folder', 'folder', folder_id)
            flash(f'Папка "{old_name}" переименована в "{new_name}"', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при переименовании папки: {str(e)}', 'error')
        
        return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
    
    @app.route('/file/<int:file_id>/rename', methods=['POST'])
    @login_required
    def rename_file(file_id):
        file = File.query.get_or_404(file_id)
        if file.user_id != current_user.id:
            abort(403)
        
        new_name = request.form.get('new_name', '').strip()
        if not new_name:
            flash('Название файла не может быть пустым', 'error')
            return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
        
        # Проверяем расширение файла
        old_ext = os.path.splitext(file.original_filename)[1]
        new_ext = os.path.splitext(new_name)[1]
        
        if old_ext != new_ext:
            flash('Нельзя изменять расширение файла', 'error')
            return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
        
        # Проверяем, что файл с таким именем не существует в той же папке
        folder_id = file.folder_id
        existing_file = File.query.filter_by(
            user_id=current_user.id,
            folder_id=folder_id,
            original_filename=new_name
        ).first()
        
        if existing_file and existing_file.id != file.id:
            flash('Файл с таким именем уже существует в этой папке', 'error')
            return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
        
        try:
            old_name = file.original_filename
            file.original_filename = new_name
            file.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_activity(current_user.id, 'rename_file', 'file', file_id)
            flash(f'Файл "{old_name}" переименован в "{new_name}"', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при переименовании файла: {str(e)}', 'error')
        
        return redirect(url_for('index', folder=request.args.get('folder', 0, type=int)))
    
    @app.route('/api/folder/<int:folder_id>/contents')
    @login_required
    def get_folder_contents(folder_id):
        """API endpoint для получения информации о содержимом папки"""
        folder = Folder.query.get_or_404(folder_id)
        
        # Проверяем права доступа
        if folder.user_id != current_user.id:
            abort(403)
        
        try:
            # Подсчитываем файлы в папке
            files_count = File.query.filter_by(folder_id=folder.id).count()
            
            # Подсчитываем подпапки в папке
            subfolders_count = Folder.query.filter_by(parent_id=folder.id).count()
            
            return jsonify({
                'success': True,
                'folder_id': folder_id,
                'folder_name': folder.name,
                'files_count': files_count,
                'subfolders_count': subfolders_count,
                'total_items': files_count + subfolders_count
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def log_activity(user_id, action, resource_type, resource_id):
        """Log user activity"""
        log = ActivityLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(log)
        db.session.commit()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create admin user if none exists
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True,
                storage_limit=10 * 1024 * 1024 * 1024  # 10GB
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: username=admin, password=admin123")
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting server on port {port}")
    print(f"Database type: {app.config['DATABASE_TYPE']}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
