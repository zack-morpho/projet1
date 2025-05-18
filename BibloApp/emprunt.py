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
    try:
        livre = get_object_or_404(Livre, isbn=isbn)
    except:
        messages.error(request, "Livre introuvable. Veuillez réessayer.")
        return redirect('home')
        
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

    # Check for date_retour in session - handle missing data gracefully
    date_retour_str = request.session.get('date_retour')
    if not date_retour_str and request.method != 'POST':
        # If accessing the page directly without going through proper flow
        try:
            # Try to redirect to emprunter_livre instead of showing an error
            return redirect('emprunter_livre', isbn=livre.isbn)
        except:
            messages.error(request, "Une erreur s'est produite. Veuillez recommencer le processus d'emprunt.")
            return redirect('home')

    if request.method == 'POST':
        try:
            cardholder = request.POST.get('cardholder')
            cardnumber = request.POST.get('cardnumber')
            expdate = request.POST.get('expdate')
            cvv = request.POST.get('cvv')
            
            if not (cardholder and cardnumber and expdate and cvv):
                messages.error(request, "Veuillez remplir tous les champs de paiement.")
                return render(request, 'application/payment.html', {'livre': livre, 'utilisateur': utilisateur})
                
            if not date_retour_str:
                # If date_retour is missing but we're in POST, handle it gracefully
                messages.error(request, "Information de date manquante. Veuillez recommencer le processus d'emprunt.")
                return redirect('emprunter_livre', isbn=livre.isbn)
                
            if livre.nbExemplaires > 0:
                try:
                    date_emprunt = timezone.now().date()
                    date_retour = date_retour_str
                    
                    # Create the loan record with proper error handling
                    emprunt = Emprunt.objects.create(
                        livre=livre,
                        utilisateur=utilisateur,
                        dateEmprunt=date_emprunt,
                        dateRetourPrevue=date_retour,
                        estRetourne=False
                    )
                    
                    # Import Payment at function level to avoid circular imports
                    from .models import Payment
                    Payment.objects.create(
                        livre=livre,
                        utilisateur=utilisateur,
                        payment_method="Carte bancaire",
                        prix=livre.prix,
                        transaction_type="Emprunt"  
                    )
                    
                    # Update book inventory
                    livre.nbExemplaires -= 1
                    livre.save()
                    
                    # Clean up session data
                    if 'date_retour' in request.session:
                        del request.session['date_retour']
                        
                    messages.success(request, "Emprunt et paiement enregistrés avec succès !")
                    return redirect('home')
                    
                except Exception as e:
                    # If any database operation fails, roll back and show error
                    messages.error(request, f"Une erreur s'est produite lors de l'enregistrement. Veuillez réessayer.")
                    return render(request, 'application/payment.html', {'livre': livre, 'utilisateur': utilisateur})
            else:
                messages.error(request, "Aucun exemplaire disponible pour ce livre.")
                return redirect('book_detail', isbn=livre.isbn)
                
        except Exception as e:
            # Catch-all for any other exceptions
            messages.error(request, f"Une erreur inattendue s'est produite. Veuillez réessayer.")
            return redirect('home')
    return render(request, 'application/payment.html', {'livre': livre, 'utilisateur': utilisateur})

def emprunter_livre(request, isbn):
    livre = get_object_or_404(Livre, isbn=isbn)
    return render(request, 'application/Emprunter.html', {'livre': livre})


