import dateutil.parser
from django.utils import timezone
import math
import csv
from connector import tasks

from harvest.models import BibliographicRecord
from patron.models import Patron
from .models import Review, Rating

barcode_to_id_mapping = tasks.get_patron_barcode_to_id_mapping()
valid_barcodes = set(barcode_to_id_mapping.keys())
valid_ils_ids = set(tasks.get_bib_record_ids())


def import_reviews():
    with open('reviews.csv', 'r') as f:
        reviews = csv.DictReader(f, delimiter=',')
        for review in reviews:
            if review['barcode'] in valid_barcodes and int(review['ils_id']) in valid_ils_ids:
                patron_id = barcode_to_id_mapping[review['barcode']]
                try:
                    patron = Patron.objects.get(patron_id=patron_id)
                except Patron.DoesNotExist:
                    patron = Patron(patron_id=patron_id)
                    patron.save()
                try:
                    bib_record = BibliographicRecord.objects.get(ils_id=int(review['ils_id']))
                except BibliographicRecord.DoesNotExist:
                    bib_record = None
                if patron and bib_record:
                    date_created = timezone.make_aware(
                        dateutil.parser.parse(review['date_created']))
                    review = Review(
                        patron=patron,
                        bib_record=bib_record,
                        title=review['title'],
                        body=review['body']
                    )
                    review.save()
                    review.date_created = date_created
                    review.save()


def import_ratings():
    with open('ratings.csv', 'r') as f:
        ratings = csv.DictReader(f, delimiter=',')
        for rating in ratings:
            if rating['barcode'] in valid_barcodes and int(rating['ils_id']) in valid_ils_ids:
                patron_id = barcode_to_id_mapping[rating['barcode']]
                try:
                    patron = Patron.objects.get(patron_id=patron_id)
                except Patron.DoesNotExist:
                    patron = Patron(patron_id=patron_id)
                    patron.save()
                try:
                    bib_record = BibliographicRecord.objects.get(ils_id=int(rating['ils_id']))
                except BibliographicRecord.DoesNotExist:
                    bib_record = None
                if patron and bib_record:
                    date_created = timezone.make_aware(
                        dateutil.parser.parse(rating['date_created']))
                    score = math.ceil(float(rating['rating']))
                    rating = Rating(
                        patron=patron,
                        bib_record=bib_record,
                        rating=score
                    )
                    rating.save()
                    rating.date_created = date_created
                    rating.save()
