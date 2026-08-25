import random
from .models import Drug
from .exam_rules import ANSWER_FORMATS, NAME_FIELDS, AnswerFormat, QuestionMode, IDENTIFY_PROMPT_FIELDS

def build_question(drug, question_mode, allowed_formats, prompt_field = None, answer_field = None):
    """Returns a question dict for this drug, including the correct answer"""
    if question_mode == QuestionMode.IDENTIFY:
        prompt_candidates = [f for f in IDENTIFY_PROMPT_FIELDS if getattr(drug, f)]
        if prompt_field is None:
            prompt_field = random.choice(sorted(prompt_candidates))
        if answer_field is None:
            answer_field = random.choice(sorted(NAME_FIELDS))
        answer_format = AnswerFormat.MULTIPLE_CHOICE
        candidates = Drug.objects.exclude(**{prompt_field: getattr(drug, prompt_field)})
        disqualified = {getattr(d, answer_field) for d in Drug.objects.filter(**{prompt_field: getattr(drug, prompt_field)})}
    else:
        if prompt_field is None:
            prompt_field = random.choice(sorted(NAME_FIELDS))
        answer_candidates = [f for f in ANSWER_FORMATS if f != prompt_field and getattr(drug, f)]
        if answer_field is None:
            answer_field = random.choice(answer_candidates)
        answer_format = AnswerFormat.MULTIPLE_CHOICE
        if answer_field == "drug_class":
            candidates = Drug.objects.exclude(drug_class = drug.drug_class)
        else:
            candidates = Drug.objects.filter(drug_class = drug.drug_class).exclude(pk = drug.pk)
        disqualified = {getattr(drug, answer_field)}

    correct = getattr(drug, answer_field)

    #Unpacks the argument into something like 'category = "antibiotics"' and then excludes it
    pool = {getattr(d, answer_field) for d in candidates if getattr(d, answer_field)} - disqualified

    #Pool is a union of answers that were generated (excluding the correct answer) so they're wrong and the correct answer
    if len(pool) < 3:
        pool |= {getattr(d, answer_field) for d in Drug.objects.exclude(pk = drug.pk) if getattr(d, answer_field)} - disqualified

    choices = random.sample(sorted(pool), 3 ) + [correct]
    random.shuffle(choices)

    assert len(choices) == 4
    assert choices.count(correct) == 1

    return {
        "drug_id" : drug.pk,
        "prompt_field" : prompt_field,
        "prompt_value" : getattr(drug, prompt_field),
        "answer_field" : answer_field,
        "answer_format" : answer_format,
        "correct_answer" : correct,
        "choices" : choices

    }

def generate_questions(drugs, question_mode, allowed_formats):
    """A drug queryset filtered from the ranking range"""
    return [build_question(d, question_mode, allowed_formats) for d in drugs]