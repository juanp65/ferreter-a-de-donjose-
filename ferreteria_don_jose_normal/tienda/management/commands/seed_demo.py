from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from tienda.models import Categoria, Producto


class Command(BaseCommand):
    help = 'Crea datos de demostración para Ferretería Don José.'

    def handle(self, *args, **options):
        datos = {
            'Pinturas': [
                ('Pintura látex 20 L', 45000, 15),
            ],
            'Herramientas': [
                ('Taladro eléctrico', 65000, 8),
            ],
            'Materiales': [
                ('Cemento 50 kg', 7500, 22),
            ],
            'Plomería': [
                ('Tubo PVC 110 mm', 3200, 0),
            ],
            'Ferretería': [
                ('Tornillo 2 pulgadas', 150, 120),
                ('Martillo carpintero', 12990, 6),
            ],
        }

        for categoria_nombre, productos in datos.items():
            categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
            for nombre, precio, stock in productos:
                Producto.objects.get_or_create(
                    nombre=nombre,
                    defaults={
                        'categoria': categoria,
                        'precio': precio,
                        'stock': stock,
                        'descripcion': 'Producto disponible en Ferretería Don José.',
                    },
                )

        User = get_user_model()

        # Crea o actualiza la cuenta administrativa de Don José.
        usuario = User.objects.filter(username='219370237').first()
        if usuario is None:
            usuario = User.objects.filter(username='donjose').first()
            if usuario is None:
                usuario = User(username='219370237')
            else:
                usuario.username = '219370237'

        usuario.first_name = 'Don José'
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.is_active = True
        usuario.set_password('1905')
        usuario.save()
        self.stdout.write(self.style.SUCCESS('Acceso de Don José actualizado: 219370237 / 1905'))


        cliente, cliente_creado = User.objects.get_or_create(
            username='cliente@demo.cl',
            defaults={
                'email': 'cliente@demo.cl',
                'first_name': 'Cliente Demo',
            },
        )
        if cliente_creado:
            cliente.set_password('Cliente123!')
            cliente.save()
            self.stdout.write(self.style.SUCCESS('Cliente creado: cliente@demo.cl / Cliente123!'))
        else:
            self.stdout.write('El cliente de demostración ya existía; no se cambió su contraseña.')

        self.stdout.write(self.style.SUCCESS('Datos de demostración cargados correctamente.'))
