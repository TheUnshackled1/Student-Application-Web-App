"""
Custom database storage backend for storing uploaded files in PostgreSQL.
Files are stored as binary data in the DBFile model.
"""

import hashlib
import mimetypes
from io import BytesIO

from django.core.files.base import ContentFile, File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    """
    A Django storage backend that stores files in the database.
    """

    def _open(self, name, mode='rb'):
        from home.models import DBFile
        try:
            db_file = DBFile.objects.get(name=name)
            return ContentFile(db_file.data, name=name)
        except DBFile.DoesNotExist:
            raise FileNotFoundError(f"File not found: {name}")

    def _save(self, name, content):
        from home.models import DBFile

        # Read data
        if hasattr(content, 'read'):
            data = content.read()
        else:
            data = content

        # Guess content type
        content_type, _ = mimetypes.guess_type(name)
        content_type = content_type or 'application/octet-stream'

        # Create or update
        db_file, created = DBFile.objects.update_or_create(
            name=name,
            defaults={
                'data': data,
                'content_type': content_type,
                'size': len(data),
            }
        )

        return name

    def delete(self, name):
        from home.models import DBFile
        DBFile.objects.filter(name=name).delete()

    def exists(self, name):
        from home.models import DBFile
        return DBFile.objects.filter(name=name).exists()

    def listdir(self, path):
        from home.models import DBFile
        files = DBFile.objects.filter(name__startswith=path).values_list('name', flat=True)
        return [], list(files)

    def size(self, name):
        from home.models import DBFile
        try:
            return DBFile.objects.get(name=name).size
        except DBFile.DoesNotExist:
            return 0

    def url(self, name):
        from django.urls import reverse
        return reverse('serve_db_file', kwargs={'file_path': name})

    def get_accessed_time(self, name):
        from home.models import DBFile
        db_file = DBFile.objects.get(name=name)
        return db_file.updated_at

    def get_created_time(self, name):
        from home.models import DBFile
        db_file = DBFile.objects.get(name=name)
        return db_file.created_at

    def get_modified_time(self, name):
        from home.models import DBFile
        db_file = DBFile.objects.get(name=name)
        return db_file.updated_at
