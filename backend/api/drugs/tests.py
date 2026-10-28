from rest_framework.test import APITestCase
from django.test import TestCase
from django.core.management import call_command
from .models import Drug, ExamAttempt, ExamAnswer
from .exam_generation import build_question
from .exam_rules import QuestionMode, AnswerFormat, ANSWER_FORMATS, NAME_FIELDS, IDENTIFY_PROMPT_FIELDS, salt_required, accepted_answers, norm, grade



# Create your tests here.

REQUIRED_FIELDS = {
                    "generic_name", "brand_name", "drug_class",
                    "primary_fda_ind", "avail_strengths", "moa", "dosing_regimen",
                    "side_effects"
                }

EXPECTED_FIELDS = {
                    "id", "ranking", "generic_name", "brand_name", "drug_class",
                    "primary_fda_ind", "other_fda_ind", "avail_strengths", "moa",
                    "dosing_regimen", "side_effects", "boxed_warnings"
                }

class TestAPIs(APITestCase):

    def setUp(self):
        self.full_drug = Drug.objects.create(
                                        ranking = 1,
                                        generic_name = "A",
                                        brand_name = "A Train",
                                        drug_class = "Drug Type A",
                                        primary_fda_ind = "Used to treat farts",
                                        other_fda_ind = "Also treats hiccups",
                                        avail_strengths = "5mg, 10mg, 15mg",
                                        moa = "Absorption in the stomach",
                                        dosing_regimen = "5 poq",
                                        side_effects = "Burps",
                                        boxed_warnings = "may cause sudden napping"
                                        )
        
        self.min_drug = Drug.objects.create(
                                        ranking = 2,
                                        generic_name = 'B',
                                        brand_name = "BoomerTown",
                                        drug_class = "Antipsychotic",
                                        primary_fda_ind = "Helps remedy schizophrenia",
                                        avail_strengths = ".25 mcg",
                                        moa = "stomach",
                                        dosing_regimen = "1poq",
                                        side_effects = "love"
                                        )
    
    def test_list_returns_200(self):
        '''
        Test to check if the API is properly returning the endpoint
        '''

        response = self.client.get("/api/drugs/")
        self.assertEqual(response.status_code, 200)

    
    def test_every_drug_has_the_same_fields(self):
        '''
        Test to make sure that every drug has the same set fields
        '''
    
        response = self.client.get("/api/drugs/")
        for drug in response.data:
            self.assertEqual(set(drug.keys()), EXPECTED_FIELDS)


    def test_round_trip_data(self):
        '''
        Test to ensure that the data from step 1 is equal to the value in step 5
        Python -> DB -> ORM - > Serializer -> Json
        Object creation -> SQLite storage -> Drugs.objects.all() reads it -> DrugSerializer converts it -> response.data["brand_name"]
        '''

        response = self.client.get("/api/drugs/")
        full_drug = response.data[0]
        self.assertEqual(full_drug["brand_name"], "A Train")

    def test_required_fields_are_populated(self):
        '''
        Test to ensure that the drug objects all have the required fields populated
        These are mandatory to have and must be populated
        '''

        response = self.client.get("/api/drugs/")
        for drug in response.data:
            for field in REQUIRED_FIELDS:
                with self.subTest(drug = drug["brand_name"], field = field):
                    self.assertTrue(drug[field])

    def test_optional_fields_default_to_empty_string(self):
        '''
        Test to ensure that optional fields (like other_fda_ind or black box warning)
        are defaulted to empty strings if they aren't populated
        '''

        response = self.client.get("/api/drugs/")
        minimal = response.data[1]
        self.assertEqual(minimal["other_fda_ind"], "")
        self.assertEqual(minimal["boxed_warnings"], "")

    def test_individual_drug_returns_200_and_correct_drug(self):
        '''A valid pk that returns that specific drug'''
        response = self.client.get(f"/api/drugs/{self.full_drug.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["brand_name"], "A Train")

    def test_detail_returns_404_for_invalid__drug(self):
        '''An id that doesn't exist returns 404, not an empty 200'''
        response = self.client.get("/api/drugs/99999/")
        self.assertEqual(response.status_code, 404)

    def test_individual_drug_has_same_fields_as_list(self):
        '''Individual drug view and list drug view have identical fields'''
        response = self.client.get(f"/api/drugs/{self.full_drug.pk}/")
        self.assertEqual(set(response.data.keys()), EXPECTED_FIELDS)


    


class TestQuestionGeneration(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("seed_drugs", verbosity = 0)

    def test_drug_class_answers_have_no_duplicate(self):
        """The failure mode: same-class distractors all yield the same class string."""
        drug = Drug.objects.get(generic_name="Atorvastatin Calcium")   # class has 8 members
        q = build_question(drug, QuestionMode.RECALL, AnswerFormat.MULTIPLE_CHOICE,
                        answer_field="drug_class")
        self.assertEqual(q["choices"].count(q["correct_answer"]), 1)

    def test_choices_are_well_formed(self):
        for drug in Drug.objects.all():
            for answer_field in ANSWER_FORMATS:
                if answer_field in NAME_FIELDS or not getattr(drug, answer_field):
                    continue
                with self.subTest(drug=drug.brand_name, field=answer_field):
                    q = build_question(drug, QuestionMode.RECALL, AnswerFormat.MULTIPLE_CHOICE,
                                    prompt_field="brand_name", answer_field=answer_field)
                    self.assertEqual(len(q["choices"]), 4)
                    self.assertEqual(len(set(q["choices"])), 4)
                    self.assertEqual(q["choices"].count(q["correct_answer"]), 1)
                    self.assertNotIn("", q["choices"])

    def test_identify_distractors_never_share_prompt(self):
        '''Ensure generated answers are not the prompt'''
        for drug in Drug.objects.all():
            for prompt_field in IDENTIFY_PROMPT_FIELDS:
                if not getattr(drug, prompt_field):
                    continue
                with self.subTest(drug = drug.brand_name, prompt = prompt_field):
                    q = build_question(drug, QuestionMode.IDENTIFY, AnswerFormat.MULTIPLE_CHOICE,
                                       prompt_field = prompt_field, answer_field = "generic_name")
                    self.assertEqual(len(set(q["choices"])), 4)
                    self.assertEqual(q["choices"].count(q["correct_answer"]), 1)

                    for choice in q["choices"]:
                        if choice == q["correct_answer"]:
                            continue
                        self.assertFalse(
                            Drug.objects.filter(
                                generic_name = choice,
                                **{prompt_field: q["prompt_value"]}
                            ).exists()
                        )
    def test_mixed_produces_both_questions(self):
        '''Ensure both types of questions are generated in mixed option'''
        drug = Drug.objects.get(ranking = 1)
        modes = set()
        for _ in range(100):
            q = build_question(drug, QuestionMode.MIXED, AnswerFormat.MULTIPLE_CHOICE)
            modes.add(q["prompt_field"] in NAME_FIELDS)
        self.assertEqual(modes, {True, False})

class TestFreeTextGrading(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("seed_drugs", verbosity = 0)
        salt_required.cache_clear()
        accepted_answers.cache_clear()


    def test_salt_required_is_found_from_data(self):
        """Checks to see if these drugs are shown to need to have salt included"""
        self.assertEqual(salt_required(), {"hydroxyzine", "metoprolol"})

    def test_generic_accepts_base_name_unless_salt_matters(self):
        """Testing on drugs that do have multiple salts vs those that don't"""
        cases = [
            ("Atorvastatin Calcium", "atorvastatin", True),
            ("Doxycycline Hyclate", "doxycycline", True),
            ("Hydrocodone Bitartrate with Acetaminophen", "hydrocodone with acetaminophen", True),
            ("Metoprolol Succinate", "metoprolol", False),
            ("Hydroxyzine Pamaote", "hydroxyzine", False),
            ("Amoxicillin with Clavulanate Potassium", "amoxicillin", False),
        ]

        for stored, typed, expected in cases:
            with self.subTest(stored = stored, typed = typed):
                self.assertEqual(typed in accepted_answers("generic_name", stored), expected)

    def test_brand_accepts_any_single_brand(self):
        cases = [
            ("Cardizem® (CD), Cartia®, Dilacor®, Dilt-XR®, Tiazac®", "cardizem"),
            ("Coreg® & Coreg® CR", "coreg"),
            ("Wellbutrin® (SR,XL), Zyban®", "zyban")
        ]

        for stored, typed in cases:
            with self.subTest(stored = stored):
                self.assertIn(typed, accepted_answers("brand_name", stored))

    def test_every_drug_accepts_its_own_name(self):
        for drug in Drug.objects.all():
            for field in ("generic_name", "brand_name"):
                with self.subTest(drug = drug.brand_name, field = field):
                    stored = getattr(drug, field)
                    self.assertIn(norm(stored), accepted_answers(field, stored))

    def test_grade(self):
        cases = [
            # (field, format, correct_answer, user_response), expected
            (("drug_class", AnswerFormat.FREE_TEXT, "Antiarrhythmic(Class II and III)", "ANTIARRHYTHMIC."), True),
            (("drug_class", AnswerFormat.FREE_TEXT, "COPD Agent", "agent"), False),
            (("generic_name", AnswerFormat.FREE_TEXT, "Atorvastatin Calcium", "atorvastatin"), True),
            (("generic_name", AnswerFormat.FREE_TEXT, "Metoprolol Succinate", "metoprolol"), False),
            (("brand_name", AnswerFormat.MULTIPLE_CHOICE, "Jenuvia", "Jenuvia"), True),
            (("brand_name", AnswerFormat.MULTIPLE_CHOICE, "Jardiance", "Zyrtec"), False),
            (("generic_name", AnswerFormat.FREE_TEXT, "Atorvastatin Calcium", ""), False),
        ]

        for args, expected in cases:
            with self.subTest(args = args):
                self.assertEqual(grade(*args), expected)

class TestExamEndpoints(APITestCase):

    @classmethod
    def setUpTestData(cls):
        call_command("seed_drugs", verbosity = 0)

    def test_create_returns_one_question_per_drug(self):
        '''A range of 5 drugs produces exactly 5 questions'''
        response = self.client.post("/api/exams/",{
            "ranking_min" : 1,
            "ranking_max" : 5,
            "question_mode" : "recall",
            "allowed_formats" : "multiple_choice"
        }, format = "json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data["questions"]), 5)

        attempt = ExamAttempt.objects.get(pk = response.data["attempt_id"])
        self.assertEqual(attempt.answers.count(), 5)
        self.assertFalse(attempt.answers.exclude(was_correct = None).exists())

    def test_never_displays_answer(self):
        '''The test doesn't display the answer.... duhhh'''

        response = self.client.post("/api/exams/", {
            "ranking_min" : 1,
            "ranking_max" : 50,
            "question_mode" : "mixed",
            "allowed_formats" : "both",
        }, format = "json")

        self.assertEqual(response.status_code, 201)
        for q in response.data["questions"]:
            with self.subTest(id = q["id"]):
                self.assertNotIn("correct_answer", q)
                self.assertNotIn("drug_id", q)

    def test_creation_rejects_bad_config(self):
        '''A bad configuratino returns 400, not a corrected exam'''
        cases = [
            #All incorrect payloads
            ({"ranking_min" : 10, "ranking_max" : 5,
            "question_mode" : "recall",
            "allowed_formats" : "multiple_choice"},
            "min above max"),

            ({"ranking_min" : 1, "ranking_max": 5000,
              "question_mode" : "recall", "allowed_formats" : "multiple_choice"},
              "Range is greater than last seeded drug"),

            ({"ranking_min" : 1, "ranking_max" : 5,
              "question_mode" : "identify", "allowed_formats": "free_text"},
            "Identify cannot be graded as free text"),

            ({"question_mode" : "recall", "allowed_formats" : "multiple_choice"},
             "ranged exam with no range"),
            ]

        for payload, reason in cases:
            with self.subTest(reason = reason):
                response = self.client.post("/api/exams/", payload, format = "json")
                self.assertEqual(response.status_code, 400)
                self.assertFalse(ExamAttempt.objects.exists())

    def test_submit_grades_and_scores(self):
        '''The server grades from its own data, not what the user claims'''
        response = self.client.post("/api/exams/",{
            "ranking_min" : 1, "ranking_max" : 5,
            "question_mode" : "recall", "allowed_formats" : "multiple_choice", 
        }, format = "json")
        attempt_id = response.data["attempt_id"]

        #Client is unable to see the answer; the test looks up the answers serverside
        rows = ExamAnswer.objects.filter(attempt_id = attempt_id).select_related("drug")
        answers = [
            {"id" : r.pk, "user_response" : getattr(r.drug, r.answer_field)} 
            for r in rows
        ]

        result = self.client.post(f"/api/exams/{attempt_id}/submit/",
                                  {"answers" : answers}, format = "json")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["score"], 5)
        self.assertEqual(result.data["total"], 5)