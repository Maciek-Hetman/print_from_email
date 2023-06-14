from rest_framework import viewsets
from .serializers import FileFormatSerializer
from .models import FileFormat

class FileFormatView(viewsets.ModelViewSet):
    serializer_class = FileFormatSerializer
    queryset = FileFormat.objects.all()
