from django.test import TestCase
from rest_framework.test import APITestCase
from .models import Drug


# Create your tests here.

class TestAPIs(APITestCase):

    def setUp(self):
        self.a_drug = Drug.objects.create(generic_name = "A",
                                        brand_name = "A Train",
                                        drug_class = "Drug Type A",
                                        primary_fda_ind = "Used to treat farts",
                                        avail_strengths = "5mg, 10mg, 15mg",
                                        moa = "Absorption in the stomach",
                                        dosing_regimen = "5 poq",
                                        side_effects = "Burps"
                                        )
    
    def test_list_returns_200(self):
        response = self.client.get("/api/drugs/")
        self.assertEqual(response.status_code, 200)
