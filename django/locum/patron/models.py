from celery.contrib.methods import task

from django.db import models
from django.utils import timezone

from harvest.models import Hold, BibliographicRecord
import connector.tasks
import overdrive.tasks
import bibliotheca.tasks
import harvest.tasks
import envisionware.tasks
import hoopla.tasks

providers = {
    'overdrive': overdrive.tasks,
    'bibliotheca': bibliotheca.tasks,
    'mmm': bibliotheca.tasks,
    'hoopla': hoopla.tasks,
}


class Patron(models.Model):

    patron_id = models.IntegerField(unique=True)
    checkout_history_last_checked = models.DateTimeField(null=True)

    def get_ils_details(self):
        ils_details = connector.tasks.get_patron(self.patron_id)
        if ils_details:
            return ils_details
        else:
            return {}

    def update_ils_basic_data(self, **kwargs):
        barcode = self.get_ils_details()['barcode']
        resp = connector.tasks.update_patron_basic_data(barcode, self.patron_id, **kwargs)
        return resp

    def get_circulation(self, provider):
        barcode = self.get_ils_details()['barcode']
        if provider in providers.keys():
            resp = providers[provider].get_circulation(barcode)
            for circ in ['checkouts', 'holds']:
                for item in resp.get(circ, []):
                    details = harvest.tasks.get_ils_details(
                        item['provider'],
                        item['provider_id'])
                    item.update(details)
        else:
            resp = harvest.tasks.get_patron_circulation(barcode)
        return resp

    def get_checkout_history(self, limit, offset):
        resp = connector.tasks.get_patron_checkout_history(
            self.patron_id,
            limit,
            offset)
        return resp

    def clear_checkout_history(self):
        patron_barcode = self.get_ils_details()['barcode']
        resp = connector.tasks.clear_patron_checkout_history(patron_barcode)
        return resp

    def checkout(self, provider, item_id):
        if provider in providers.keys():
            barcode = self.get_ils_details()['barcode']
            resp = providers[provider].checkout(barcode, item_id)
            return resp

    def checkin(self, provider, item_id):
        if provider in providers.keys():
            barcode = self.get_ils_details()['barcode']
            resp = providers[provider].checkin(barcode, item_id)
            return resp

    def place_hold(self, provider, item_id):
        details = self.get_ils_details()
        barcode = details['barcode']
        email = details['email']
        if provider in providers.keys():
            if '@' not in email:
                resp = {
                    "success": False,
                    "error": "invalid email address"
                }
            else:
                resp = providers[provider].place_hold(barcode, item_id, email)
        else:
            resp = connector.tasks.patron_place_hold(self.patron_id, item_id)
            if resp['success']:
                try:
                    bib_record = BibliographicRecord.objects.get(ils_id=item_id)
                except BibliographicRecord.DoesNotExist:
                    bib_record = None
                if bib_record:
                    hold = Hold(bib_record=bib_record)
                    hold.save()
        return resp

    def cancel_hold(self, provider, item_id):
        barcode = self.get_ils_details()['barcode']
        if provider in providers.keys():
            resp = providers[provider].cancel_hold(barcode, item_id)
        else:
            resp = connector.tasks.patron_cancel_hold(barcode, item_id)
        return resp

    def suspend_hold(self, provider, request_id, activation_date):
        details = self.get_ils_details()
        barcode = details['barcode']
        email = details['email']
        if provider in providers.keys():
            if '@' not in email:
                resp = {
                    "success": False,
                    "error": "invalid email address"
                }
            else:
                resp = providers[provider].suspend_hold(
                    barcode,
                    request_id,
                    email)
        else:
            resp = connector.tasks.patron_suspend_hold(
                barcode,
                request_id,
                activation_date)
        return resp

    def suspend_all_holds(self, activation_date):
        barcode = self.get_ils_details()['barcode']
        resp = connector.tasks.patron_suspend_all_holds(
            barcode,
            activation_date)
        return resp

    def reactivate_hold(self, provider, request_id):
        barcode = self.get_ils_details()['barcode']
        if provider in providers.keys():
            resp = providers[provider].reactivate_hold(
                barcode,
                request_id)
        else:
            resp = connector.tasks.patron_reactivate_hold(
                barcode,
                request_id)
        return resp

    def reactivate_all_holds(self):
        barcode = self.get_ils_details()['barcode']
        resp = connector.tasks.patron_reactivate_all_holds(barcode)
        return resp

    def get_fines(self):
        barcode = self.get_ils_details()['barcode']
        resp = connector.tasks.get_patron_fines(barcode)
        return resp

    def get_balance(self):
        barcode = self.get_ils_details()['barcode']
        resp = envisionware.tasks.get_balance(barcode)
        return resp


class Checkout(models.Model):

    checkout_date = models.DateTimeField()
    patron = models.ForeignKey(Patron, related_name='checkouts')
    title = models.CharField(max_length=1023, blank=True)
    author = models.CharField(max_length=1023, blank=True)

    class Meta:
        ordering = ['-checkout_date']
