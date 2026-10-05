from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Drug, ExamAnswer
from .serializers import DrugSerializer, ExamAttemptCreateSerializer, QuestionSerializer
from .exam_generation import generate_questions
from .exam_rules import SelectionMode

class DrugView(ListAPIView):
    queryset = Drug.objects.all()
    serializer_class = DrugSerializer


class DrugDetailView(RetrieveAPIView):
    queryset = Drug.objects.all()
    serializer_class = DrugSerializer

class ExamCreateView(APIView):
    def post(self, request):
        s = ExamAttemptCreateSerializer(data = request.data)
        s.is_valid(raise_exception= True)
        attempt = s.save()

        drugs = self.get_drugs(attempt)
        questions = generate_questions(drugs, attempt.question_mode, attempt.allowed_formats)

        rows = ExamAnswer.objects.bulk_create([
            ExamAnswer(
                attempt = attempt,
                drug_id = q["drug_id"],
                prompt_field = q["prompt_field"],
                answer_field = q["answer_field"],
                answer_format = q["answer_format"],
            ) 
            for q in questions
        ])
        for q, row in zip(questions, rows):
            q["id"] = row.pk

        return Response(
            {"attempt_id": attempt.pk,
             "questions" : QuestionSerializer(questions, many = True).data},
             status = 201
        )

    def get_drugs(self, attempt):
        """Which drug this exam covers"""
        if attempt.selection_mode == SelectionMode.MISSED:
            raise NotImplementedError

        qs = Drug.objects.filter(ranking__gte = attempt.ranking_min,
                                 ranking__lte = attempt.ranking_max)
        if attempt.selection_mode == SelectionMode.RANDOM:
            qs = qs.order_by("?")

        return qs


