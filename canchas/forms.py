from django import forms
from .models import Evento, Reserva

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['titulo', 'descripcion', 'fecha', 'hora_inicio', 'hora_fin', 'cancha']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del Evento',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del Evento',
                'rows': 3,
            }),
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),
            'hora_inicio': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
            }),
            'hora_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
            }),
            'cancha': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            raise forms.ValidationError("La hora de inicio debe ser antes que la hora de fin.")
        return cleaned_data

    def __init__(self, *args, **kwargs):
        cancha = kwargs.pop('cancha', None)  # Recupera la cancha del contexto
        super().__init__(*args, **kwargs)

        if cancha:
            self.fields['cancha'].initial = cancha
            self.fields['cancha'].widget.attrs['readonly'] = True  # Alternativamente: disabled


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['cancha', 'fecha_reserva', 'hora_inicio', 'hora_fin']
        widgets = {
            'fecha_reserva': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        cancha = cleaned_data.get('cancha')
        fecha_reserva = cleaned_data.get('fecha_reserva')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')

        # Verificar que la hora de inicio sea menor que la hora de fin
        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            raise forms.ValidationError("La hora de inicio debe ser anterior a la hora de fin.")

        # Verificar si la cancha ya está reservada en ese rango de tiempo
        if Reserva.objects.filter(
            cancha=cancha,
            fecha_reserva=fecha_reserva,
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio
        ).exists():
            raise forms.ValidationError("La cancha ya está reservada para este horario.")

        return cleaned_data