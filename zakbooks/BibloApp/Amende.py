from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Utilisateur, Amende, Payment


def user_amendes(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    if not user_id:
        return redirect('login')
    
    if user_role == 'ADMIN':
        messages.info(request, "Les administrateurs doivent utiliser l'interface d'administration.")
        return redirect('dynamic_admin_object_list', model_name='Amende')
    
    user = get_object_or_404(Utilisateur, id=user_id)
    amendes = user.amendes.all().select_related('emprunt', 'emprunt__livre')
    
    status = request.GET.get('status')
    if status == 'unpaid':
        amendes = amendes.filter(estPayee=False)
    elif status == 'paid':
        amendes = amendes.filter(estPayee=True)
    
    total_unpaid = sum(amende.montant for amende in amendes if not amende.estPayee)
    
    return render(request, 'accounts/amendes.html', {
        'user': user,
        'amendes': amendes,
        'total_unpaid': total_unpaid,
        'active_tab': 'amendes'
    })

def pay_fine(request, amende_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    amende = get_object_or_404(Amende, id=amende_id, utilisateur_id=user_id)
    
    if amende.estPayee:
        messages.info(request, "Cette amende a déjà été payée.")
        return redirect('user-amendes')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        if not payment_method:
            messages.error(request, "Veuillez sélectionner une méthode de paiement.")
            return redirect('pay-fine', amende_id=amende_id)
        
        if amende.payer():
            messages.success(request, f"Paiement de {amende.montant} DH effectué avec succès.")
            
            if amende.emprunt and not amende.emprunt.estRetourne:
                messages.warning(request, f"N'oubliez pas de retourner le livre '{amende.emprunt.livre.titre}' à la bibliothèque.")
        else:
            messages.error(request, "Une erreur est survenue lors du paiement. Veuillez réessayer.")
        
        return redirect('user-amendes')
    
    return render(request, 'accounts/payer_amende.html', {
        'amende': amende
    })

def check_overdue_books(request):
    user_role = request.session.get('role')
    if user_role != 'ADMIN':
        messages.error(request, "Vous n'avez pas les droits pour effectuer cette action.")
        return redirect('mon-compte')
    
    from django.utils import timezone
    today = timezone.now().date()
    
    from .models import Emprunt, Amende
    emprunts_en_retard = Emprunt.objects.filter(
        estRetourne=False,
        dateRetourPrevue__lt=today
    ).exclude(
        amendes__isnull=False
    )
    
    amendes_creees = 0
    for emprunt in emprunts_en_retard:
        jours_retard = (today - emprunt.dateRetourPrevue).days
        montant = jours_retard * 5  # 5 DH par jour de retard
        
        Amende.objects.create(
            emprunt=emprunt,
            utilisateur=emprunt.utilisateur,
            montant=montant,
            raison=f"Retard de {jours_retard} jours pour le livre '{emprunt.livre.titre}'"
        )
        amendes_creees += 1
    
    messages.success(request, f'{amendes_creees} amendes ont été créées pour des livres en retard.')
    return redirect('dynamic_admin_object_list', model_name='Amende')
