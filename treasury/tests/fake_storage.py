from django.core.files.storage import Storage
from io import BytesIO


class InMemoryStorage(Storage):
    def __init__(self):
        self.files = {}

    def _open(self, name, mode="rb"):
        if name in self.files:
            return BytesIO(self.files[name])
        else:
            return BytesIO()

    def _save(self, name, content):
        content.open()
        self.files[name] = content.read()
        content.close()
        return name

    def delete(self, name):
        del self.files[name]

    def exists(self, name):
        return name in self.files

    def listdir(self, path):
        return [], list(self.files.keys())

    def url(self, name):
        return f"http://example.com/{name}"

    def size(self, name):
        return len(self.files[name])
