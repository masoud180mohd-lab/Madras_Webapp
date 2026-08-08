from io import BytesIO
from pathlib import Path
from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction

from .academic import get_active_muhula
from .models import (
    AinaMalipo,
    Darasa,
    Hudhurio,
    Malipo,
    Muhula,
    MwakaWaMasomo,
    Mwalimu,
    Mwanafunzi,
    Nyenzo,
    Mtihani,
    MsetoMtihani,
    PandeMurajaa,
    RekodiHifdhu,
    RekodiMaendeleoMchana,
    RekodiSimuMzazi,
    validate_picha,
)

User = get_user_model()

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover - Pillow is expected, but we fail softly.
    Image = None
    ImageOps = None


class MwanafunziForm(forms.ModelForm):
    class Meta:
        model = Mwanafunzi
        fields = [
            'jina_kamili', 'tarehe_ya_kuzaliwa', 'jinsia', 'darasa',
            'programu_ya_usiku', 'juzuu_aliyohifadhi', 'mahala_anapoishi',
            'jina_la_mzazi', 'uhusiano_wa_mlezi', 'namba_ya_simu_mzazi', 'picha',
        ]
        labels = {
            'jina_kamili': 'Jina Kamili',
            'tarehe_ya_kuzaliwa': 'Tarehe ya Kuzaliwa',
            'jinsia': 'Jinsia',
            'darasa': 'Darasa / Ngazi',
            'programu_ya_usiku': 'Programu ya Usiku',
            'juzuu_aliyohifadhi': 'Juzuu Aliyohifadhi',
            'mahala_anapoishi': 'Mahala Anapoishi',
            'jina_la_mzazi': 'Jina la Mzazi / Mlezi',
            'uhusiano_wa_mlezi': 'Uhusiano',
            'namba_ya_simu_mzazi': 'Namba ya Simu ya Mzazi',
            'picha': 'Picha ya Mwanafunzi',
        }
        help_texts = {
            'picha': 'Formats: JPG, JPEG, PNG, WebP. Ukubwa usizidi 0.5MB.',
        }
        widgets = {
            'tarehe_ya_kuzaliwa': forms.DateInput(attrs={'type': 'date'}),
            'picha': forms.ClearableFileInput(attrs={'accept': '.jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['programu_ya_usiku'].required = False
        self.fields['programu_ya_usiku'].empty_label = '-- Hana programu ya usiku --'
        self.fields['darasa'].required = False
        self.fields['darasa'].empty_label = '-- Hajapangiwa darasa --'
        self.fields['picha'].validators = []

    def clean_picha(self):
        picha = self.cleaned_data.get('picha')
        if not picha:
            return picha
        if Image is None:
            validate_picha(picha)
            return picha

        try:
            picha.seek(0)
            original = Image.open(picha)
            original = ImageOps.exif_transpose(original)
            original.thumbnail((1600, 1600), Image.LANCZOS)

            extension = Path(picha.name).suffix.lower().lstrip(".")
            if extension in {"jpg", "jpeg"}:
                extension = "jpg"
                if original.mode not in ("RGB",):
                    original = original.convert("RGB")
                content_type = "image/jpeg"
                save_kwargs = {"format": "JPEG", "quality": 82, "optimize": True, "progressive": True}
            elif extension == "png":
                content_type = "image/png"
                save_kwargs = {"format": "PNG", "optimize": True, "compress_level": 9}
            elif extension == "webp":
                content_type = "image/webp"
                save_kwargs = {"format": "WEBP", "quality": 82, "method": 6}
            else:
                return picha

            output = BytesIO()
            original.save(output, **save_kwargs)
            output.seek(0)
            new_name = f"{Path(picha.name).stem}.{extension}"
            compressed = SimpleUploadedFile(new_name, output.read(), content_type=content_type)
            validate_picha(compressed)
            return compressed
        except Exception:
            picha.seek(0)
            validate_picha(picha)
            return picha


class NyenzoForm(forms.ModelForm):
    class Meta:
        model = Nyenzo
        fields = ['jina_la_faili', 'faili']
        help_texts = {
            'faili': 'Formats: PDF, DOC/DOCX, PPT/PPTX, XLS/XLSX, TXT, JPG, PNG, WebP. Ukubwa usizidi 10MB.',
        }
        widgets = {
            'faili': forms.ClearableFileInput(attrs={
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.jpg,.jpeg,.png,.webp'
            }),
        }


class MwakaWaMasomoForm(forms.ModelForm):
    class Meta:
        model = MwakaWaMasomo
        fields = [
            "jina",
            "mwaka_kuanzia",
            "mwaka_kuisha",
            "tarehe_kuanzia",
            "tarehe_kuisha",
            "ni_hai",
        ]
        widgets = {
            "tarehe_kuanzia": forms.DateInput(attrs={"type": "date"}),
            "tarehe_kuisha": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("mwaka_kuanzia")
        end = cleaned.get("mwaka_kuisha")
        if start and end and end < start:
            self.add_error("mwaka_kuisha", "Mwaka wa kuisha hawezi kuwa kabla ya kuanza.")
        # Clear other active years before UniqueConstraint validation on this instance.
        if cleaned.get("ni_hai"):
            others = MwakaWaMasomo.objects.filter(ni_hai=True)
            if self.instance.pk:
                others = others.exclude(pk=self.instance.pk)
            others.update(ni_hai=False)
        return cleaned


class MuhulaForm(forms.ModelForm):
    class Meta:
        model = Muhula
        fields = [
            "mwaka",
            "namba",
            "jina",
            "tarehe_kuanzia",
            "tarehe_kuisha",
            "ni_hai",
        ]
        widgets = {
            "tarehe_kuanzia": forms.DateInput(attrs={"type": "date"}),
            "tarehe_kuisha": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("ni_hai"):
            others = Muhula.objects.filter(ni_hai=True)
            if self.instance.pk:
                others = others.exclude(pk=self.instance.pk)
            others.update(ni_hai=False)
        return cleaned


class MsetoMtihaniForm(forms.ModelForm):
    class Meta:
        model = MsetoMtihani
        fields = ["jina", "muhula", "tarehe", "maelezo"]
        widgets = {
            "tarehe": forms.DateInput(attrs={"type": "date"}),
            "maelezo": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["muhula"].queryset = Muhula.objects.select_related("mwaka").order_by(
            "-mwaka__mwaka_kuanzia", "namba"
        )
        self.fields["muhula"].required = False
        self.fields["muhula"].empty_label = "-- Chagua muhula (hiari) --"
        active = get_active_muhula()
        if active and not self.is_bound and not self.instance.pk:
            self.initial.setdefault("muhula", active.pk)
            self.initial.setdefault("jina", f"{active.jina} · {active.mwaka.jina}")


class MtihaniForm(forms.ModelForm):
    class Meta:
        model = Mtihani
        fields = ['jina_la_mtihani', 'tarehe', 'mseto']
        widgets = {
            'tarehe': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, darasa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mseto'].required = False
        self.fields['mseto'].empty_label = '-- Hakuna (Mtihani peke yake) --'
        if darasa:
            qs = (
                MsetoMtihani.objects.filter(darasa=darasa)
                .select_related("muhula", "muhula__mwaka")
                .order_by("-muhula__mwaka__mwaka_kuanzia", "-muhula__namba", "-id")
            )
            self.fields['mseto'].queryset = qs
        else:
            self.fields['mseto'].queryset = MsetoMtihani.objects.none()


class MawasilianoContactForm(forms.ModelForm):
    """Hariri haraka mawasiliano ya mzazi (ofisi)."""

    class Meta:
        model = Mwanafunzi
        fields = ["jina_la_mzazi", "uhusiano_wa_mlezi", "namba_ya_simu_mzazi"]
        labels = {
            "jina_la_mzazi": "Jina la mzazi / mlezi",
            "uhusiano_wa_mlezi": "Uhusiano",
            "namba_ya_simu_mzazi": "Namba ya simu",
        }
        widgets = {
            "jina_la_mzazi": forms.TextInput(attrs={"class": "app-input"}),
            "uhusiano_wa_mlezi": forms.Select(attrs={"class": "app-input"}),
            "namba_ya_simu_mzazi": forms.TextInput(
                attrs={"class": "app-input", "inputmode": "tel"}
            ),
        }


class RekodiSimuMzaziForm(forms.ModelForm):
    class Meta:
        model = RekodiSimuMzazi
        fields = ["namba_iliyopigwa", "sababu", "matokeo", "maelezo", "tarehe_ya_simu"]
        labels = {
            "namba_iliyopigwa": "Namba iliyopigwa",
            "sababu": "Sababu ya simu",
            "matokeo": "Matokeo",
            "maelezo": "Maelezo / ahadi",
            "tarehe_ya_simu": "Tarehe na saa",
        }
        widgets = {
            "namba_iliyopigwa": forms.TextInput(
                attrs={"class": "app-input", "inputmode": "tel"}
            ),
            "sababu": forms.Select(attrs={"class": "app-input"}),
            "matokeo": forms.Select(attrs={"class": "app-input"}),
            "maelezo": forms.Textarea(attrs={"class": "app-input", "rows": 3}),
            "tarehe_ya_simu": forms.DateTimeInput(
                attrs={"class": "app-input", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, mwanafunzi=None, **kwargs):
        from django.utils import timezone as dj_tz

        super().__init__(*args, **kwargs)
        self.fields["tarehe_ya_simu"].input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]
        if not self.is_bound:
            if mwanafunzi:
                self.fields["namba_iliyopigwa"].initial = (
                    mwanafunzi.namba_ya_simu_mzazi or ""
                )
            if not getattr(self.instance, "pk", None):
                self.fields["tarehe_ya_simu"].initial = dj_tz.localtime(
                    dj_tz.now()
                ).strftime("%Y-%m-%dT%H:%M")


class DarasaForm(forms.ModelForm):
    class Meta:
        model = Darasa
        fields = ["jina", "maelezo"]
        widgets = {
            "jina": forms.TextInput(attrs={"class": "app-input"}),
            "maelezo": forms.Textarea(attrs={"class": "app-input", "rows": 3}),
        }


class AinaMalipoForm(forms.ModelForm):
    class Meta:
        model = AinaMalipo
        fields = ["jina", "kiasi_kinachotakiwa", "maelezo"]
        widgets = {
            "jina": forms.TextInput(attrs={"class": "app-input"}),
            "kiasi_kinachotakiwa": forms.NumberInput(
                attrs={"class": "app-input", "step": "0.01", "min": "0"}
            ),
            "maelezo": forms.Textarea(attrs={"class": "app-input", "rows": 3}),
        }


class MwalimuCreateForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Jina la akaunti",
        widget=forms.TextInput(attrs={"class": "app-input", "autocomplete": "username"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "app-input", "autocomplete": "new-password"}
        ),
        label="Nenosiri",
        strip=False,
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label="Jina la kwanza",
        widget=forms.TextInput(attrs={"class": "app-input"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Jina la ukoo",
        widget=forms.TextInput(attrs={"class": "app-input"}),
    )
    cheo = forms.ChoiceField(
        choices=Mwalimu._meta.get_field("cheo").choices,
        label="Cheo",
        widget=forms.Select(attrs={"class": "app-input"}),
    )
    namba_ya_simu = forms.CharField(
        max_length=15,
        required=False,
        label="Namba ya simu",
        widget=forms.TextInput(attrs={"class": "app-input"}),
    )
    picha = forms.ImageField(required=False, label="Picha", validators=[validate_picha])

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Jina la akaunti linatumika tayari.")
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self):
        data = self.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(
                username=data["username"],
                password=data["password"],
                first_name=data.get("first_name") or "",
                last_name=data.get("last_name") or "",
            )
            mwalimu = Mwalimu(
                user=user,
                cheo=data["cheo"],
                namba_ya_simu=data.get("namba_ya_simu") or None,
            )
            if data.get("picha"):
                mwalimu.picha = data["picha"]
            mwalimu.save()
        return mwalimu


class MwalimuEditForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label="Jina la kwanza",
        widget=forms.TextInput(attrs={"class": "app-input"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Jina la ukoo",
        widget=forms.TextInput(attrs={"class": "app-input"}),
    )
    is_active = forms.BooleanField(
        required=False,
        label="Akaunti hai (inaweza kuingia)",
        help_text="Ondoa tiki ili kumzuia mwalimu kuingia bila kufuta akaunti.",
    )

    class Meta:
        model = Mwalimu
        fields = ["cheo", "namba_ya_simu", "picha"]
        labels = {
            "cheo": "Cheo",
            "namba_ya_simu": "Namba ya simu",
            "picha": "Picha",
        }
        widgets = {
            "cheo": forms.Select(attrs={"class": "app-input"}),
            "namba_ya_simu": forms.TextInput(attrs={"class": "app-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance.user
        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name
        self.fields["is_active"].initial = user.is_active
        if "picha" in self.fields:
            self.fields["picha"].required = False
            self.fields["picha"].validators = [validate_picha]

    def save(self, commit=True):
        mwalimu = super().save(commit=False)
        user = mwalimu.user
        user.first_name = self.cleaned_data.get("first_name") or ""
        user.last_name = self.cleaned_data.get("last_name") or ""
        user.is_active = bool(self.cleaned_data.get("is_active"))
        if commit:
            user.save()
            mwalimu.save()
        return mwalimu


class MalipoForm(forms.Form):
    """Pokea malipo — field names match existing template inputs."""

    kiasi = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        error_messages={
            "required": "Weka kiasi cha malipo.",
            "min_value": "Kiasi lazima kiwe zaidi ya sifuri.",
            "invalid": "Kiasi si sahihi.",
        },
    )
    njia = forms.ChoiceField(
        choices=Malipo._meta.get_field("njia_ya_malipo").choices,
        error_messages={"required": "Chagua njia ya malipo.", "invalid_choice": "Njia si sahihi."},
    )
    maelezo = forms.CharField(required=False, max_length=2000)

    def __init__(self, *args, max_kiasi=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_kiasi = max_kiasi

    def clean_kiasi(self):
        kiasi = self.cleaned_data["kiasi"]
        if self.max_kiasi is not None and kiasi > self.max_kiasi:
            raise forms.ValidationError(
                f"Hawezi kulipa zaidi ya deni (Tsh {self.max_kiasi}/=)."
            )
        return kiasi


class MaendeleoMchanaForm(forms.ModelForm):
    class Meta:
        model = RekodiMaendeleoMchana
        fields = ["mada_iliyosomwa", "ukurasa_au_aya", "hali", "maoni"]
        labels = {
            "mada_iliyosomwa": "Mada iliyosomwa",
            "ukurasa_au_aya": "Ukurasa / aya",
            "hali": "Tathmini",
            "maoni": "Maoni ya mwalimu",
        }
        widgets = {
            "mada_iliyosomwa": forms.TextInput(
                attrs={
                    "class": "app-input custom-input",
                    "placeholder": "Mf. Mlango wa Udhu",
                }
            ),
            "ukurasa_au_aya": forms.TextInput(
                attrs={
                    "class": "app-input custom-input",
                    "placeholder": "Mf. uk. 12–15",
                }
            ),
            "hali": forms.RadioSelect,
            "maoni": forms.Textarea(
                attrs={"class": "app-input custom-input", "rows": 3}
            ),
        }


class SabaqRekodiForm(forms.Form):
    sabaq_sura = forms.CharField(required=False, max_length=50)
    sabaq_aya_kuanzia = forms.IntegerField(required=False, min_value=1)
    sabaq_aya_kuishia = forms.IntegerField(required=False, min_value=1)
    sabaq_hali = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + list(RekodiHifdhu._meta.get_field("sabaq_hali").choices),
    )
    maoni = forms.CharField(required=False, max_length=2000)

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("sabaq_aya_kuanzia")
        end = cleaned.get("sabaq_aya_kuishia")
        if start is not None and end is not None and end < start:
            self.add_error("sabaq_aya_kuishia", "Aya ya kuishia haiwezi kuwa chini ya kuanzia.")
        return cleaned


def parse_mapande_from_post(post_data):
    """Validate murajaa rows from the dynamic sabaq template lists."""
    sura_list = post_data.getlist("pande_sura[]")
    kuanzia_list = post_data.getlist("pande_aya_kuanzia[]")
    kuishia_list = post_data.getlist("pande_aya_kuishia[]")
    hali_list = post_data.getlist("pande_hali[]")
    valid_hali = {c[0] for c in PandeMurajaa._meta.get_field("hali").choices}

    rows = []
    errors = []
    for i, sura in enumerate(sura_list):
        sura = (sura or "").strip()
        if not sura:
            continue
        hali = hali_list[i] if i < len(hali_list) else ""
        if hali not in valid_hali:
            errors.append(f"Hali ya pande '{sura}' si sahihi.")
            continue
        kuanzia = kuanzia_list[i] if i < len(kuanzia_list) else ""
        kuishia = kuishia_list[i] if i < len(kuishia_list) else ""
        try:
            aya_kuanzia = int(kuanzia) if str(kuanzia).strip() else None
            aya_kuishia = int(kuishia) if str(kuishia).strip() else None
        except (TypeError, ValueError):
            errors.append(f"Aya za pande '{sura}' si namba sahihi.")
            continue
        if aya_kuanzia is not None and aya_kuanzia < 1:
            errors.append(f"Aya kuanzia ya '{sura}' lazima iwe ≥ 1.")
            continue
        if aya_kuishia is not None and aya_kuanzia is not None and aya_kuishia < aya_kuanzia:
            errors.append(f"Aya kuishia ya '{sura}' haiwezi kuwa chini ya kuanzia.")
            continue
        rows.append(
            {
                "sura": sura,
                "aya_kuanzia": aya_kuanzia,
                "aya_kuishia": aya_kuishia,
                "hali": hali,
            }
        )
    return rows, errors


def parse_maksi_post(wanafunzi, post_data):
    """Parse maksi_<id> fields; return {mwanafunzi_id: float} and error messages."""
    scores = {}
    errors = []
    for mwanafunzi in wanafunzi:
        raw = (post_data.get(f"maksi_{mwanafunzi.id}") or "").strip()
        if not raw:
            continue
        try:
            value = float(raw)
        except ValueError:
            errors.append(f"Maksi ya {mwanafunzi.jina_kamili} si namba sahihi.")
            continue
        if value < 0 or value > 100:
            errors.append(f"Maksi ya {mwanafunzi.jina_kamili} lazima iwe kati ya 0 na 100.")
            continue
        scores[mwanafunzi.id] = value
    return scores, errors


def build_hudhurio_rows(wanafunzi, post_data, *, aina_ya_rekodi, tarehe, iliyorekodiwa_na=None):
    """Build Hudhurio instances for bulk_create from attendance grid POST."""
    rows = []
    for mwanafunzi in wanafunzi:
        yupo = post_data.get(f"yupo_{mwanafunzi.id}") == "on"
        sababu = (post_data.get(f"sababu_{mwanafunzi.id}") or "").strip()
        if yupo:
            sababu = ""
        rows.append(
            Hudhurio(
                mwanafunzi=mwanafunzi,
                yupo=yupo,
                sababu_kama_hayupo=sababu or None,
                aina_ya_rekodi=aina_ya_rekodi,
                tarehe=tarehe,
                iliyorekodiwa_na=iliyorekodiwa_na,
            )
        )
    return rows
