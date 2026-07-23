from django.db import models


class Drug(models.Model):
    generic_name = models.CharField(max_length = 200)
    brand_name = models.CharField(max_length = 200)
    drug_class = models.CharField(max_length = 200)
    primary_fda_ind = models.TextField()
    other_fda_ind = models.TextField()
    avail_strengths = models.TextField()
    moa = models.TextField()
    dosing_regimen = models.TextField()
    side_effects = models.TextField()
    boxed_warnings = models.TextField()

    def __str__(self):
        return f"(Brand: {self.brand_name}, Generic: {self.generic_name}, Classification: {self.drug_class}, Primary FDA: {self.primary_fda_ind})"
