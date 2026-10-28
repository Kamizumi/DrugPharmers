from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Drug, ExamAnswer, ExamAttempt
from .serializers import DrugSerializer, ExamAttemptCreateSerializer, QuestionSerializer, AnswerSubmitSerializer
from .exam_generation import generate_questions
from .exam_rules import SelectionMode, grade

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

class ExamSubmitView(APIView):
    def post(self, request, pk):
        attempt = get_object_or_404(ExamAttempt, pk = pk)
        if attempt.completed_at is not None:
            return Response({"detail": "this exam has already been submitted"}, status = 400)

        s = AnswerSubmitSerializer(data = request.data.get("answers", []), many = True)
        s.is_valid(raise_exception = True)

        rows_by_id = {r.pk: r for r in attempt.answers.select_related("drug")}

        submitted = []

        for item in s.validated_data:
            row = rows_by_id.get(item["id"])
            if row is None:
                return Response({
                    "detail": f"question {item['id']} is not part of this exam"}, status = 400,
            )

            correct = getattr(row.drug, row.answer_field)
            row.user_response = item["user_response"]
            row.was_correct = grade(row.answer_field, row.answer_format, correct, item["user_response"])

            submitted.append(row)

        ExamAnswer.objects.bulk_update(submitted, ["user_response", "was_correct"])
        attempt.completed_at = timezone.now()
        attempt.save(update_fields = ["completed_at"])

        return Response({
            "attempt_id" : attempt.pk,
            "score" : sum(1 for r in submitted if r.was_correct),
            "total" : len(rows_by_id),
        })



