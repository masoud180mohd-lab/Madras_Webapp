from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from datetime import date

PICHA_MAX_SIZE = 512 * 1024
PICHA_FORMATS = ("jpg", "jpeg", "png", "webp")
NYENZO_MAX_SIZE = 10 * 1024 * 1024
NYENZO_FORMATS = (
    "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt",
    "jpg", "jpeg", "png", "webp",
)


def _validate_file_size(uploaded_file, max_size, label):
    if uploaded_file and uploaded_file.size > max_size:
        max_mb = max_size / (1024 * 1024)
        max_display = f"{max_mb:g}"
        raise ValidationError(f"{label} lisizidi {max_display}MB.")


def _validate_file_extension(uploaded_file, allowed_extensions, label):
    extension = Path(uploaded_file.name).suffix.lower().lstrip(".")
    if extension not in allowed_extensions:
        formats = ", ".join(ext.upper() for ext in allowed_extensions)
        raise ValidationError(f"{label} linapaswa kuwa katika format hizi: {formats}.")


def validate_picha(uploaded_file):
    _validate_file_size(uploaded_file, PICHA_MAX_SIZE, "Picha")
    _validate_file_extension(uploaded_file, PICHA_FORMATS, "Picha")


def validate_nyenzo(uploaded_file):
    _validate_file_size(uploaded_file, NYENZO_MAX_SIZE, "Faili")
    _validate_file_extension(uploaded_file, NYENZO_FORMATS, "Faili")


class Darasa(models.Model):
    jina = models.CharField(max_length=50, help_text="Mfano: Darasa la Kwanza, Ibtidai, n.k.")
    maelezo = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.jina

