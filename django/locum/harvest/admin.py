from django.contrib import admin

from .models import BibliographicRecord, WorkRecord, ISBN


class BibliographicRecordAdmin(admin.ModelAdmin):
    model = BibliographicRecord
    list_display = ["ils_id",
                    "author",
                    "browse_title",
                    "provider",
                    "provider_id",
                    "abs_mat_code"]
    search_fields = ["ils_id", "browse_title", "browse_author", "provider"]
    list_filter = ["abs_mat_code", "provider"]
    raw_id_fields = ["isbns"]


class BibliographicRecordInline(admin.TabularInline):
    model = BibliographicRecord
    raw_id_fields = ("work_record", "isbns")


class WorkRecordAdmin(admin.ModelAdmin):
    model = WorkRecord
    list_display = ["id", "title", "author"]
    search_fields = ["title", "author"]
    raw_id_fields = ["primary_bib_record"]
    inlines = [
        BibliographicRecordInline,
    ]


class ISBNAdmin(admin.ModelAdmin):
    model = ISBN
    list_display = ["isbn"]

admin.site.register(BibliographicRecord, BibliographicRecordAdmin)
admin.site.register(WorkRecord, WorkRecordAdmin)
admin.site.register(ISBN, ISBNAdmin)
