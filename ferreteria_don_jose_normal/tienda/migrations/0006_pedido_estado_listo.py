from django.db import migrations, models


def convertir_pagados_en_pendientes(apps, schema_editor):
    Pedido = apps.get_model('tienda', 'Pedido')
    Pedido.objects.filter(estado='pagado').update(estado='pendiente')


def revertir_listos(apps, schema_editor):
    Pedido = apps.get_model('tienda', 'Pedido')
    Pedido.objects.filter(estado='listo').update(estado='pendiente')


class Migration(migrations.Migration):
    dependencies = [
        ('tienda', '0005_pedido_estado_pagado'),
    ]

    operations = [
        migrations.RunPython(convertir_pagados_en_pendientes, revertir_listos),
        migrations.AlterField(
            model_name='pedido',
            name='estado',
            field=models.CharField(
                choices=[
                    ('pendiente', 'Pendiente'),
                    ('listo', 'Pedido listo'),
                    ('entregado', 'Entregado'),
                    ('cancelado', 'Cancelado'),
                ],
                default='pendiente',
                max_length=20,
            ),
        ),
    ]
