from django.contrib import admin
from .models import (
    Darasa,
    Mwalimu,
    Somo,
    Mwanafunzi,
    Hudhurio,
    Tangazo,
    Nyenzo,
    Mtihani,
    Matokeo,
    RekodiHifdhu,
    PandeMurajaa,
    AinaMalipo,
    Malipo,
    MsetoMtihani,
    MwakaWaMasomo,
    Muhula,
    RekodiUkaguzi,
    RekodiSimuMzazi,
)


class NoDeleteAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class MwanafunziAdmin(NoDeleteAdmin):
    list_display = (
        "jina_kamili",
        "namba_ya_usajili",
        "umri",
        "amehifadhiwa",
        "mahala_anapoishi",
        "jina_la_mzazi",
        "uhusiano_wa_mlezi",
        "namba_ya_simu_mzazi",
        "tarehe_ya_kujiunga",
    )
    search_fields = ("jina_kamili", "namba_ya_usajili", "jina_la_mzazi", "namba_ya_simu_mzazi")
    list_filter = ("amehifadhiwa", "mahala_anapoishi", "darasa")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("namba_ya_usajili", "tarehe_ya_kuhifadhiwa")
        return ()

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj is None:
            return [f for f in fields if f != "namba_ya_usajili"]
        return fields


class HudhurioAdmin(NoDeleteAdmin):
    list_display = ("mwanafunzi", "tarehe", "yupo", "aina_ya_rekodi", "iliyorekodiwa_na")
    list_filter = ("tarehe", "yupo", "aina_ya_rekodi")


class MaendeleoAdmin(NoDeleteAdmin):
    list_display = ("mwanafunzi", "tarehe", "sabaq_sura", "sabaq_hali", "mwalimu")
    list_filter = ("tarehe", "mwalimu")
    search_fields = ("mwanafunzi__jina_kamili", "sabaq_sura")


admin.site.register(Darasa, NoDeleteAdmin)
admin.site.register(Mwalimu, NoDeleteAdmin)
admin.site.register(Somo, NoDeleteAdmin)
admin.site.register(Hudhurio, HudhurioAdmin)
admin.site.register(Tangazo, NoDeleteAdmin)
admin.site.register(Nyenzo, NoDeleteAdmin)


class MtihaniAdmin(NoDeleteAdmin):
    list_display = ("jina_la_mtihani", "somo", "mseto", "tarehe")
    list_filter = ("mseto", "somo__darasa")


admin.site.register(Mtihani, MtihaniAdmin)
admin.site.register(Matokeo, NoDeleteAdmin)
admin.site.register(PandeMurajaa, NoDeleteAdmin)
admin.site.register(Mwanafunzi, MwanafunziAdmin)
admin.site.register(RekodiHifdhu, MaendeleoAdmin)


class MuhulaInline(admin.TabularInline):
    model = Muhula
    extra = 1
    fields = ("namba", "jina", "tarehe_kuanzia", "tarehe_kuisha", "ni_hai")


@admin.register(MwakaWaMasomo)
class MwakaWaMasomoAdmin(NoDeleteAdmin):
    list_display = (
        "jina",
        "mwaka_kuanzia",
        "mwaka_kuisha",
        "ni_hai",
        "tarehe_kuanzia",
        "tarehe_kuisha",
    )
    list_filter = ("ni_hai",)
    search_fields = ("jina",)
    inlines = [MuhulaInline]


@admin.register(Muhula)
class MuhulaAdmin(NoDeleteAdmin):
    list_display = ("jina", "mwaka", "namba", "ni_hai", "tarehe_kuanzia", "tarehe_kuisha")
    list_filter = ("mwaka", "ni_hai", "namba")
    search_fields = ("jina", "mwaka__jina")


@admin.register(MsetoMtihani)
class MsetoMtihaniAdmin(NoDeleteAdmin):
    list_display = ("jina", "darasa", "muhula", "tarehe", "tarehe_iliyoundwa")
    list_filter = ("darasa", "muhula__mwaka", "muhula")


@admin.register(AinaMalipo)
class AinaMalipoAdmin(NoDeleteAdmin):
    list_display = ("jina", "kiasi_kinachotakiwa", "tarehe_ya_kuanzishwa")


@admin.register(Malipo)
class MalipoAdmin(NoDeleteAdmin):
    list_display = (
        "mwanafunzi",
        "aina_ya_malipo",
        "kiasi_kilicholipwa",
        "tarehe_ya_malipo",
        "iliyorekodiwa_na",
        "mpokeaji",
    )
    list_filter = ("aina_ya_malipo", "njia_ya_malipo")
    search_fields = ("mwanafunzi__jina_kamili",)


@admin.register(RekodiUkaguzi)
class RekodiUkaguziAdmin(NoDeleteAdmin):
    list_display = ("tarehe_ya_kitendo", "kitendo", "mtumiaji", "maelezo", "idadi_ya_rekodi")
    list_filter = ("kitendo", "tarehe_ya_kitendo")
    search_fields = ("maelezo", "mtumiaji__username", "mwanafunzi__jina_kamili")
    readonly_fields = (
        "mtumiaji",
        "kitendo",
        "maelezo",
        "darasa",
        "somo",
        "mwanafunzi",
        "malipo",
        "idadi_ya_rekodi",
        "tarehe_ya_kitendo",
    )

    def has_add_permission(self, request):
        return False


@admin.register(RekodiSimuMzazi)
class RekodiSimuMzaziAdmin(NoDeleteAdmin):
    list_display = (
        "tarehe_ya_simu",
        "mwanafunzi",
        "namba_iliyopigwa",
        "sababu",
        "matokeo",
        "iliyorekodiwa_na",
    )
    list_filter = ("sababu", "matokeo", "tarehe_ya_simu")
    search_fields = (
        "mwanafunzi__jina_kamili",
        "namba_iliyopigwa",
        "maelezo",
        "iliyorekodiwa_na__username",
    )
