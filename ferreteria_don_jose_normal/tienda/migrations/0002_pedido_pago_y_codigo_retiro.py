from django.db import migrations, models
import tienda.models


def completar_codigos(apps, schema_editor):
    Pedido = apps.get_model('tienda', 'Pedido')
    usados = set(Pedido.objects.exclude(codigo_retiro__isnull=True).values_list('codigo_retiro', flat=True))
    for pedido in Pedido.objects.filter(codigo_retiro__isnull=True).iterator():
        codigo = tienda.models.generar_codigo_retiro()
        while codigo in usados:
            codigo = tienda.models.generar_codigo_retiro()
        pedido.codigo_retiro = codigo
        pedido.save(update_fields=['codigo_retiro'])
        usados.add(codigo)


class Migration(migrations.Migration):
    dependencies = [
        ('tienda', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='codigo_retiro',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='pedido',
            name='metodo_pago',
            field=models.CharField(choices=[('tienda', 'Pagar al retirar'), ('tarjeta', 'Tarjeta')], default='tienda', max_length=20),
        ),
        migrations.AddField(
            model_name='pedido',
            name='estado_pago',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('pagado', 'Pagado'), ('rechazado', 'Rechazado')], default='pendiente', max_length=20),
        ),
        migrations.AddField(
            model_name='pedido',
            name='tarjeta_ultimos4',
            field=models.CharField(blank=True, max_length=4),
        ),
        migrations.AddField(
            model_name='pedido',
            name='referencia_pago',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.RunPython(completar_codigos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='pedido',
            name='codigo_retiro',
            field=models.CharField(default=tienda.models.generar_codigo_retiro, editable=False, max_length=20, unique=True),
        ),
    ]
