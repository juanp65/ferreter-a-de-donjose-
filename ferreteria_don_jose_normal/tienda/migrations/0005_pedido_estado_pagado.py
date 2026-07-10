from django.db import migrations, models


def convertir_confirmados_en_pagados(apps, schema_editor):
    Pedido = apps.get_model('tienda', 'Pedido')
    Pedido.objects.filter(estado='confirmado').update(estado='pagado', estado_pago='pagado')


def revertir_pagados_a_confirmados(apps, schema_editor):
    Pedido = apps.get_model('tienda', 'Pedido')
    Pedido.objects.filter(estado='pagado').update(estado='confirmado')


class Migration(migrations.Migration):
    dependencies = [
        ('tienda', '0004_remove_producto_icono'),
    ]

    operations = [
        migrations.RunPython(convertir_confirmados_en_pagados, revertir_pagados_a_confirmados),
        migrations.AlterField(
            model_name='pedido',
            name='estado',
            field=models.CharField(
                choices=[
                    ('pendiente', 'Pendiente'),
                    ('pagado', 'Pagado'),
                    ('entregado', 'Entregado'),
                    ('cancelado', 'Cancelado'),
                ],
                default='pendiente',
                max_length=20,
            ),
        ),
    ]
