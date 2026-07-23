from django.core.management.base import BaseCommand
import csv
from drugs.models import Drug
class Command(BaseCommand):

    file_loc = "backend/data/updated_drugs.csv"

    help = "Seeds the database with our initial 200 drugs (missing 100)"

    def handle(self, *args, **options):

        self.stdout.write(self.style.WARNING(f"Seeding new data"))

        with open("/Users/timothytsang/CS/DrugPharmers/backend/data/updated_drugs.csv", encoding = 'utf-8-sig') as drug_file:
            reader = csv.DictReader(drug_file)
            for row in reader:

                Drug.objects.get_or_create(
                    generic_name = row['generic_name'],
                    brand_name = row['brand_name'],
                    defaults = {
                        'drug_class': row['drug_class'],
                        'primary_fda_ind': row['primary_fda_ind'],
                        'other_fda_ind': row['other_fda_ind'],
                        'avail_strengths': row['available_strengths'],
                        'moa': row['moa'],
                        'dosing_regimen': row['dosing_regimen'],
                        'side_effects': row['side_effects'],
                        'boxed_warnings': row['boxed_warnings']

                    }
                )


    

