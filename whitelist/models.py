from django.db import models

class Email(models.Model):
    email = models.EmailField(max_length=254, unique=True)

    def _str_(self):
        return self.email 
