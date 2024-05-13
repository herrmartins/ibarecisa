import uuid
import os
import mimetypes


def custom_upload_to(instance, filename):
    file_mime_type, _ = mimetypes.guess_type(filename)

    base_name, ext = os.path.splitext(filename)

    new_filename = f"{uuid.uuid4()}{ext.lower()}"

    new_file_path = os.path.join('treasury/receipts', new_filename)

    return new_file_path
