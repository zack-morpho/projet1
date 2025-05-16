from django.contrib import admin
from .models import Utilisateur, Livre, Emprunt, Amende, Reservation, Commentaire



# Register your models here.
admin.site.register(Utilisateur)
admin.site.register(Livre)
admin.site.register(Emprunt)
admin.site.register(Amende)
admin.site.register(Reservation)
admin.site.register(Commentaire)
