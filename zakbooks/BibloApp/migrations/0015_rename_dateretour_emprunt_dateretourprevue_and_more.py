# Generated by Django 5.2 on 2025-05-05 17:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BibloApp', '0014_reservation_estannulee'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emprunt',
            old_name='dateRetour',
            new_name='dateRetourPrevue',
        ),
        migrations.AddField(
            model_name='amende',
            name='datePaiement',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='amende',
            name='emprunt',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='amendes', to='BibloApp.emprunt'),
        ),
        migrations.AddField(
            model_name='amende',
            name='estPayee',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='amende',
            name='raison',
            field=models.CharField(default='Retard de retour', max_length=200),
        ),
        migrations.AddField(
            model_name='emprunt',
            name='dateRetourEffective',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expediteur', models.CharField(default='Administrateur', max_length=100)),
                ('sujet', models.CharField(max_length=200)),
                ('contenu', models.TextField()),
                ('dateEnvoi', models.DateTimeField(auto_now_add=True)),
                ('estLu', models.BooleanField(default=False)),
                ('destinataire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='BibloApp.utilisateur')),
            ],
            options={
                'verbose_name': 'Message',
                'verbose_name_plural': 'Messages',
                'ordering': ['-dateEnvoi'],
            },
        ),
    ]
