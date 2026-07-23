from rest_framework.generics import ListAPIView
from .models import Drug
from .serializers import DrugSerializer

class DrugView(ListAPIView):
    queryset = Drug.objects.all()
    serializer_class = DrugSerializer
