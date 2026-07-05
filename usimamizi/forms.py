from django import forms
from .models import Mwanafunzi, Nyenzo, Mtihani, MsetoMtihani


class MwanafunziForm(forms.ModelForm):
    class Meta:
        model = Mwanafunzi
        fields = [
            'jina_kamili', 'tarehe_ya_kuzaliwa', 'jinsia', 'darasa',
            'programu_ya_usiku', 'juzuu_aliyohifadhi', 'mahala_anapoishi',
            'jina_la_mzazi', 'namba_ya_simu_mzazi', 'picha',
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
            'namba_ya_simu_mzazi': 'Namba ya Simu ya Mzazi',
            'picha': 'Picha ya Mwanafunzi',
        }
        help_texts = {
            'picha': 'Formats: JPG, JPEG, PNG, WebP. Ukubwa usizidi 2MB.',
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


class MsetoMtihaniForm(forms.ModelForm):
    class Meta:
        model = MsetoMtihani
        fields = ['jina', 'tarehe', 'maelezo']
        widgets = {
            'tarehe': forms.DateInput(attrs={'type': 'date'}),
            'maelezo': forms.Textarea(attrs={'rows': 2}),
        }


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
            self.fields['mseto'].queryset = MsetoMtihani.objects.filter(darasa=darasa)
        else:
            self.fields['mseto'].queryset = MsetoMtihani.objects.none()
