from __future__ import annotations

from decimal import Decimal

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
    Nyenzo,
    RekodiMaendeleoMchana,
    RekodiSimuMzazi,
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
    wavulana = serializers.IntegerField(read_only=True, required=False)
    wasichana = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Darasa
        fields = (
            "id",
            "jina",
            "maelezo",
            "idadi_wanafunzi",
            "wavulana",
            "wasichana",
        )


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
    darasa = serializers.IntegerField(required=False, allow_null=True)
    somo = serializers.IntegerField(required=False, allow_null=True)
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

    def validate(self, attrs):
        aina = attrs.get("aina_ya_rekodi") or "Kawaida"
        if aina == "Hifdhu" and not attrs.get("somo"):
            raise serializers.ValidationError({"somo": "Somo la Hifdhu linahitajika."})
        if aina == "Kawaida" and not attrs.get("darasa"):
            raise serializers.ValidationError({"darasa": "Darasa linahitajika."})
        return attrs


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


class NyenzoSerializer(serializers.ModelSerializer):
    faili = serializers.SerializerMethodField()

    class Meta:
        model = Nyenzo
        fields = ("id", "jina_la_faili", "faili", "tarehe_iliyowekwa")

    def get_faili(self, obj):
        if not obj.faili:
            return None
        url = obj.faili.url
        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class PandeItemSerializer(serializers.Serializer):
    sura = serializers.CharField(max_length=100)
    aya_kuanzia = serializers.IntegerField(required=False, allow_null=True)
    aya_kuishia = serializers.IntegerField(required=False, allow_null=True)
    hali = serializers.ChoiceField(
        choices=["Pasi", "Makosa", "Feli"],
        default="Pasi",
    )


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
    mapande = PandeItemSerializer(many=True, required=False, default=list)


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
    mseto = serializers.IntegerField(source="mseto_id", allow_null=True, required=False)

    class Meta:
        model = Mtihani
        fields = ("id", "jina_la_mtihani", "tarehe", "somo", "mseto")


class MtihaniCreateSerializer(serializers.Serializer):
    jina_la_mtihani = serializers.CharField(max_length=100)
    tarehe = serializers.DateField()
    mseto = serializers.IntegerField(required=False, allow_null=True)


class MsetoCreateSerializer(serializers.Serializer):
    jina = serializers.CharField(max_length=100)
    tarehe = serializers.DateField(required=False, allow_null=True)
    muhula = serializers.IntegerField(required=False, allow_null=True)


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
            "amehifadhiwa",
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
    programu_ya_usiku_id = serializers.IntegerField(
        allow_null=True, required=False, read_only=True
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
            "programu_ya_usiku_id",
            "juzuu_aliyohifadhi",
            "tarehe_ya_kujiunga",
            "picha",
            "amehifadhiwa",
            "sababu_ya_kuhifadhiwa",
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


class MalipoCreateSerializer(serializers.Serializer):
    aina_ya_malipo = serializers.IntegerField()
    kiasi = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    njia = serializers.ChoiceField(
        choices=Malipo._meta.get_field("njia_ya_malipo").choices
    )
    maelezo = serializers.CharField(required=False, allow_blank=True, default="")


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


class AinaMalipoWriteSerializer(serializers.Serializer):
    mwaka = serializers.IntegerField(required=False, allow_null=True)
    mwezi = serializers.ChoiceField(
        choices=AinaMalipo.MWEZI_CHOICES,
        required=False,
        allow_null=True,
    )
    jina = serializers.CharField(required=False, allow_blank=True, default="")
    kiasi_kinachotakiwa = serializers.DecimalField(
        max_digits=10, decimal_places=2
    )
    maelezo = serializers.CharField(required=False, allow_blank=True, default="")


class MuhulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Muhula
        fields = ("id", "namba", "jina", "ni_hai")


class MuhulaWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Muhula
        fields = (
            "mwaka",
            "namba",
            "jina",
            "tarehe_kuanzia",
            "tarehe_kuisha",
            "ni_hai",
        )
        extra_kwargs = {
            "jina": {"required": False},
            "tarehe_kuanzia": {"required": False},
            "tarehe_kuisha": {"required": False},
            "ni_hai": {"required": False, "default": False},
        }


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


class MwakaWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MwakaWaMasomo
        fields = (
            "jina",
            "mwaka_kuanzia",
            "mwaka_kuisha",
            "tarehe_kuanzia",
            "tarehe_kuisha",
            "ni_hai",
        )
        extra_kwargs = {
            "tarehe_kuanzia": {"required": False},
            "tarehe_kuisha": {"required": False},
            "ni_hai": {"required": False, "default": False},
        }


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


class MawasilianoContactWriteSerializer(serializers.Serializer):
    jina_la_mzazi = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    uhusiano_wa_mlezi = serializers.CharField(required=False, allow_blank=True)
    namba_ya_simu_mzazi = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    jina_la_mzazi_pili = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    uhusiano_wa_mlezi_pili = serializers.CharField(
        required=False, allow_blank=True
    )
    namba_ya_simu_mzazi_pili = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class MawasilianoWhatsAppOpenSerializer(serializers.Serializer):
    mzazi = serializers.IntegerField(required=False, default=1)
    kigezo = serializers.CharField(required=False, allow_blank=True, default="")
    ujumbe = serializers.CharField(required=False, allow_blank=True, default="")


class RekodiSimuSerializer(serializers.ModelSerializer):
    mwanafunzi = serializers.IntegerField(source="mwanafunzi_id")
    sababu_jina = serializers.CharField(source="get_sababu_display", read_only=True)
    matokeo_jina = serializers.CharField(source="get_matokeo_display", read_only=True)
    iliyorekodiwa_na = serializers.SerializerMethodField()

    class Meta:
        model = RekodiSimuMzazi
        fields = (
            "id",
            "mwanafunzi",
            "namba_iliyopigwa",
            "sababu",
            "sababu_jina",
            "matokeo",
            "matokeo_jina",
            "maelezo",
            "tarehe_ya_simu",
            "iliyorekodiwa_na",
        )

    def get_iliyorekodiwa_na(self, obj):
        if obj.iliyorekodiwa_na_id is None:
            return None
        user = obj.iliyorekodiwa_na
        return user.get_full_name() or user.username


class RekodiSimuWriteSerializer(serializers.Serializer):
    namba_iliyopigwa = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    sababu = serializers.ChoiceField(choices=RekodiSimuMzazi.SABABU_CHOICES)
    matokeo = serializers.ChoiceField(choices=RekodiSimuMzazi.MATOKEO_CHOICES)
    maelezo = serializers.CharField(required=False, allow_blank=True, default="")
    tarehe_ya_simu = serializers.DateTimeField(required=False, allow_null=True)


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
