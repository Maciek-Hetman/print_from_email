from django.contrib import admin
from .models import FileFormat

class FileFormatAdmin(admin.ModelAdmin):
    list_display = ('file_format', 'enabled')

admin.site.register(FileFormat, FileFormatAdmin)
