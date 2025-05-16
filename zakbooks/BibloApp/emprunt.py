from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Livre, Emprunt, Utilisateur
from django.utils import timezone

def payer_emprunt(request, isbn):
    livre = get_object_or_404(Livre, isbn=isbn)
    user_id = request.session.get('user_id')
    utilisateur = None
    if user_id:
        try:
            utilisateur = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            utilisateur = None
    if not utilisateur:
        messages.error(request, "Vous devez être connecté pour payer l'emprunt.")
        return redirect('book_detail', isbn=livre.isbn)

    if request.method == 'POST':
        date_retour_str = request.POST.get('dateRetour')
        if not date_retour_str:
            messages.error(request, "Date de retour manquante.")
            return redirect('emprunter_livre', isbn=livre.isbn)
        request.session['date_retour'] = date_retour_str
        return redirect('payment_emprunt', isbn=livre.isbn)

    return redirect('emprunter_livre', isbn=livre.isbn)

def payment_emprunt(request, isbn):
    livre = get_object_or_404(Livre, isbn=isbn)
    user_id = request.session.get('user_id')
    utilisateur = None
    if user_id:
        try:
            utilisateur = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            utilisateur = None
    if not utilisateur:
        messages.error(request, "Vous devez être connecté pour payer l'emprunt.")
        return redirect('book_detail', isbn=livre.isbn)

    date_retour_str = request.session.get('date_retour')
    if not date_retour_str:
        messages.error(request, "Date de retour manquante.")
        return redirect('emprunter_livre', isbn=livre.isbn)

    if request.method == 'POST':
        cardholder = request.POST.get('cardholder')
        cardnumber = request.POST.get('cardnumber')
        expdate = request.POST.get('expdate')
        cvv = request.POST.get('cvv')
        if not (cardholder and cardnumber and expdate and cvv):
            messages.error(request, "Veuillez remplir tous les champs de paiement.")
            return render(request, 'application/payment.html', {'livre': livre, 'utilisateur': utilisateur})
        if livre.nbExemplaires > 0:
            date_emprunt = timezone.now().date()
            date_retour = date_retour_str
            Emprunt.objects.create(
                livre=livre,
                utilisateur=utilisateur,
                dateEmprunt=date_emprunt,
                dateRetourPrevue=date_retour,
                estRetourne=False
            )
            from .models import Payment
            Payment.objects.create(
                livre=livre,
                utilisateur=utilisateur,
                payment_method="Carte bancaire",
                prix=livre.prix,
                transaction_type="Emprunt"  
            )
            livre.nbExemplaires -= 1
            livre.save()
            if 'date_retour' in request.session:
                del request.session['date_retour']
            messages.success(request, "Emprunt et paiement enregistrés avec succès !")
            return redirect('home')
        else:
            messages.error(request, "Aucun exemplaire disponible pour ce livre.")
            return redirect('book_detail', isbn=livre.isbn)
    return render(request, 'application/payment.html', {'livre': livre, 'utilisateur': utilisateur})

def emprunter_livre(request, isbn):
    livre = get_object_or_404(Livre, isbn=isbn)
    return render(request, 'application/Emprunter.html', {'livre': livre})


