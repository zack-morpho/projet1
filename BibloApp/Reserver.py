from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Livre, Utilisateur, Reservation, Payment
from django.db import transaction, IntegrityError
from datetime import date

def reserver_livre(request, isbn):
    livre = get_object_or_404(Livre, isbn=isbn)
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.error(request, "Vous devez être connecté pour réserver un livre.")
        return redirect('book_detail', isbn=livre.isbn)
        
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    
    if Reservation.objects.filter(livre=livre, utilisateur=utilisateur).exists():
        messages.error(request, "Vous avez déjà réservé ce livre.")
        return redirect('book_detail', isbn=livre.isbn)
    
    if request.method == 'POST':
        date_retour = request.POST.get('dateRetour')
        if not date_retour:
            messages.error(request, "Date de retour manquante.")
            return redirect('reserver_livre', isbn=livre.isbn)
            
        request.session['date_retour'] = date_retour
        return redirect('payer_reservation', isbn=livre.isbn)
    
    next_date = None
    
    reservations_existantes = Reservation.objects.filter(livre=livre)
    dates_reservees = set(reservations_existantes.values_list('ProchaineDateRetour', flat=True))
    
    emprunts = livre.emprunts.filter(estRetourne=False).order_by('dateRetourPrevue')
    
    for emprunt in emprunts:
        if emprunt.dateRetourPrevue and emprunt.dateRetourPrevue not in dates_reservees:
            next_date = emprunt.dateRetourPrevue
            break
    
    if not next_date:
        from datetime import timedelta
        derniere_reservation = reservations_existantes.order_by('-ProchaineDateRetour').first()
        
        if derniere_reservation and derniere_reservation.ProchaineDateRetour:
            next_date = derniere_reservation.ProchaineDateRetour + timedelta(days=1)
        else:
            next_date = timezone.now().date()
    
    request.session['next_date'] = str(next_date)
    
    return render(request, 'application/Reserver.html', {
        'livre': livre,
        'next_date': next_date,
        'already_reserved': False  
    })

def payer_reservation(request, isbn):
    livre = get_object_or_404(Livre, isbn=isbn)
    utilisateur = get_object_or_404(Utilisateur, id=request.session.get('user_id'))
    
    if Reservation.objects.filter(livre=livre, utilisateur=utilisateur).exists():
        messages.error(request, "Vous avez déjà réservé ce livre.")
        return redirect('book_detail', isbn=isbn)
    
    if request.method == 'POST':
        if not all([request.POST.get('cardholder'), request.POST.get('cardnumber'), 
                   request.POST.get('expdate'), request.POST.get('cvv')]):
            return render(request, 'application/payment.html', {'livre': livre})
        
        try:
            with transaction.atomic():
                date_retour_str = request.session.get('date_retour')
                next_date_str = request.session.get('next_date')
                
                date_retour = None
                if date_retour_str:
                    try:
                        date_retour = date.fromisoformat(date_retour_str)
                    except ValueError:
                        from datetime import timedelta
                        date_retour = timezone.now().date() + timedelta(days=14)
                else:
                    from datetime import timedelta
                    date_retour = timezone.now().date() + timedelta(days=14)
                
                emprunts_actifs = livre.emprunts.filter(estRetourne=False).order_by('dateRetourPrevue')
                
                reservations_existantes = Reservation.objects.filter(livre=livre)
                dates_reservees = set(reservations_existantes.values_list('ProchaineDateRetour', flat=True))
                
                prochaine_date_retour = None
                
                for emprunt in emprunts_actifs:
                    if emprunt.dateRetourPrevue and emprunt.dateRetourPrevue not in dates_reservees:
                        prochaine_date_retour = emprunt.dateRetourPrevue
                        break
                
                if not prochaine_date_retour:
                    from datetime import timedelta
                    
                    derniere_reservation = reservations_existantes.order_by('-ProchaineDateRetour').first()
                    
                    if derniere_reservation and derniere_reservation.ProchaineDateRetour:
                        prochaine_date_retour = derniere_reservation.ProchaineDateRetour + timedelta(days=1)
                    else:
                        prochaine_date_retour = timezone.now().date()
                
                while prochaine_date_retour in dates_reservees:
                    prochaine_date_retour = prochaine_date_retour + timedelta(days=1)
                    
                reservation = Reservation.objects.create(
                    livre=livre,
                    utilisateur=utilisateur,
                    dateRetour=date_retour, 
                    ProchaineDateRetour=prochaine_date_retour,
                    estEffectuee=False 
                )
                
                print(f"Réservation créée: ID={reservation.id}, dateRetour={reservation.dateRetour}")
                
                Payment.objects.create(
                    livre=livre,
                    utilisateur=utilisateur,
                    payment_method="Card",
                    prix=livre.prix,
                    transaction_type="Reservation"  
                )
                
                if 'date_retour' in request.session:
                    del request.session['date_retour']
                if 'next_date' in request.session:
                    del request.session['next_date']
                
                messages.success(request, "Réservation confirmée !")
                return redirect('book_detail', isbn=isbn)
        except IntegrityError:
            messages.error(request, "Erreur: Vous avez déjà réservé ce livre.")
            return redirect('book_detail', isbn=isbn)
