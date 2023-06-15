from django.shortcuts import render
from rest_framework import viewsets, generics
from .seralizers import PrinterSerializer
from .models import Printer

class PrinterView(viewsets.ModelViewSet):
    serializer_class = PrinterSerializer
    queryset = Printer.objects.all()

class PrinterCreateView(generics.CreateAPIView):
    serializer_class = PrinterSerializer
    queryset = Printer.objects.all()

class PrinterDeleteView(generics.DestroyAPIView):
    serializer_class = PrinterSerializer
    queryset = Printer.objects.all()

class PrinterUpdateView(generics.UpdateAPIView):
    serializer_class = PrinterSerializer
    queryset = Printer.objects.all()
