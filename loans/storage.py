import mimetypes
import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.text import get_valid_filename


def upload_document(upload, user_id, application_id):
    safe_name = get_valid_filename(os.path.basename(upload.name))
    path = f'{user_id}/{application_id}/{uuid.uuid4().hex}_{safe_name}'
    content_type = upload.content_type or mimetypes.guess_type(upload.name)[0] or 'application/octet-stream'
    stored_path = default_storage.save(path, upload)
    return stored_path, content_type