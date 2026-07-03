from django.db import models
# Tunavuta Mwanafunzi na Mwalimu (Jaji) kutoka kwenye app ya usimamizi
from usimamizi.models import Mwanafunzi, Mwalimu 

class Kitengo(models.Model):
    jina = models.CharField(max_length=50) # Mfano: Juzuu 30, Juzuu 3, Juzuu 5
    
    def __str__(self):
        return self.jina

class Mshiriki(models.Model):
    # Mshiriki lazima awe mwanafunzi aliyesajiliwa
    mwanafunzi = models.ForeignKey(Mwanafunzi, on_delete=models.CASCADE)
    kitengo = models.ForeignKey(Kitengo, on_delete=models.CASCADE)
    namba_ya_kifua = models.CharField(max_length=10, unique=True) # Namba anayovaa mshiriki

    def __str__(self):
        return f"Namba {self.namba_ya_kifua} - {self.mwanafunzi.jina_kamili}"

class Alama(models.Model):
    mshiriki = models.ForeignKey(Mshiriki, on_delete=models.CASCADE)
    jaji = models.ForeignKey(Mwalimu, on_delete=models.CASCADE)
    
    # 1. IDADI YA MAKOSA YA HIFDH
    saka_kubwa = models.IntegerField(default=0, help_text="Makato -5")
    saka_dogo = models.IntegerField(default=0, help_text="Makato -3")
    kibw = models.IntegerField(default=0, help_text="Makato -4")
    neno = models.IntegerField(default=0, help_text="Makato -2")
    shakli = models.IntegerField(default=0, help_text="Makato -1")

    # 2. IDADI YA MAKOSA MENGINE
    makosa_tajweed = models.IntegerField(default=0, help_text="Kila kosa -2")
    makosa_makharij = models.IntegerField(default=0, help_text="Kila kosa -2")
    
    # 3. ALAMA ZA MWISHO (Zitahifadhiwa hapa baada ya kukatwa)
    alama_hifdh = models.IntegerField(default=50, editable=False)
    alama_tajweed = models.IntegerField(default=30, editable=False)
    alama_makharij = models.IntegerField(default=20, editable=False)
    jumla_kuu = models.IntegerField(default=100, editable=False)

    # UBONGO WA KUPIGA HESABU (Hufanya kazi yenyewe kabla ya kusave)
    def save(self, *args, **kwargs):
        # Makato ya Hifdhu (Max 50)
        makato_hifdh = (self.saka_kubwa * 5) + (self.kibw * 4) + (self.saka_dogo * 3) + (self.neno * 2) + (self.shakli * 1)
        self.alama_hifdh = max(0, 50 - makato_hifdh) # Tunatumia max(0) kuzuia isishuke chini ya sufuri

        # Makato ya Tajweed (Max 30)
        self.alama_tajweed = max(0, 30 - (self.makosa_tajweed * 2))

        # Makato ya Makharij (Max 20)
        self.alama_makharij = max(0, 20 - (self.makosa_makharij * 2))

        # Jumla Kuu
        self.jumla_kuu = self.alama_hifdh + self.alama_tajweed + self.alama_makharij
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.mshiriki.mwanafunzi.jina_kamili} | Jaji: {self.jaji.user.username} | Jumla: {self.jumla_kuu}"