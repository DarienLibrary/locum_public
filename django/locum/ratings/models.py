from django.db import models


class Review(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=256)
    body = models.TextField()
    patron = models.ForeignKey('patron.Patron', related_name='reviews')
    bib_record = models.ForeignKey(
        'harvest.BibliographicRecord',
        related_name='reviews')

    class Meta:
        ordering = ['-date_modified']


class Rating(models.Model):
    SCORE_CHOICES = zip(range(1, 5), range(1, 5))
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    rating = models.IntegerField(choices=SCORE_CHOICES)
    patron = models.ForeignKey('patron.Patron', related_name='ratings')
    bib_record = models.ForeignKey(
        'harvest.BibliographicRecord',
        related_name='ratings')

    class Meta:
        ordering = ['-date_modified']


class Wish(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    patron = models.ForeignKey('patron.Patron', related_name='wishes')
    work_record = models.ForeignKey(
        'harvest.WorkRecord',
        related_name='wishes')

    class Meta:
        ordering = ['-date_created']