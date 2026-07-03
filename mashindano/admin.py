from django.contrib import admin
from .models import Kitengo, Mshiriki, Alama

class AlamaAdmin(admin.ModelAdmin):
    list_display = ('mshiriki', 'jaji', 'hifdh_score', 'tajweed_score', 'makharij_score', 'jumla_kuu')
    readonly_fields = ('alama_hifdh', 'alama_tajweed', 'alama_makharij', 'jumla_kuu')

    # Hizi ni kodi za kuonyesha alama zilizobaki kwenye list ya admin
    def hifdh_score(self, obj): return obj.alama_hifdh
    def tajweed_score(self, obj): return obj.alama_tajweed
    def makharij_score(self, obj): return obj.alama_makharij
    
    hifdh_score.short_description = 'Hifdh (50)'
    tajweed_score.short_description = 'Tajweed (30)'
    makharij_score.short_description = 'Makharij (20)'

admin.site.register(Kitengo)
admin.site.register(Mshiriki)
admin.site.register(Alama, AlamaAdmin)