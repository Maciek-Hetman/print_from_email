from django.db import models

class FileFormat(models.Model):
    file_format = models.TextField(max_length=8, unique=True)
    enabled = models.BooleanField(default=True)

    def _str_(self):
        return self.file_format
