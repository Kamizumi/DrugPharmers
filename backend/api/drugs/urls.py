from django.urls import path
from .views import DrugView, DrugDetailView, ExamCreateView, ExamSubmitView

urlpatterns = [
    path("drugs/", DrugView.as_view()),
    path("drugs/<int:pk>/", DrugDetailView.as_view()),
    path("exams/", ExamCreateView.as_view()),
    path("exams/<int:pk>/submit/", ExamSubmitView.as_view())

]