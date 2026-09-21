from functools import lru_cache
import re
from django.db import models
import random
from collections import defaultdict

#Answers that don't really give credit because they're too vague
NOISE = {"agent", "hormone"}

#For fill in the blank so that users don't have to get exact match
CLASS_OVERRIDES = {
    "CNS Agent for ADHD" : {"cns agent for adhd", "adhd"}
}

#Questions will TYPICALLY start with either the generic name or brand name when asking about its details
NAME_FIELDS = {"generic_name", "brand_name"}

IDENTIFY_PROMPT_FIELDS = {"drug_class", "primary_fda_ind", "moa", "boxed_warnings"}

SALT_FORMS = {"calcium", "sodium", "hydrochloride" , "hcl", "potassium", "besylate",
              "succinate", "tartrate", "bitartrate", "mesylate", "phosphate", "hyclate",
              "oxalate", "medoxomil", "trihydrate", "monohydrate", "dihydrate", "sulfate",
              "bromide", "fumarate", "maleate", "citrate", "acetate", "propionate", 
              "xinafoate", "pamoate", "ferrous"}

BRAND_SUFFIXES = {"hfa", "cr", "xr", "er", "sr", "xl", "odt", "cd", "ir", "la"}

SALT_REQUIRED_MANUAL = set()


def strip_salt(stored):
    """Returns (stripped,full). Equal to when there are no salts to strip"""
    base = re.sub(r"\s*\([^)]*\)", "", stored)
    words = norm(base).replace(",", " ").split()
    full = " ".join(words)
    while words and words[-1] in SALT_FORMS:
        words.pop()

    return " ".join(words), full

@lru_cache(maxsize = 1)
def salt_required():
    """Base names carried by 2+ salt forms """
    from .models import Drug
    bases = defaultdict(set)
    for name in Drug.objects.values_list("generic_name", flat = True):
        stripped, full = strip_salt(name)
        if stripped and stripped != full:
            bases[stripped].add(full)

    return {b for b, forms in bases.items() if len(forms) > 1} | SALT_REQUIRED_MANUAL

def derive_generic_answers(stored):
    base = re.sub(r"\s*\([^)]*\)", "", stored)
    accepted = {norm(stored), norm(base)}
    stripped, full = strip_salt(stored)
    if stripped and stripped not in salt_required():
        accepted.add(stripped)

    no_salts = " ".join(w for w in norm(base).replace(",", " ").split()
                        if w not in SALT_FORMS)
    if no_salts and no_salts not in salt_required():
        accepted.add(no_salts)

    return {a for a in accepted if a} 

def derive_brand_answers(stored):
    base = re.sub(r"\s*\([^)]*\)", "", stored)
    base = base.replace("®", "").replace("™", "").replace("„¢", "")
    accepted= {norm(stored)}
    for part in re.split(r"\s*[,&]\s*", base):
        p = norm(part)
        if not p:
            continue
        accepted.add(p)
        words = p.split()
        while words and words[-1] in BRAND_SUFFIXES:
            words.pop()
        if words:
            accepted.add(" ".join(words))
    return {a for a in accepted if a}
#Normalizes the drug classification so that users are able to guess it easier
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

FREE_TEXT_GRADERS = {
        "drug_class" : lambda s: CLASS_OVERRIDES.get(s) or derive_accepted(s),
        "generic_name" : derive_generic_answers,
        "brand_name" : derive_brand_answers,
    }
    
@lru_cache(maxsize = None)
def accepted_answers(field, stored):
    """Public entry point - overrides win, otherwise derive"""
    return FREE_TEXT_GRADERS[field](stored)

class AnswerFormat(models.TextChoices):
    """Types of questions that a user can select when creating an exam"""
    MULTIPLE_CHOICE = "multiple_choice", "Multiple choice"
    FREE_TEXT = "free_text", "Free text"
    BOTH = "both", "Both"

RENDERABLE_FORMATS = [c for c in AnswerFormat.choices if c[0] != AnswerFormat.BOTH]

class QuestionMode(models.TextChoices):
    """Types of exam modes that a user can select when creating an exam """
    RECALL = "recall", "Recall"
    IDENTIFY = "identify", "Identify"
    MIXED = "mixed", "Mixed"

class SelectionMode(models.TextChoices):
    """"""
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