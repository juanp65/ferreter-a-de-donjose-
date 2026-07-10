import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils import timezone

from .models import Pedido, Producto


def _luhn_valido(numero):
    total = 0
    invertir = numero[::-1]
    for indice, caracter in enumerate(invertir):
        digito = int(caracter)
        if indice % 2 == 1:
            digito *= 2
            if digito > 9:
                digito -= 9
        total += digito
    return total % 10 == 0


def _normalizar_rut(rut):
    limpio = re.sub(r'[^0-9kK]', '', rut or '').upper()
    if len(limpio) < 2:
        return limpio
    cuerpo, dv = limpio[:-1], limpio[-1]
    cuerpo_formateado = f'{int(cuerpo):,}'.replace(',', '.') if cuerpo.isdigit() else cuerpo
    return f'{cuerpo_formateado}-{dv}'


def _rut_valido(rut):
    limpio = re.sub(r'[^0-9kK]', '', rut or '').upper()
    if len(limpio) < 2 or not limpio[:-1].isdigit():
        return False
    cuerpo, dv = limpio[:-1], limpio[-1]
    suma = 0
    factor = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1
    resultado = 11 - (suma % 11)
    esperado = '0' if resultado == 11 else 'K' if resultado == 10 else str(resultado)
    return dv == esperado


class InicioSesionForm(AuthenticationForm):
    username = forms.CharField(
        label='Correo o usuario',
        widget=forms.TextInput(attrs={
            'placeholder': 'correo@ejemplo.cl o 219370237',
            'autocomplete': 'username',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Ingresa tu contraseña',
            'autocomplete': 'current-password',
        }),
    )


class RegistroClienteForm(UserCreationForm):
    first_name = forms.CharField(
        label='Nombre',
        max_length=80,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej.: María González',
            'autocomplete': 'name',
        }),
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'placeholder': 'correo@ejemplo.cl',
            'autocomplete': 'email',
        }),
    )
    password1 = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Crea una contraseña',
            'autocomplete': 'new-password',
        }),
    )
    password2 = forms.CharField(
        label='Repite la contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repite la contraseña',
            'autocomplete': 'new-password',
        }),
    )

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        User = get_user_model()
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta asociada a este correo.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        user.username = email
        user.email = email
        user.first_name = self.cleaned_data['first_name'].strip()
        if commit:
            user.save()
        return user


