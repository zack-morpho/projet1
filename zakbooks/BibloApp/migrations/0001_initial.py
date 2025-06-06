# Generated by Django 5.2 on 2025-04-11 23:42

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Livre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=100)),
                ('auteur', models.CharField(max_length=100)),
                ('isbn', models.CharField(max_length=13, unique=True)),
                ('categorie', models.CharField(choices=[('FICTION', 'Fiction'), ('NON_FICTION', 'Non-Fiction'), ('SCIENCE', 'Science'), ('HISTORY', 'History'), ('BIOGRAPHY', 'Biography'), ('TECHNOLOGY', 'Technology'), ('ART', 'Art'), ('OTHER', 'Other')], default='OTHER', max_length=100)),
                ('nbExemplaires', models.PositiveIntegerField(default=1)),
                ('datePublication', models.DateField()),
                ('description', models.TextField(blank=True, null=True)),
                ('dateAjout', models.DateField(auto_now_add=True)),
                ('estDisponible', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Book',
                'verbose_name_plural': 'Books',
                'ordering': ['-dateAjout'],
            },
        ),
        migrations.CreateModel(
            name='Utilisateur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('prenom', models.CharField(max_length=100)),
                ('username', models.CharField(max_length=100, unique=True)),
                ('password', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=100, unique=True)),
                ('role', models.CharField(choices=[('ADMIN', 'Administrator'), ('USER', 'utilisateur')], default='USER', max_length=50)),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
        ),
        migrations.CreateModel(
            name='Emprunt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dateEmprunt', models.DateField(auto_now_add=True)),
                ('dateRetour', models.DateField()),
                ('estRetourne', models.BooleanField(default=False)),
                ('livre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emprunts', to='BibloApp.livre')),
                ('utilisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emprunts', to='BibloApp.utilisateur')),
            ],
            options={
                'verbose_name': 'Emprunt',
                'verbose_name_plural': 'Emprunts',
                'ordering': ['-dateEmprunt'],
            },
        ),
        migrations.CreateModel(
            name='Commentaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texte', models.TextField()),
                ('note', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('livre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commentaires', to='BibloApp.livre')),
                ('utilisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commentaires', to='BibloApp.utilisateur')),
            ],
            options={
                'verbose_name': 'Comment',
                'verbose_name_plural': 'Comments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Amende',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('montant', models.DecimalField(decimal_places=2, max_digits=10)),
                ('dateAmende', models.DateField(auto_now_add=True)),
                ('utilisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amendes', to='BibloApp.utilisateur')),
            ],
            options={
                'verbose_name': 'Amende',
                'verbose_name_plural': 'Amendes',
                'ordering': ['-dateAmende'],
            },
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dateReservation', models.DateField(auto_now_add=True)),
                ('livre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='BibloApp.livre')),
                ('utilisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='BibloApp.utilisateur')),
            ],
            options={
                'verbose_name': 'Reservation',
                'verbose_name_plural': 'Reservations',
                'ordering': ['-dateReservation'],
                'unique_together': {('livre', 'utilisateur')},
            },
        ),
    ]
