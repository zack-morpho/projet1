from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.hashers import make_password

class Utilisateur(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('USER', 'Utilisateur'),
    ]
    
    nom = models.CharField(max_length=100,)
    prenom = models.CharField(max_length=100,)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    role = models.CharField(max_length=13, choices=ROLE_CHOICES, default='USER')
    
    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.role})"
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

class Livre(models.Model):
    CATEGORY_CHOICES = [
        ('FICTION', 'Fiction'),
        ('NON_FICTION', 'Non-Fiction'),
        ('SCIENCE', 'Science'),
        ('HISTORY', 'History'),
        ('BIOGRAPHY', 'Biography'),
        ('TECHNOLOGY', 'Technology'),
        ('ART', 'Art'),
        ('OTHER', 'Other'),
    ]
    
    titre = models.CharField(max_length=100)
    auteur = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=6, decimal_places=2, default=50.0, verbose_name="Prix (Dirhams)")
    isbn = models.CharField(max_length=13, unique=True)
    categorie = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='OTHER')
    nbExemplaires = models.PositiveIntegerField(default=1)
    datePublication = models.DateField()
    imageUrl = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    dateAjout = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.titre} by {self.auteur} ({self.nbExemplaires})"
    
    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"
        ordering = ['-dateAjout']

class Emprunt(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='emprunts')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='emprunts')
    dateEmprunt = models.DateField(auto_now_add=True)
    dateRetourPrevue = models.DateField()
    dateRetourEffective = models.DateField(null=True, blank=True)
    estRetourne = models.BooleanField(default=False)
    
    def __str__(self):
        status = "Returned" if self.estRetourne else "Borrowed"
        return f"{self.utilisateur} - {self.livre} ({status})"
    
    @property
    def estEnRetard(self):
        from django.utils import timezone
        today = timezone.now().date()
        return not self.estRetourne and self.dateRetourPrevue < today
        
    _is_overdue = None
    
    @property
    def is_overdue(self):
        if self._is_overdue is not None:
            return self._is_overdue
        return self.estEnRetard
        
    @is_overdue.setter
    def is_overdue(self, value):
        self._is_overdue = value
        
    _jours_retard = None
    
    @property
    def joursRetard(self):
        if self._jours_retard is not None:
            return self._jours_retard
            
        if not self.estEnRetard:
            return 0
        from django.utils import timezone
        today = timezone.now().date()
        return (today - self.dateRetourPrevue).days
        
    @joursRetard.setter
    def joursRetard(self, value):
        self._jours_retard = value
        
    _montant_amende = None
    
    @property
    def montantAmende(self):
        if self._montant_amende is not None:
            return self._montant_amende
            
        return self.joursRetard * 5 if self.estEnRetard else 0
        
    @montantAmende.setter
    def montantAmende(self, value):
        self._montant_amende = value
        
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        was_returned = False
        
        if not is_new:
            try:
                old_instance = Emprunt.objects.get(pk=self.pk)
                was_returned = old_instance.estRetourne != self.estRetourne and self.estRetourne
            except Emprunt.DoesNotExist:
                pass
        
        if was_returned and not self.dateRetourEffective:
            from django.utils import timezone
            self.dateRetourEffective = timezone.now().date()
        
        super().save(*args, **kwargs)
        
        from django.utils import timezone
        today = timezone.now().date()
        
        is_overdue = not self.estRetourne and self.dateRetourPrevue < today
        was_overdue = was_returned and self.dateRetourPrevue < self.dateRetourEffective
        
        if is_overdue or was_overdue:
            from .models import Amende
            if not Amende.objects.filter(emprunt=self).exists():
                if was_returned:
                    jours_retard = (self.dateRetourEffective - self.dateRetourPrevue).days
                else:
                    jours_retard = (today - self.dateRetourPrevue).days
                
                montant = jours_retard * 5  
                
                Amende.objects.create(
                    emprunt=self,
                    utilisateur=self.utilisateur,
                    montant=montant,
                    raison=f"Retard de {jours_retard} jours pour le livre '{self.livre.titre}'"
                )
    
    class Meta:
        verbose_name = "Emprunt"
        verbose_name_plural = "Emprunts"


        ordering = ['-dateEmprunt']

