from rest_framework import serializers
from .models import Drug


class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = '__all__'



class ExamQuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Drug
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        allowed = set(kwargs.pop("allowed_fields"))
        super().__init__(*args, **kwargs)
        for name in set(self.fields) - allowed:
            self.fields.pop(name)