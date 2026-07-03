from django.contrib import admin
from .models import Darasa, Mwalimu, Somo, Mwanafunzi, Hudhurio, Tangazo, Nyenzo, Mtihani, Matokeo, RekodiHifdhu, PandeMurajaa, AinaMalipo, Malipo, MsetoMtihani

class MwanafunziAdmin(admin.ModelAdmin):
    list_display = ('jina_kamili', 'namba_ya_usajili', 'umri', 'mahala_anapoishi', 'jina_la_mzazi', 'namba_ya_simu_mzazi', 'tarehe_ya_kujiunga')
    search_fields = ('jina_kamili', 'namba_ya_usajili')
    list_filter = ('mahala_anapoishi',)

    # 1. Hii inafanya namba ionekane lakini isiharirike (Read-only) mwanafunzi akiwa tayari yupo
    def get_readonly_fields(self, request, obj=None):
        if obj: # Ikiwa mwanafunzi ameshaandikishwa (Editing)
            return ('namba_ya_usajili',)
        return () # Ikiwa ni usajili mpya

    # 2. Hii inaificha namba isionekane kabisa kwenye fomu ya kusajili mpya
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj is None: # Wakati wa kusajili mwanafunzi mpya
            # Ondoa namba ya usajili kwenye orodha ya maboksi ya kujaza
            return [f for f in fields if f != 'namba_ya_usajili']
        return fields

class HudhurioAdmin(admin.ModelAdmin):
    list_display = ('mwanafunzi', 'tarehe', 'yupo', 'sababu_kama_hayupo')
    list_filter = ('tarehe', 'yupo')

class MaendeleoAdmin(admin.ModelAdmin):
    list_display = ('mwanafunzi', 'tarehe', 'sabaq_sura', 'sabaq_hali', 'mwalimu')
    list_filter = ('tarehe', 'mwalimu')
    search_fields = ('mwanafunzi__jina_kamili', 'sabaq_sura')

# USAJILI WA MODELS KWA ADMIN
admin.site.register(Darasa)
admin.site.register(Mwalimu)
admin.site.register(Somo)
admin.site.register(Hudhurio, HudhurioAdmin)
admin.site.register(Tangazo)
admin.site.register(Nyenzo)

class MtihaniAdmin(admin.ModelAdmin):
    list_display = ('jina_la_mtihani', 'somo', 'mseto', 'tarehe')
    list_filter = ('mseto', 'somo__darasa')

admin.site.register(Mtihani, MtihaniAdmin)
admin.site.register(Matokeo)
admin.site.register(PandeMurajaa)

# MUHIMU: Tumesajili Mwanafunzi pamoja na MwanafunziAdmin yake
admin.site.register(Mwanafunzi, MwanafunziAdmin)

# Tumesajili RekodiHifdhu pamoja na MaendeleoAdmin yake
admin.site.register(RekodiHifdhu, MaendeleoAdmin)

@admin.register(MsetoMtihani)
class MsetoMtihaniAdmin(admin.ModelAdmin):
    list_display = ('jina', 'darasa', 'tarehe', 'tarehe_iliyoundwa')
    list_filter = ('darasa',)

@admin.register(AinaMalipo)
class AinaMalipoAdmin(admin.ModelAdmin):
    list_display = ('jina', 'kiasi_kinachotakiwa', 'tarehe_ya_kuanzishwa')

@admin.register(Malipo)
class MalipoAdmin(admin.ModelAdmin):
    list_display = ('mwanafunzi', 'aina_ya_malipo', 'kiasi_kilicholipwa', 'tarehe_ya_malipo')
    list_filter = ('aina_ya_malipo', 'njia_ya_malipo')
    search_fields = ('mwanafunzi__jina_kamili',)