class Amende(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='amendes')
    emprunt = models.ForeignKey(Emprunt, on_delete=models.CASCADE, related_name='amendes', null=True, blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    raison = models.CharField(max_length=200, default="Retard de retour")
    dateAmende = models.DateField(auto_now_add=True)
    estPayee = models.BooleanField(default=False)
    datePaiement = models.DateField(null=True, blank=True)
    
    def __str__(self):
        status = "Payée" if self.estPayee else "Non payée"
        return f"Amende: {self.montant} DH pour {self.utilisateur} ({status})"
    
    def payer(self):
        """Marquer l'amende comme payée et créer un enregistrement de paiement"""
        if not self.estPayee:
            from django.utils import timezone
            self.estPayee = True
            self.datePaiement = timezone.now().date()
            self.save()
            
            if self.emprunt and hasattr(self.emprunt, 'livre'):
                Payment.objects.create(
                    utilisateur=self.utilisateur,
                    livre=self.emprunt.livre,
                    prix=self.montant,
                    payment_method="Carte bancaire",
                    transaction_type="Amende"
                )
            else:
                from .models import Livre
                default_livre = Livre.objects.first()
                if default_livre:
                    Payment.objects.create(
                        utilisateur=self.utilisateur,
                        livre=default_livre,
                        prix=self.montant,
                        payment_method="Carte bancaire",
                        transaction_type="Amende"
                    )
            return True
        return False
    
    @classmethod
    def verifier_retards(cls):
        """Vérifie les emprunts en retard et crée des amendes si nécessaire"""
        from django.utils import timezone
        today = timezone.now().date()
        
        emprunts_en_retard = Emprunt.objects.filter(
            estRetourne=False,
            dateRetourPrevue__lt=today
        ).exclude(
            amendes__isnull=False
        )
        
        amendes_creees = 0
        for emprunt in emprunts_en_retard:
            jours_retard = (today - emprunt.dateRetourPrevue).days
            montant = jours_retard * 5

            cls.objects.create(
                emprunt=emprunt,
                utilisateur=emprunt.utilisateur,
                montant=montant,
                raison=f"Retard de {jours_retard} jours pour le livre '{emprunt.livre.titre}'"
            )
            amendes_creees += 1
            
        return amendes_creees
    
    class Meta:
        verbose_name = "Amende"
        verbose_name_plural = "Amendes"
        ordering = ['-dateAmende']

class Reservation(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='reservations')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='reservations')
    dateReservation = models.DateField(auto_now_add=True)
    dateRetour = models.DateField(null=True, blank=True)
    ProchaineDateRetour = models.DateField(null=True, blank=True)
    estEffectuee = models.BooleanField(default=False)
    estAnnulee = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Réservation: {self.utilisateur} - {self.livre} (Retour prévu: {self.dateRetour})"
    
    class Meta:
        unique_together = ('livre', 'utilisateur')  
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ['-dateReservation']

class Commentaire(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='commentaires')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='commentaires')
    texte = models.TextField()
    note = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.utilisateur} on {self.livre}"
    
    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ['-created_at']  

class Payment(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='payments')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Prix payé (Dirhams)")
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=20, default="Emprunt", choices=[("Emprunt", "Emprunt"), ("Reservation", "Réservation")])
    
    def __str__(self):
        return f"Payment: {self.utilisateur} - {self.livre} - {self.payment_method} - {self.prix} DH"
    
    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-created_at']

class Message(models.Model):
    expediteur = models.CharField(max_length=100, default="Administrateur")
    destinataire = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='messages')
    sujet = models.CharField(max_length=200)
    contenu = models.TextField()
    dateEnvoi = models.DateTimeField(auto_now_add=True)
    estLu = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Message de {self.expediteur} à {self.destinataire}: {self.sujet}"
    
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['-dateEnvoi']