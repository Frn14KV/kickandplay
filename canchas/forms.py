from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Evento, Reserva, Comentarios, UserProfile
from .models import Canchas

# -----------------------------------------------
# FORMULARIOS PARA EVENTOS Y RESERVAS
# -----------------------------------------------

class EventoForm(forms.ModelForm):
    """
    Formulario para crear o editar eventos.
    Permite gestionar el título, descripción y tipo de evento (público o privado).
    """
    class Meta:
        model = Evento
        fields = ['titulo', 'descripcion', 'tipo_evento']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo_evento': forms.Select(attrs={'class': 'form-control'}),
        }


class ReservaForm(forms.ModelForm):
    """
    Formulario para crear o editar reservas.
    Permite verificar conflictos en las horas de reserva.
    """
    class Meta:
        model = Reserva
        fields = ['cancha', 'fecha_reserva', 'hora_inicio', 'hora_fin', 'estado']
        widgets = {
            'cancha': forms.Select(attrs={'class': 'form-control'}),
            'fecha_reserva': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        """
        Valida los datos ingresados en el formulario:
        - Verifica que la hora de inicio sea menor que la hora de fin.
        - Verifica que la cancha no esté reservada en el mismo horario.
        """
        cleaned_data = super().clean()

        cancha = cleaned_data.get('cancha')
        fecha_reserva = cleaned_data.get('fecha_reserva')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')

        # Validación de horas
        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            raise forms.ValidationError("La hora de inicio debe ser anterior a la hora de fin.")

        # Validación de conflictos de reservas
        if Reserva.objects.filter(
            cancha=cancha,
            fecha_reserva=fecha_reserva,
            hora_inicio__lt=hora_fin,  # Empieza antes de que finalice la nueva
            hora_fin__gt=hora_inicio  # Finaliza después de que comience la nueva
        ).exists():
            raise forms.ValidationError("La cancha ya está reservada para este horario.")

        return cleaned_data

# -----------------------------------------------
# FORMULARIO PARA COMENTARIOS
# -----------------------------------------------

class ComentarioForm(forms.ModelForm):
    """
    Formulario para añadir comentarios a una cancha con calificación.
    """
    class Meta:
        model = Comentarios
        fields = ['texto', 'calificacion']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escribe tu comentario aquí...'
            }),
            'calificacion': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'texto': 'Comentario',
            'calificacion': 'Calificación',
        }

# -----------------------------------------------
# FORMULARIOS PARA USUARIOS Y PERFILES
# -----------------------------------------------

class RegistroForm(UserCreationForm):
    """
    Formulario para registrar nuevos usuarios.
    Incluye campos para email y contraseñas.
    """
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        """
        Personaliza el estilo de los campos del formulario.
        """
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class UserProfileForm(forms.ModelForm):
    """
    Formulario para editar el perfil del usuario (biografía, imagen de perfil, etc.).
    """
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_image', 'location', 'phone_number']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EditUserForm(forms.ModelForm):
    """
    Formulario para editar la información básica del usuario (nombre, apellido, email).
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# -----------------------------------------------
# FORMULARIO PERSONALIZADO DE LOGIN
# -----------------------------------------------

class CustomLoginForm(AuthenticationForm):
    """
    Personaliza el formulario de inicio de sesión con estilos y placeholders.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
            # Personaliza la etiqueta de cada campo
            field.label_tag = lambda: f'<label class="form-label" for="id_{field_name}">{field.label}</label>'


class CanchaForm(forms.ModelForm):
    class Meta:
        model = Canchas
        fields = ['nombre', 'direccion', 'capacidad', 'imagen_url', 'latitud', 'longitud']  # Campos editables

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Deshabilitamos el campo 'dueño' en el formulario
        self.fields['dueño'] = forms.CharField(
            initial=self.instance.dueño.username,  # Mostramos el nombre del dueño
            disabled=True,
            label="Dueño"
        )
