"""
Database router para direcionar models de auditoria para banco separado.

Models de auditoria ficam em banco SQLite separado (audit.sqlite3)
para isolamento e segurança dos dados.
"""


class AuditRouter:
    """
    Direciona models de auditoria para o banco separado 'audit'.

    Models que devem ir para o banco de auditoria:
    - PeriodSnapshot
    - AuditLog
    - Outros models de auditoria/histórico
    """

    # Models que vão para o banco de auditoria (model_name em lowercase)
    # NOTA: PeriodSnapshot não usa mais ForeignKey (apenas IDs), então pode
    # ficar no banco de auditoria
    audit_models = {
        'periodsnapshot',
        'auditlog',
    }

    # Apps que devem ter migrations no banco de auditoria
    # (necessário para contenttypes, auth, etc.)
    audit_apps = {'treasury', 'contenttypes', 'auth'}

    def db_for_read(self, model, **hints):
        """
        Direciona leitura de models de auditoria para o banco 'audit'.
        """
        if model._meta.model_name in self.audit_models:
            return 'audit'
        return None

    def db_for_write(self, model, **hints):
        """
        Direciona escrita de models de auditoria para o banco 'audit'.
        """
        if model._meta.model_name in self.audit_models:
            return 'audit'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Bloqueia relações entre bancos diferentes.

        SQLite/Django não suporta FKs cross-db, então retornamos None
        para deixar o Django decidir (bloqueia automaticamente).
        """
        # Verifica se os objetos estão em bancos diferentes
        db1 = self.db_for_write(obj1.__class__)
        db2 = self.db_for_write(obj2.__class__)

        if db1 and db2 and db1 != db2:
            return False  # Bloqueia relação cross-db

        return None  # Deixa o Django decidir para outros casos

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Controla quais migrations vão para cada banco.

        - Banco 'audit': apenas treasury (models de auditoria), contenttypes, auth
        - Banco 'default': tudo exceto models de auditoria
        """
        # Para hints de model
        if hints.get('model'):
            model_name_lower = hints['model']._meta.model_name.lower()
            if model_name_lower in self.audit_models:
                return db == 'audit'
            if db == 'audit':
                return False

        # Para model_name direto
        if model_name:
            model_name_lower = model_name.lower()
            if model_name_lower in self.audit_models:
                return db == 'audit'

        # Controle por app_label
        if db == 'audit':
            # Apenas apps específicos podem ter migrations no banco audit
            return app_label in self.audit_apps

        # Para banco default, apps de audit não podem ter suas migrations aqui
        if app_label in self.audit_apps and model_name:
            model_name_lower = model_name.lower()
            if model_name_lower in self.audit_models:
                return False

        return None  # Deixa o Django decidir para outros casos
