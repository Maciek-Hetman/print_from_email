from django.db import models

class Printer(models.Model):
    printer_key = models.TextField(max_length=100, unique=True)
    enabled = models.BooleanField(default=False)

    def _str_(self):
        return self.printer_key
