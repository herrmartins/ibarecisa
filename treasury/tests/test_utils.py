from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
import random


def get_test_image_file():
    image_io = BytesIO()
    # Generate a random color
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # Create an image with a random color
    image = Image.new("RGB", (100, 100), color=color)

    image.save(image_io, format="JPEG")  # Save the image as JPEG
    image_io.seek(0)  # Rewind the file

    # Generate a random file name to further ensure uniqueness
    file_name = f"test_image_{random.randint(1000, 9999)}.jpg"

    return SimpleUploadedFile(
        name=file_name, content=image_io.getvalue(), content_type="image/jpeg"
    )
