from __future__ import annotations

from rest_framework import serializers

from usimamizi.models import (
    AinaMalipo,
    Darasa,
    Hudhurio,
    Malipo,
    Mtihani,
    Muhula,
    MwakaWaMasomo,
    Mwalimu,
    Mwanafunzi,
    RekodiMaendeleoMchana,
    RekodiUkaguzi,
    Somo,
    Tangazo,
)


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    jina = serializers.CharField()
    cheo = serializers.CharField(allow_null=True)
    capabilities = serializers.ListField(child=serializers.CharField())


class DarasaSerializer(serializers.ModelSerializer):
    idadi_wanafunzi = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Darasa
        fields = ("id", "jina", "maelezo", "idadi_wanafunzi")


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
    darasa_jina = serializers.CharField(source="darasa.jina", allow_null=True)
    mwalimu = serializers.SerializerMethodField()

    class Meta:
        model = Somo
        fields = (
            "id",
            "jina",
            "ni_la_hifdhu",
            "darasa",
            "darasa_jina",
            "mwalimu",
        )

    def get_mwalimu(self, obj):
        if obj.mwalimu_id is None:
            return None
        user = obj.mwalimu.user
        return user.get_full_name() or user.username


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


class MwalimuSerializer(serializers.ModelSerializer):
    jina = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username", read_only=True)
    picha = serializers.SerializerMethodField()

    class Meta:
        model = Mwalimu
        fields = ("id", "jina", "username", "cheo", "namba_ya_simu", "picha")

    def get_jina(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_picha(self, obj):
        if not obj.picha:
            return None
        request = self.context.get("request")
        url = obj.picha.url
        if request:
            return request.build_absolute_uri(url)
        return url


class MwanafunziDirectorySerializer(serializers.ModelSerializer):
    darasa = serializers.CharField(source="darasa.jina", allow_null=True)
    darasa_id = serializers.IntegerField(allow_null=True, required=False)
    picha = serializers.SerializerMethodField()

    class Meta:
        model = Mwanafunzi
        fields = (
            "id",
            "jina_kamili",
            "namba_ya_usajili",
            "jinsia",
            "darasa",
            "darasa_id",
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


class MwanafunziDetailSerializer(serializers.ModelSerializer):
    darasa = serializers.CharField(source="darasa.jina", allow_null=True)
    darasa_id = serializers.IntegerField(allow_null=True, required=False)
    programu_usiku = serializers.CharField(
        source="programu_ya_usiku.jina", allow_null=True
    )
    picha = serializers.SerializerMethodField()

    class Meta:
        model = Mwanafunzi
        fields = (
            "id",
            "jina_kamili",
            "namba_ya_usajili",
            "jinsia",
            "tarehe_ya_kuzaliwa",
            "mahala_anapoishi",
            "darasa",
            "darasa_id",
            "programu_usiku",
            "juzuu_aliyohifadhi",
            "tarehe_ya_kujiunga",
            "picha",
            "jina_la_mzazi",
            "namba_ya_simu_mzazi",
            "uhusiano_wa_mlezi",
            "jina_la_mzazi_pili",
            "namba_ya_simu_mzazi_pili",
            "uhusiano_wa_mlezi_pili",
        )

    def get_picha(self, obj):
        if not obj.picha:
            return None
        request = self.context.get("request")
        url = obj.picha.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request is None:
            return data
        from usimamizi.permissions import CAP_PARENT_CONTACT, user_has_capability

        if not user_has_capability(request.user, CAP_PARENT_CONTACT):
            for key in (
                "jina_la_mzazi",
                "namba_ya_simu_mzazi",
                "uhusiano_wa_mlezi",
                "jina_la_mzazi_pili",
                "namba_ya_simu_mzazi_pili",
                "uhusiano_wa_mlezi_pili",
            ):
                data.pop(key, None)
        return data


class WatoroRowSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    jina_kamili = serializers.CharField()
    darasa = serializers.CharField(allow_null=True)
    idadi_ya_utoro = serializers.IntegerField()
    aina = serializers.CharField()
    aina_jina = serializers.CharField()


class MalipoSerializer(serializers.ModelSerializer):
    mwanafunzi = serializers.CharField(source="mwanafunzi.jina_kamili")
    aina = serializers.CharField(source="aina_ya_malipo.lebo_kamili")

    class Meta:
        model = Malipo
        fields = (
            "id",
            "mwanafunzi",
            "aina",
            "kiasi_kilicholipwa",
            "tarehe_ya_malipo",
            "njia_ya_malipo",
        )


class AinaMalipoSerializer(serializers.ModelSerializer):
    lebo_kamili = serializers.CharField(read_only=True)
    mwaka = serializers.CharField(source="mwaka.jina", allow_null=True)

    class Meta:
        model = AinaMalipo
        fields = (
            "id",
            "jina",
            "lebo_kamili",
            "kiasi_kinachotakiwa",
            "mwaka",
            "mwezi",
        )


class MuhulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Muhula
        fields = ("id", "namba", "jina", "ni_hai")


class MwakaSerializer(serializers.ModelSerializer):
    muhula = MuhulaSerializer(many=True, read_only=True)

    class Meta:
        model = MwakaWaMasomo
        fields = (
            "id",
            "jina",
            "mwaka_kuanzia",
            "mwaka_kuisha",
            "ni_hai",
            "muhula",
        )


class MawasilianoSerializer(serializers.ModelSerializer):
    darasa = serializers.CharField(source="darasa.jina", allow_null=True)

    class Meta:
        model = Mwanafunzi
        fields = (
            "id",
            "jina_kamili",
            "namba_ya_usajili",
            "darasa",
            "jina_la_mzazi",
            "namba_ya_simu_mzazi",
            "uhusiano_wa_mlezi",
            "jina_la_mzazi_pili",
            "namba_ya_simu_mzazi_pili",
        )


class UkaguziSerializer(serializers.ModelSerializer):
    mtumiaji = serializers.SerializerMethodField()
    kitendo_jina = serializers.CharField(source="get_kitendo_display")

    class Meta:
        model = RekodiUkaguzi
        fields = (
            "id",
            "kitendo",
            "kitendo_jina",
            "maelezo",
            "mtumiaji",
            "tarehe_ya_kitendo",
        )

    def get_mtumiaji(self, obj):
        if obj.mtumiaji is None:
            return None
        return obj.mtumiaji.get_full_name() or obj.mtumiaji.username


class TangazoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tangazo
        fields = ("id", "kichwa_cha_habari", "maelezo", "tarehe_iliyotolewa")
