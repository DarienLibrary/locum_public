from rest_framework import serializers

from .models import Checkout


class CheckoutSerializer(serializers.ModelSerializer):

    patron_id = serializers.SerializerMethodField()

    def get_patron_id(self, obj):
        return obj.patron.patron_id

    class Meta:
        model = Checkout
        fields = [
            "id",
            "patron_id",
            "title",
            "author",
            "checkout_date",
        ]