class Mwalimu(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    namba_ya_simu = models.CharField(max_length=15, blank=True, null=True)
    cheo = models.CharField(max_length=50, choices=[
        ('Mwalimu Mkuu', 'Mwalimu Mkuu'),
        ('Mwalimu wa Kawaida', 'Mwalimu wa Kawaida'),
        ('Jaji', 'Jaji')
    ])
    picha = models.ImageField(upload_to='picha_za_walimu/', null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Somo(models.Model):
    jina = models.CharField(max_length=100, help_text="Mfano: Fiqhi, Tawheed, Hifdhu (Tashjii)")
    ni_la_hifdhu = models.BooleanField(default=False, help_text="Weka TIKI hapa kama hili ni somo maalum la Hifdhu linalohitaji Mahudhurio na Sabaq zake")
    mwalimu = models.ForeignKey(Mwalimu, on_delete=models.SET_NULL, null=True, blank=True)

    darasa = models.ForeignKey('Darasa', on_delete=models.CASCADE, null=True, blank=True, related_name='masomo')

    def __str__(self):
        return self.jina

class Mwanafunzi(models.Model):
    jina_kamili = models.CharField(
        max_length=100,
        unique=True,
        error_messages={
            'unique': "Mwanafunzi with this Jina already exists.",
        }
    )

    # 1. Tumeruhusu namba ya usajili iwe wazi kwenye fomu, mfumo utaijaza yenyewe
    namba_ya_usajili = models.CharField(max_length=20, unique=True, blank=True)

    # 2. Tumefuta "umri", badala yake tunaweka "tarehe ya kuzaliwa"
    tarehe_ya_kuzaliwa = models.DateField(null=True, blank=True)

    mahala_anapoishi = models.CharField(max_length=100, null=True, blank=True)
    jina_la_mzazi = models.CharField(max_length=100, null=True, blank=True)
    namba_ya_simu_mzazi = models.CharField(max_length=15, null=True, blank=True)
    jinsia = models.CharField(max_length=2, choices=[('ME', 'Mwanamume (ME)'), ('KE', 'Mwanamke (KE)')], default='ME')
    darasa = models.ForeignKey(Darasa, on_delete=models.SET_NULL, null=True, blank=True)
    programu_ya_usiku = models.ForeignKey(Somo, on_delete=models.SET_NULL, null=True, blank=True, related_name='wanafunzi_usiku', help_text="Chagua kama anasoma usiku (Acha wazi kama hasomi usiku)")
    juzuu_aliyohifadhi = models.IntegerField(default=1)
    picha = models.ImageField(upload_to='picha_za_wanafunzi/', null=True, blank=True, validators=[validate_picha])
    tarehe_ya_kujiunga = models.DateField(auto_now_add=True)

    # 3. KODI YA KUPIGA HESABU YA UMRI AUTOMATIKI
    @property
    def umri(self):
        if self.tarehe_ya_kuzaliwa:
            leo = date.today()
            return leo.year - self.tarehe_ya_kuzaliwa.year - ((leo.month, leo.day) < (self.tarehe_ya_kuzaliwa.month, self.tarehe_ya_kuzaliwa.day))
        return "-"

    # 4. KODI YA KUTENGENEZA NAMBA MPYA ZA USAJILI (MR-001, MR-002...)
    def save(self, *args, **kwargs):
        if not self.namba_ya_usajili:
            mwanafunzi_wa_mwisho = Mwanafunzi.objects.all().order_by('id').last()
            if mwanafunzi_wa_mwisho and mwanafunzi_wa_mwisho.namba_ya_usajili.startswith('MR-'):
                try:
                    namba_ya_mwisho = int(mwanafunzi_wa_mwisho.namba_ya_usajili.split('-')[1])
                    namba_mpya = namba_ya_mwisho + 1
                except ValueError:
                    namba_mpya = 1
            else:
                namba_mpya = 1
            self.namba_ya_usajili = f"MR-{namba_mpya:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.namba_ya_usajili} - {self.jina_kamili}"

class Hudhurio(models.Model):
    mwanafunzi = models.ForeignKey(Mwanafunzi, on_delete=models.CASCADE)
    tarehe = models.DateField(auto_now_add=True)
    yupo = models.BooleanField(default=True)
    sababu_kama_hayupo = models.TextField(blank=True, null=True)
    aina_ya_rekodi = models.CharField(max_length=20, choices=[('Kawaida', 'Madrasa ya Kawaida'), ('Hifdhu', 'Somo la Hifdhu')], default='Kawaida')

    def __str__(self):
        hali = "Yupo" if self.yupo else "Hayupo"
        return f"{self.mwanafunzi.jina_kamili} - {self.tarehe} - {hali}"

class Tangazo(models.Model):
    kichwa_cha_habari = models.CharField(max_length=200)
    maelezo = models.TextField()
    tarehe_iliyotolewa = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.kichwa_cha_habari

# ==========================================
# MFUMO MPYA WA HIFDHU (SABAQ NA MAPANDE)
# ==========================================

class RekodiHifdhu(models.Model):
    mwanafunzi = models.ForeignKey(Mwanafunzi, on_delete=models.CASCADE)
    somo = models.ForeignKey(Somo, on_delete=models.CASCADE, null=True, blank=True)
    darasa = models.ForeignKey(Darasa, on_delete=models.CASCADE, null=True, blank=True)
    aina_ya_rekodi = models.CharField(max_length=20, choices=[('Darasa', 'Darasa'), ('Usiku', 'Usiku')], default='Usiku')
    mwalimu = models.ForeignKey(Mwalimu, on_delete=models.SET_NULL, null=True)
    tarehe = models.DateField(auto_now_add=True)

    sabaq_sura = models.CharField(max_length=50, blank=True, null=True)
    sabaq_aya_kuanzia = models.IntegerField(blank=True, null=True)
    sabaq_aya_kuishia = models.IntegerField(blank=True, null=True)
    sabaq_hali = models.CharField(max_length=30, choices=[
        ('Kajua', '✅ Kajua'),
        ('Hajajua', '❌ Hajajua'),
        ('Hajasikilizwa', '⏸️ Hajasikilizwa')
    ], blank=True, null=True)
    maoni_ya_mwalimu = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Sabaq ({self.aina_ya_rekodi}) ya {self.mwanafunzi.jina_kamili} - {self.tarehe}"

    class Meta:
        ordering = ['-tarehe']

class RekodiMaendeleoMchana(models.Model):
    mwanafunzi = models.ForeignKey(Mwanafunzi, on_delete=models.CASCADE)
    somo = models.ForeignKey(Somo, on_delete=models.CASCADE) # Mfano: Fiqhi
    mwalimu = models.ForeignKey(Mwalimu, on_delete=models.SET_NULL, null=True)
    tarehe = models.DateField(auto_now_add=True)

    mada_iliyosomwa = models.CharField(max_length=200, help_text="Mfano: Mlango wa Udhu")
    ukurasa_au_aya = models.CharField(max_length=50, blank=True, null=True)
    hali = models.CharField(max_length=20, choices=[
        ('Ameelewa', '✅ Ameelewa'),
        ('Hajaelewa', '❌ Hajaelewa'),
        ('Hajasikilizwa', '⏸️ Hajasikilizwa')
    ])
    maoni = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.somo.jina} - {self.mwanafunzi.jina_kamili}"


class PandeMurajaa(models.Model):
    rekodi = models.ForeignKey(RekodiHifdhu, on_delete=models.CASCADE, related_name='mapande')
    sura = models.CharField(max_length=50)
    aya_kuanzia = models.IntegerField(blank=True, null=True)
    aya_kuishia = models.IntegerField(blank=True, null=True)
    hali = models.CharField(max_length=20, choices=[
        ('Pasi', '✅ Pasi'),
        ('Makosa', '⚠️ Makosa Madogo'),
        ('Feli', '❌ Feli')
    ])

    def __str__(self):
        return f"Pande: {self.sura} - {self.rekodi.mwanafunzi.jina_kamili}"

# ==========================================
# NYENZO NA MITIHANI
# ==========================================

class Nyenzo(models.Model):
    somo = models.ForeignKey(Somo, on_delete=models.CASCADE)
    jina_la_faili = models.CharField(max_length=200)
    faili = models.FileField(upload_to='nyenzo_masomo/', validators=[validate_nyenzo])
    tarehe_iliyowekwa = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.jina_la_faili

class MsetoMtihani(models.Model):
    """Mseto wa mitihani ya muhula — unaunganisha mitihani ya masomo yote ya darasa."""
    darasa = models.ForeignKey(Darasa, on_delete=models.CASCADE, related_name='mseto_mitihani')
    jina = models.CharField(max_length=100, help_text="Mfano: Muhula wa 1 - 2026")
    tarehe = models.DateField(null=True, blank=True)
    maelezo = models.TextField(blank=True, null=True)
    tarehe_iliyoundwa = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-tarehe_iliyoundwa']
        verbose_name_plural = 'Mseto wa Mitihani'

    def __str__(self):
        return f"{self.jina} ({self.darasa.jina})"

class Mtihani(models.Model):
    somo = models.ForeignKey(Somo, on_delete=models.CASCADE)
    jina_la_mtihani = models.CharField(max_length=100)
    tarehe = models.DateField()
    mseto = models.ForeignKey(
        MsetoMtihani, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mitihani', help_text="Chagua mseto wa muhula ili matokeo yaingie kwenye ripoti ya jumla"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['somo', 'mseto'],
                condition=models.Q(mseto__isnull=False),
                name='unique_mtihani_per_somo_mseto',
            ),
        ]

    def __str__(self):
        return f"{self.jina_la_mtihani} - {self.somo.jina}"

