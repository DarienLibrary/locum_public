from django.contrib import admin

from .models import Patron, Checkout


class PatronAdmin(admin.ModelAdmin):
    model = Patron
    list_display = ["patron_id", "checkout_history_last_checked"]
    # search_fields = ["ils_id", "browse_title", "browse_author", "provider"]
    # raw_id_fields = ["isbns"]


# class BibliographicRecordInline(admin.TabularInline):
#     model = BibliographicRecord
#     raw_id_fields = ("work_record", "isbns")


class CheckoutAdmin(admin.ModelAdmin):
    model = Checkout
    list_display = ["title", "author", "checkout_date"]
    search_fields = ["title", "author"]
    # raw_id_fields = ["primary_bib_record"]
    # inlines = [
    #     BibliographicRecordInline,
    # ]


# class ISBNAdmin(admin.ModelAdmin):
#     model = ISBN
#     list_display = ["isbn"]

admin.site.register(Checkout, CheckoutAdmin)
admin.site.register(Patron, PatronAdmin)
