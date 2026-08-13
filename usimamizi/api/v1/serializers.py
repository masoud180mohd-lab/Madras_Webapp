from __future__ import annotations

from rest_framework import serializers

from usimamizi.models import Darasa, Hudhurio, Mwanafunzi


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    jina = serializers.CharField()
    cheo = serializers.CharField(allow_null=True)
    capabilities = serializers.ListField(child=serializers.CharField())


class DarasaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Darasa
        fields = ("id", "jina", "maelezo")


class MwanafunziRosterSerializer(serializers.ModelSerializer):
    picha = serializers.SerializerMethodField()

    class Meta:
        model = Mwanafunzi
        fields = (
            "id",
            "jina_kamili",
            "namba_ya_usajili",
            "jinsia",
            "picha",
        )

    def get_picha(self, obj):
        if not obj.picha:
            return None
        request = self.context.get("request")
        url = obj.picha.url
        if request:
            return request.build_absolute_uri(url)
        return url


class HudhurioRowSerializer(serializers.Serializer):
    mwanafunzi = serializers.IntegerField()
    yupo = serializers.BooleanField()
    sababu_kama_hayupo = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class MahudhurioBatchSerializer(serializers.Serializer):
    darasa = serializers.IntegerField()
    tarehe = serializers.DateField(required=False)
    aina_ya_rekodi = serializers.ChoiceField(
        choices=["Kawaida", "Hifdhu"],
        default="Kawaida",
    )
    rekodi = HudhurioRowSerializer(many=True)

    def validate_rekodi(self, value):
        if not value:
            raise serializers.ValidationError("Rekodi haziwezi kuwa tupu.")
        ids = [row["mwanafunzi"] for row in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Mwanafunzi amerudiwa kwenye rekodi.")
        return value


class HudhurioSerializer(serializers.ModelSerializer):
    mwanafunzi = serializers.IntegerField(source="mwanafunzi_id")

    class Meta:
        model = Hudhurio
        fields = (
            "id",
            "mwanafunzi",
            "tarehe",
            "yupo",
            "sababu_kama_hayupo",
            "aina_ya_rekodi",
        )
