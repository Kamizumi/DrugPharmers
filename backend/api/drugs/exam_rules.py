from functools import lru_cache
import re

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

ANSWER_FORMATS = {
    "generic_name" : {"free_text", "multiple_choice"},
    "brand_name" : {"free_text", "multiple_choice"},
    "drug_class" : {"free_text", "multiple_choice"},
    "primary_fda_ind" : {"multiple_choice"},
    "other_fda_ind" : {"multiple_choice"},
    "avail_strengths" : {"multiple_choice"},
    "moa" : {"multiple_choice"},
    "dosing_regimen" : {"multiple_choice"},
    "side_effects" : {"multiple_choice"},
    "boxed_warnings" : {"multiple_choice"}
}

@lru_cache(maxsize = None)
def accepted_answers(stored):
    """Public entry point - overrides win, otherwise derive"""
    return CLASS_OVERRIDES.get(stored) or derive_accepted(stored)