class PedidoForm(forms.Form):
    cliente_nombre = forms.CharField(
        label='Nombre',
        max_length=120,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej.: María González',
            'autocomplete': 'name',
        }),
    )
    cliente_telefono = forms.CharField(
        label='Teléfono / WhatsApp',
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej.: 9 1234 5678',
            'autocomplete': 'tel',
            'inputmode': 'tel',
        }),
    )
    tipo_documento = forms.ChoiceField(
        label='Documento tributario',
        choices=Pedido.TIPOS_DOCUMENTO,
        initial='boleta',
        required=False,
        widget=forms.RadioSelect,
    )
    factura_rut = forms.CharField(
        label='RUT de la empresa',
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej.: 76.123.456-7',
            'autocomplete': 'off',
        }),
    )
    factura_razon_social = forms.CharField(
        label='Razón social',
        required=False,
        max_length=160,
        widget=forms.TextInput(attrs={'placeholder': 'Nombre legal de la empresa'}),
    )
    factura_giro = forms.CharField(
        label='Giro',
        required=False,
        max_length=160,
        widget=forms.TextInput(attrs={'placeholder': 'Actividad comercial'}),
    )
    factura_direccion = forms.CharField(
        label='Dirección',
        required=False,
        max_length=220,
        widget=forms.TextInput(attrs={'placeholder': 'Calle, número y comuna'}),
    )
    factura_email = forms.EmailField(
        label='Correo para la factura',
        required=False,
        widget=forms.EmailInput(attrs={
            'placeholder': 'facturacion@empresa.cl',
            'autocomplete': 'email',
        }),
    )
    metodo_pago = forms.ChoiceField(
        label='Forma de pago',
        choices=Pedido.METODOS_PAGO,
        initial='tienda',
        widget=forms.RadioSelect,
    )
    titular_tarjeta = forms.CharField(
        label='Nombre del titular',
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={
            'placeholder': 'Como aparece en la tarjeta',
            'autocomplete': 'cc-name',
        }),
    )
    numero_tarjeta = forms.CharField(
        label='Número de tarjeta',
        required=False,
        max_length=23,
        widget=forms.TextInput(attrs={
            'placeholder': '1234 5678 9012 3456',
            'autocomplete': 'cc-number',
            'inputmode': 'numeric',
            'pattern': '[0-9 ]*',
            'maxlength': '23',
            'aria-describedby': 'card-number-help card-brand-status',
        }),
    )
    vencimiento_tarjeta = forms.CharField(
        label='Vencimiento',
        required=False,
        max_length=5,
        widget=forms.TextInput(attrs={
            'placeholder': 'MM/AA',
            'autocomplete': 'cc-exp',
            'inputmode': 'numeric',
        }),
    )
    cvv_tarjeta = forms.CharField(
        label='CVV',
        required=False,
        max_length=4,
        widget=forms.PasswordInput(render_value=False, attrs={
            'placeholder': '123',
            'autocomplete': 'cc-csc',
            'inputmode': 'numeric',
        }),
    )
    observacion = forms.CharField(
        label='Observación',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Horario de retiro, consulta o detalle adicional',
        }),
    )

    def clean(self):
        cleaned = super().clean()
        cleaned['tipo_documento'] = cleaned.get('tipo_documento') or 'boleta'

        if cleaned.get('tipo_documento') == 'factura':
            campos_factura = {
                'factura_rut': 'Ingresa el RUT para la factura.',
                'factura_razon_social': 'Ingresa la razón social.',
                'factura_giro': 'Ingresa el giro.',
                'factura_direccion': 'Ingresa la dirección de facturación.',
                'factura_email': 'Ingresa el correo para la factura.',
            }
            for campo, mensaje in campos_factura.items():
                if not cleaned.get(campo):
                    self.add_error(campo, mensaje)

            rut = cleaned.get('factura_rut', '')
            if rut and not _rut_valido(rut):
                self.add_error('factura_rut', 'Ingresa un RUT chileno válido.')
            elif rut:
                cleaned['factura_rut'] = _normalizar_rut(rut)
        else:
            for campo in ('factura_rut', 'factura_razon_social', 'factura_giro', 'factura_direccion', 'factura_email'):
                cleaned[campo] = ''

        if cleaned.get('metodo_pago') != 'tarjeta':
            return cleaned

        campos_requeridos = {
            'titular_tarjeta': 'Ingresa el nombre del titular.',
            'numero_tarjeta': 'Ingresa el número de la tarjeta.',
            'vencimiento_tarjeta': 'Ingresa la fecha de vencimiento.',
            'cvv_tarjeta': 'Ingresa el código CVV.',
        }
        for campo, mensaje in campos_requeridos.items():
            if not cleaned.get(campo):
                self.add_error(campo, mensaje)

        numero_original = (cleaned.get('numero_tarjeta') or '').strip()
        if numero_original and not re.fullmatch(r'[0-9 ]+', numero_original):
            self.add_error('numero_tarjeta', 'El número de tarjeta solo puede contener números.')

        numero = re.sub(r'\s', '', numero_original)
        if numero and not (13 <= len(numero) <= 19):
            self.add_error('numero_tarjeta', 'El número de tarjeta debe tener entre 13 y 19 dígitos.')
        cleaned['numero_tarjeta'] = numero

        cvv = re.sub(r'\D', '', cleaned.get('cvv_tarjeta', ''))
        if cvv and len(cvv) not in (3, 4):
            self.add_error('cvv_tarjeta', 'El CVV debe tener 3 o 4 dígitos.')
        cleaned['cvv_tarjeta'] = cvv

        vencimiento = cleaned.get('vencimiento_tarjeta', '').strip()
        coincidencia = re.fullmatch(r'(0[1-9]|1[0-2])/(\d{2})', vencimiento)
        if vencimiento and not coincidencia:
            self.add_error('vencimiento_tarjeta', 'Usa el formato MM/AA.')
        elif coincidencia:
            mes = int(coincidencia.group(1))
            anio = 2000 + int(coincidencia.group(2))
            hoy = timezone.localdate()
            if (anio, mes) < (hoy.year, hoy.month):
                self.add_error('vencimiento_tarjeta', 'La tarjeta está vencida.')

        return cleaned


class ProductoForm(forms.ModelForm):
    eliminar_imagen = forms.BooleanField(
        required=False,
        label='Quitar imagen actual',
    )

    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'precio', 'stock', 'descripcion', 'imagen', 'activo']
        labels = {
            'nombre': 'Nombre del producto',
            'categoria': 'Categoría',
            'precio': 'Precio de venta (IVA incluido)',
            'stock': 'Cantidad disponible',
            'descripcion': 'Descripción breve',
            'imagen': 'Imagen del producto',
            'activo': 'Mostrar producto en la tienda',
        }
        help_texts = {
            'descripcion': 'Opcional. Puedes agregar una descripción corta.',
            'imagen': 'Sube una fotografía clara del producto. Se recomienda una imagen cuadrada.',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej.: Cemento 50 kg',
                'autocomplete': 'off',
                'autofocus': True,
            }),
            'categoria': forms.Select(),
            'precio': forms.NumberInput(attrs={
                'placeholder': 'Ej.: 7500',
                'min': 0,
                'step': 1,
                'inputmode': 'numeric',
            }),
            'stock': forms.NumberInput(attrs={
                'placeholder': 'Ej.: 20',
                'min': 0,
                'step': 1,
                'inputmode': 'numeric',
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Ej.: Producto disponible para retiro en tienda.',
            }),
            'imagen': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'native-file-input',
            }),
            'activo': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].empty_label = 'Selecciona una categoría'
        if not self.instance.pk:
            self.fields['activo'].initial = True

    def save(self, commit=True):
        producto = super().save(commit=False)
        if (
            self.cleaned_data.get('eliminar_imagen')
            and not self.cleaned_data.get('imagen')
            and producto.imagen
        ):
            producto.imagen.delete(save=False)
            producto.imagen = None
        if commit:
            producto.save()
            self.save_m2m()
        return producto
