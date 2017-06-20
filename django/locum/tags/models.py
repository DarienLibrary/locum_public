from django.db import models


class Label(models.Model):
    value = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['value']


class Tag(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    label = models.ForeignKey(Label, related_name='tags')
    bib_record = models.ForeignKey(
        'harvest.BibliographicRecord',
        related_name='tags')

    class Meta:
        ordering = ['-date_modified']
