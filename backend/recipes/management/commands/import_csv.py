import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


def find_data(csv_file):
    """Найти и открыть нужный файл csv."""
    csv_path = os.path.join(
        settings.BASE_DIR, "data", csv_file
    )
    return csv.reader(open(csv_path, "r", encoding="utf-8"), delimiter=",")


class Command(BaseCommand):
    help = "Импортирует данные из csv файлов."

    def handle(self, *args, **options):
        reader = find_data("ingredients.csv")
        for row in reader:
            data, status = Ingredient.objects.get_or_create(
                name=row[0],
                measurement_unit=row[1],
            )
        reader = find_data("tags.csv")
        for row in reader:
            data, status = Tag.objects.get_or_create(
                name=row[0],
                color=row[1],
                slug=row[2],
            )
        self.stdout.write(self.style.SUCCESS("Данные загружены!"))
