from rest_framework import serializers
from .models import Drug, ExamAttempt
from .exam_rules import QuestionMode, AnswerFormat, SelectionMode
from django.db import models


class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = '__all__'
class ExamAttemptCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExamAttempt
        fields = ["selection_mode", "question_mode", "allowed_formats", "ranking_min", "ranking_max"]

    def validate(self, data):

        lo, hi = data.get("ranking_min"), data.get("ranking_max")

        if lo is not None and hi is not None and lo > hi:
            raise serializers.ValidationError("ranking_min must be <= ranking_max")
        
        highest = Drug.objects.aggregate(models.Max("ranking"))["ranking__max"] or 0
        if hi is not None and hi > highest:
            raise serializers.ValidationError(f"only drugs 1 - {highest} are available")

        if (data.get("question_mode") == QuestionMode.IDENTIFY and data.get("allowed_formats") == AnswerFormat.FREE_TEXT):
            raise serializers.ValidationError("Identify questions are multiple choice only")

        if data.get("selection_mode") != SelectionMode.MISSED and (lo is None or hi is None):
            raise serializers.ValidationError("Ranged and Random exams require ranking_min and ranking_max")
        return data

class QuestionSerializer(serializers.Serializer):
    """Shape of a question; No correct answer and no drug id in this"""
    id = serializers.IntegerField()
    prompt_field = serializers.CharField()
    prompt_value = serializers.CharField()
    answer_field = serializers.CharField()
    answer_format = serializers.CharField()
    choices = serializers.ListField(child = serializers.CharField(), allow_null = True)

class AnswerSubmitSerializer(serializers.Serializer):
    """One submitted answer: Which ExamAnswer row, and what they chose/typed"""
    id = serializers.IntegerField()
    user_response = serializers.CharField(allow_blank = True)
