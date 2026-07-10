from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0006_pedido_estado_listo'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='tipo_documento',
            field=models.CharField(
                choices=[('boleta', 'Boleta'), ('factura', 'Factura')],
                default='boleta',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='pedido',
            name='factura_rut',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='pedido',
            name='factura_razon_social',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name='pedido',
            name='factura_giro',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name='pedido',
            name='factura_direccion',
            field=models.CharField(blank=True, max_length=220),
        ),
        migrations.AddField(
            model_name='pedido',
            name='factura_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
    ]
