from django.contrib import admin
from .models import Printer

class PrinterAdmin(admin.ModelAdmin):
    list_display = ('printer_key', 'enabled')

admin.site.register(Printer, PrinterAdmin)
