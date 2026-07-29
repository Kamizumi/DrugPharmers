from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import Drug
from .serializers import DrugSerializer

class DrugView(ListAPIView):
    queryset = Drug.objects.all()
    serializer_class = DrugSerializer


class DrugDetailView(RetrieveAPIView):
    queryset = Drug.objects.all()
    serializer_class = DrugSerializer
