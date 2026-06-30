from django.db import models


class Drug(models.Model):
    brand_name = models.CharField(max_length = 200)
    generic_name = models.CharField(max_length = 200)
    drug_class = models.CharField(max_length = 200)
    moa = models.TextField()
    dosage = models.CharField(max_length = 200)
    dosingSched = models.CharField(max_length = 200)
    bbLabel = models.TextField()
    advEffects = models.CharField(max_length = 200)

    def __str__(self):
        return f"({self.brand_name}, {self.generic_name})"
