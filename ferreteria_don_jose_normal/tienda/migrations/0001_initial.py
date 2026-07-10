# Generated manually for the demo project
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=80, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=90, unique=True)),
            ],
            options={'verbose_name': 'Categoría', 'verbose_name_plural': 'Categorías', 'ordering': ['nombre']},
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120)),
                ('descripcion', models.TextField(blank=True)),
                ('precio', models.DecimalField(decimal_places=0, max_digits=10)),
                ('stock', models.PositiveIntegerField(default=0)),
                ('icono', models.CharField(default='🧰', help_text='Emoji o símbolo corto', max_length=10)),
                ('imagen', models.ImageField(blank=True, null=True, upload_to='productos/')),
                ('activo', models.BooleanField(default=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='productos', to='tienda.categoria')),
            ],
            options={'ordering': ['nombre']},
        ),
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cliente_nombre', models.CharField(max_length=120)),
                ('cliente_telefono', models.CharField(max_length=30)),
                ('observacion', models.TextField(blank=True)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('confirmado', 'Confirmado'), ('entregado', 'Entregado'), ('cancelado', 'Cancelado')], default='pendiente', max_length=20)),
                ('total', models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ('stock_descontado', models.BooleanField(default=False)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-creado_en']},
        ),
        migrations.CreateModel(
            name='ItemPedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField(default=1)),
                ('precio_unitario', models.DecimalField(decimal_places=0, max_digits=10)),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='tienda.pedido')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='tienda.producto')),
            ],
        ),
    ]
