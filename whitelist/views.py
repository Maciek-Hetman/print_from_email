from django.shortcuts import render
from rest_framework import viewsets
from .serializers import EmailSerializer
from .models import Email


# Create your views here.
class EmailView(viewsets.ModelViewSet):
    serializer_class = EmailSerializer
    queryset = Email.objects.all()
