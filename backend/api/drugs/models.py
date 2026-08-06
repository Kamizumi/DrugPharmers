from django.db import models
from django.conf import settings
from .exam_rules import AnswerFormat, SelectionMode, QuestionMode, RENDERABLE_FORMATS


class Drug(models.Model):
    ranking = models.PositiveSmallIntegerField(unique = True)
    generic_name = models.CharField(max_length = 200)
    brand_name = models.CharField(max_length = 200)
    drug_class = models.CharField(max_length = 200)
    primary_fda_ind = models.TextField()
    other_fda_ind = models.TextField(blank = True, default = "")
    avail_strengths = models.TextField()
    moa = models.TextField()
    dosing_regimen = models.TextField()
    side_effects = models.TextField()
    boxed_warnings = models.TextField(blank = True, default = "")
    class Meta:
        ordering = ["ranking"]

    def __str__(self):
        return f"(Brand: {self.brand_name}, Generic: {self.generic_name}, Classification: {self.drug_class}, Primary FDA: {self.primary_fda_ind})"

class ExamAttempt(models.Model):
    """User starts an exam; that is this session"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null = True, blank = True, on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add = True)
    ranking_min = models.PositiveSmallIntegerField(null = True, blank = True)
    ranking_max = models.PositiveSmallIntegerField(null = True, blank = True)
    selection_mode = models.CharField(max_length = 20, choices = SelectionMode.choices, default = SelectionMode.RANGED)
    question_mode = models.CharField(max_length = 20, choices = QuestionMode.choices, default = QuestionMode.RECALL)
    allowed_formats = models.CharField(max_length = 20, choices = AnswerFormat.choices, default = AnswerFormat.MULTIPLE_CHOICE)

class ExamAnswer(models.Model):
    """A  single question generated on the exam
    
    Drug is paired with prompt_field/answer_field to define the question
    The question is then displayed in the answer_format and the user's response
    """
    attempt = models.ForeignKey(ExamAttempt, related_name = "answers", on_delete = models.CASCADE)
    drug = models.ForeignKey(Drug, on_delete = models.CASCADE)
    prompt_field = models.CharField(max_length = 50)
    answer_field = models.CharField(max_length = 50)
    answer_format = models.CharField(max_length = 20, choices = RENDERABLE_FORMATS)
    user_response = models.TextField(blank = True, default = "")
    was_correct = models.BooleanField()

    
