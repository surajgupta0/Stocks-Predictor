from django import forms
from .models import Alert


class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ['stock', 'alert_type', 'condition', 'threshold', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(AlertForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'