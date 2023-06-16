from django.shortcuts import render
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from .seralizers import PrinterSerializer
from .models import Printer
from urllib.parse import quote

class PrinterViewSet(viewsets.ModelViewSet):
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer
    lookup_field = 'printer_key'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class PrinterCreateView(generics.CreateAPIView):
    serializer_class = PrinterSerializer
    queryset = Printer.objects.all()

class PrinterDeleteView(generics.DestroyAPIView):
    serializer_class = PrinterSerializer
    queryset = Printer.objects.all()

class PrinterUpdateView(generics.UpdateAPIView):
    serializer_class = PrinterSerializer
    queryset = Printer.objects.all()
