from rest_framework import serializers

from .models import Tag, Label


class LabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Label
        fields = [
            'id',
            'value',
        ]


class TagSerializer(serializers.ModelSerializer):
    label = LabelSerializer(read_only=True)

    class Meta:
        model = Tag
        fields = [
            'id',
            'label',
        ]
