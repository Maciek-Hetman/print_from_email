from rest_framework import serializers
from .models import FileFormat

class FileFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileFormat
        fields = ('file_format', 'enabled')
