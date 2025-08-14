from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    storage_used = db.Column(db.BigInteger, default=0)  # bytes
    storage_limit = db.Column(db.BigInteger, default=1073741824)  # 1GB default
    
    # Relationships
    files = db.relationship('File', backref='owner', lazy=True)
    folders = db.relationship('Folder', backref='owner', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_storage_usage_mb(self):
        return round(self.storage_used / (1024 * 1024), 2)
    
    def get_storage_limit_mb(self):
        return round(self.storage_limit / (1024 * 1024), 2)
    
    def get_storage_percentage(self):
        if self.storage_limit == 0:
            return 0
        return round((self.storage_used / self.storage_limit) * 100, 2)

class Folder(db.Model):
    __tablename__ = 'folders'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(1000), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subfolders = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]))
    files = db.relationship('File', backref='folder', lazy=True)
    
    def get_full_path(self):
        if self.parent:
            return os.path.join(self.parent.get_full_path(), self.name)
        return self.name

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(1000), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)  # bytes
    mime_type = db.Column(db.String(100), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    public_url = db.Column(db.String(255), unique=True, nullable=True)
    
    def get_file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    def get_file_size_formatted(self):
        """Return file size in human readable format"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{round(self.file_size / 1024, 2)} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{round(self.file_size / (1024 * 1024), 2)} MB"
        else:
            return f"{round(self.file_size / (1024 * 1024 * 1024), 2)} GB"

class FileShare(db.Model):
    __tablename__ = 'file_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    shared_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shared_with = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission = db.Column(db.String(20), default='read')  # read, write, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    file = db.relationship('File', backref='shares')
    shared_by_user = db.relationship('User', foreign_keys=[shared_by])
    shared_with_user = db.relationship('User', foreign_keys=[shared_with])

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # upload, download, delete, share, etc.
    resource_type = db.Column(db.String(50), nullable=False)  # file, folder, user
    resource_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='activity_logs')