class Matokeo(models.Model):
    mtihani = models.ForeignKey(Mtihani, on_delete=models.CASCADE)
    mwanafunzi = models.ForeignKey(Mwanafunzi, on_delete=models.CASCADE)
    maksi = models.FloatField()

    def __str__(self):
        return f"{self.mwanafunzi.jina_kamili} - {self.maksi}"

# ==========================================
# MFUMO WA MALIPO (FINANCE)
# ==========================================

class AinaMalipo(models.Model):
    jina = models.CharField(max_length=100, help_text="Mfano: Ada ya Mwezi Aprili, Mchango wa Mtihani")
    kiasi_kinachotakiwa = models.DecimalField(max_digits=10, decimal_places=2, help_text="Kiasi kamili kinachopaswa kulipwa")
    maelezo = models.TextField(blank=True, null=True)
    tarehe_ya_kuanzishwa = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.jina} - {self.kiasi_kinachotakiwa}/="

class Malipo(models.Model):
    mwanafunzi = models.ForeignKey(Mwanafunzi, on_delete=models.CASCADE, related_name='malipo_yote')
    aina_ya_malipo = models.ForeignKey(AinaMalipo, on_delete=models.CASCADE)
    kiasi_kilicholipwa = models.DecimalField(max_digits=10, decimal_places=2)
    tarehe_ya_malipo = models.DateField(auto_now_add=True)
    njia_ya_malipo = models.CharField(max_length=20, choices=[
        ('Cash', 'Pesa Taslimu (Cash)'),
        ('Simu', 'Simu / Benki')
    ], default='Cash')
    mpokeaji = models.ForeignKey(Mwalimu, on_delete=models.SET_NULL, null=True)
    maelezo_ya_ziada = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.mwanafunzi.jina_kamili} - {self.aina_ya_malipo.jina}"

    class Meta:
        ordering = ['-tarehe_ya_malipo']
