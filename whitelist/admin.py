from django.contrib import admin
from .models import Email

class EmailAdmin(admin.ModelAdmin):
    list_display = ('email',)

admin.site.register(Email, EmailAdmin)
