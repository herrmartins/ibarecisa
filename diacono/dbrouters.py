import sys


class AuditRouter:
    """
    A router to control all database operations on models in
    the django-easy-audit app to go to the 'audit_db'.
    """

    def db_for_read(self, model, **hints):
        if model._meta.app_label == "easyaudit" and not self._is_test():
            return "audit_db"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "easyaudit" and not self._is_test():
            return "audit_db"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label == "easyaudit"
            or obj2._meta.app_label == "easyaudit"
            and not self._is_test()
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == "easyaudit":
            return db == "audit_db"
        return None

    def _is_test(self):
        print(f"Current sys.argv: {sys.argv}")  # Debugging statement
        return "test" in sys.argv
