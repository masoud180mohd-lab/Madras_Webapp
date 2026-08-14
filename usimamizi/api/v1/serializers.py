from __future__ import annotations

from rest_framework import serializers

from usimamizi.models import (
    Darasa,
    Hudhurio,
    Mtihani,
    Mwanafunzi,
    RekodiMaendeleoMchana,
    Somo,
)


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


class SomoSerializer(serializers.ModelSerializer):
    darasa = serializers.IntegerField(source="darasa_id", allow_null=True)

    class Meta:
        model = Somo
        fields = ("id", "jina", "ni_la_hifdhu", "darasa")


class SabaqCreateSerializer(serializers.Serializer):
    mwanafunzi = serializers.IntegerField()
    aina_ya_rekodi = serializers.ChoiceField(choices=["Darasa", "Usiku"])
    sabaq_sura = serializers.CharField(required=False, allow_blank=True, default="")
    sabaq_aya_kuanzia = serializers.IntegerField(required=False, allow_null=True)
    sabaq_aya_kuishia = serializers.IntegerField(required=False, allow_null=True)
    sabaq_hali = serializers.ChoiceField(
        choices=["Kajua", "Hajajua", "Hajasikilizwa"],
        required=False,
        allow_null=True,
    )
    maoni_ya_mwalimu = serializers.CharField(
        required=False, allow_blank=True, default=""
    )


class MaendeleoCreateSerializer(serializers.Serializer):
    mwanafunzi = serializers.IntegerField()
    somo = serializers.IntegerField()
    mada_iliyosomwa = serializers.CharField(max_length=200)
    ukurasa_au_aya = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    hali = serializers.ChoiceField(
        choices=[
            RekodiMaendeleoMchana.HALI_AMEELEWA,
            RekodiMaendeleoMchana.HALI_HAJAELEWA,
            RekodiMaendeleoMchana.HALI_HAJASIKILIZWA,
        ]
    )
    maoni = serializers.CharField(required=False, allow_blank=True, default="")


class MtihaniSerializer(serializers.ModelSerializer):
    somo = serializers.IntegerField(source="somo_id")

    class Meta:
        model = Mtihani
        fields = ("id", "jina_la_mtihani", "tarehe", "somo")


class MaksiRowSerializer(serializers.Serializer):
    mwanafunzi = serializers.IntegerField()
    maksi = serializers.FloatField(min_value=0, max_value=100)


class MaksiBatchSerializer(serializers.Serializer):
    rekodi = MaksiRowSerializer(many=True)

    def validate_rekodi(self, value):
        if not value:
            raise serializers.ValidationError("Rekodi haziwezi kuwa tupu.")
        ids = [row["mwanafunzi"] for row in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Mwanafunzi amerudiwa kwenye rekodi.")
        return value
