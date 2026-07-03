from django import forms
from .models import Nyenzo, Mtihani, MsetoMtihani


class NyenzoForm(forms.ModelForm):
    class Meta:
        model = Nyenzo
        fields = ['jina_la_faili', 'faili']


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
