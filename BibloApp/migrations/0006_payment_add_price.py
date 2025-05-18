from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('BibloApp', '0005_alter_livre_prix_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='prix',
            field=models.DecimalField(max_digits=6, decimal_places=2, verbose_name='Prix payé (Dirhams)', default=50.0),
            preserve_default=False,
        ),
    ]
