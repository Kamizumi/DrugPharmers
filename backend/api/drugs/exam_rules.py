from functools import lru_cache
import re
from django.db import models

NOISE = {"agent", "hormone"}

CLASS_OVERRIDES = {
    "CNS Agent for ADHD" : {"cns agent for adhd", "adhd"}
}

def norm(s):
    return " ".join(s.casefold().split())

def derive_accepted(stored):
    """Given a drug_class string, return the set of answers worth full credit"""
    base = re.sub(r"\s*\([^)]*\)", "", stored)
    parts = re.split(r"\s*/\s*|\s+-\s+", base)
    accepted = {norm(stored), norm(base)}
    for p in parts:
        p = norm(p)
        words = p.split()
        if words and words[-1] in NOISE:
            p = " ".join(words[:-1])
        if p:
            accepted.add(p)
    return accepted - NOISE

@lru_cache(maxsize = None)
def accepted_answers(stored):
    """Public entry point - overrides win, otherwise derive"""
    return CLASS_OVERRIDES.get(stored) or derive_accepted(stored)

class AnswerFormat(models.TextChoices):
    MULTIPLE_CHOICE = "multiple_choice", "Multiple choice"
    FREE_TEXT = "free_text", "Free text"
    BOTH = "both", "Both"

RENDERABLE_FORMATS = [c for c in AnswerFormat.choices if c[0] != AnswerFormat.BOTH]

class QuestionMode(models.TextChoices):
    RECALL = "recall", "Recall"
    IDENTIFY = "identify", "Identify"
    MIXED = "mixed", "Mixed"

class SelectionMode(models.TextChoices):
    RANGED = "ranged", "Ranged"
    RANDOM = "random", "Random"
    MISSED = "missed", "Missed"


ANSWER_FORMATS = {
    "generic_name" : {AnswerFormat.FREE_TEXT, AnswerFormat.MULTIPLE_CHOICE},
    "brand_name" : {AnswerFormat.FREE_TEXT, AnswerFormat.MULTIPLE_CHOICE},
    "drug_class" : {AnswerFormat.FREE_TEXT, AnswerFormat.MULTIPLE_CHOICE},
    "primary_fda_ind" : {AnswerFormat.MULTIPLE_CHOICE},
    "other_fda_ind" : {AnswerFormat.MULTIPLE_CHOICE},
    "avail_strengths" : {AnswerFormat.MULTIPLE_CHOICE},
    "moa" : {AnswerFormat.MULTIPLE_CHOICE},
    "dosing_regimen" : {AnswerFormat.MULTIPLE_CHOICE},
    "side_effects" : {AnswerFormat.MULTIPLE_CHOICE},
    "boxed_warnings" : {AnswerFormat.MULTIPLE_CHOICE}
}