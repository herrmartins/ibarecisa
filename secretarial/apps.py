from django.apps import AppConfig


class SecretarialConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "secretarial"

    def ready(self):
        """Importa signals quando a app estiver pronta."""
        import secretarial.signals  # noqa
