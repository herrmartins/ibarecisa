from django.utils import timezone


def user_profile_image_path(instance, filename):
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")

    extension = filename.split(".")[-1]

    new_filename = f"user_{instance.id}_{timestamp}.{extension}"

    return f"img/profile/{new_filename}"
