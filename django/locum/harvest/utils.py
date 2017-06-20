import dateutil.parser
from django.utils import timezone
import csv
from connector import tasks

from harvest.models import BibliographicRecord
from .models import Hold


def import_holds():
    valid_ils_ids = set(tasks.get_bib_record_ids())
    with open('holds.csv', 'r') as f:
        holds = csv.DictReader(f, delimiter=',')
        for hold in holds:
            ils_id = int(hold['bnum'])
            if ils_id in valid_ils_ids:
                try:
                    bib_record = BibliographicRecord.objects.get(ils_id=ils_id)
                except BibliographicRecord.DoesNotExist:
                    bib_record = None
                if bib_record:
                    date_created = timezone.make_aware(
                        dateutil.parser.parse(hold['hold_date']))
                    hold = Hold(
                        bib_record=bib_record
                    )
                    hold.save()
                    hold.date_created = date_created
                    hold.save()
