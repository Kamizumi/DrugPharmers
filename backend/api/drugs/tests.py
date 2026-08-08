from rest_framework.test import APITestCase
from django.test import TestCase
from django.core.management import call_command
from .models import Drug
from .exam_generation import build_question
from .exam_rules import QuestionMode, AnswerFormat, ANSWER_FORMATS, NAME_FIELDS


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

