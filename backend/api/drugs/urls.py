from django.urls import path
from .views import DrugView, DrugDetailView

urlpatterns = [
    path("drugs/", DrugView.as_view()),
    path("drugs/<int:pk>/", DrugDetailView.as_view())
]