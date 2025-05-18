from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Reservation, Message, Utilisateur, Livre, Emprunt, Amende, Commentaire, Payment
from django.utils import timezone
from django.http import HttpResponse
import csv
from django.apps import apps
from django.db.models import Count, Sum, F, Q
from datetime import timedelta

def admin_cancel_reservation(request, reservation_id):
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    
    if not user_id or user_role != 'ADMIN':
        messages.error(request, "Vous n'êtes pas autorisé à effectuer cette action.")
        return redirect('dynamic_admin_model_list')
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if reservation.estAnnulee:
        messages.warning(request, "Cette réservation a déjà été annulée.")
        return redirect('dynamic_admin_object_list', model_name='Reservation')
    
    if reservation.estEffectuee:
        messages.warning(request, "Cette réservation a déjà été effectuée et ne peut pas être annulée.")
        return redirect('dynamic_admin_object_list', model_name='Reservation')
    
    if request.method == 'POST':
        raison = request.POST.get('raison', 'Aucune raison spécifiée')
        
        reservation.estAnnulee = True
        reservation.save()
        
        Message.objects.create(
            expediteur="Administrateur",
            destinataire=reservation.utilisateur,
            sujet="Annulation de votre réservation",
            contenu=f"Votre réservation pour le livre '{reservation.livre.titre}' a été annulée par l'administrateur. Raison: {raison}"
        )
        
        messages.success(request, f"Réservation annulée et message envoyé à {reservation.utilisateur.prenom} {reservation.utilisateur.nom}.")
        return redirect('dynamic_admin_object_list', model_name='Reservation')
    
    from django.apps import apps
    app = apps.get_app_config('BibloApp')
    models = list(app.get_models())
    model_tuples = [(model.__name__, model) for model in models]
    
    connected_user = None
    try:
        connected_user = Utilisateur.objects.get(id=user_id)
    except Utilisateur.DoesNotExist:
        pass
    
    return render(request, 'dynamic_admin/Annule_reservation.html', {
        'reservation': reservation,
        'model_tuples': model_tuples,
        'connected_user': connected_user,
    })


def export_csv(request, model_name):
    """Exporter les données d'un modèle en CSV"""
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    
    if not user_id or user_role != 'ADMIN':
        messages.error(request, "Vous n'êtes pas autorisé à effectuer cette action.")
        return redirect('dynamic_admin_model_list')
    
    app_models = {
        'Livre': Livre,
        'Utilisateur': Utilisateur,
        'Reservation': Reservation,
        'Emprunt': Emprunt,
        'Amende': Amende,
        'Message': Message,
        'Commentaire': Commentaire,
        'Payment': Payment
    }
    
    model = app_models.get(model_name)
    if not model:
        messages.error(request, f"Le modèle {model_name} n'existe pas.")
        return redirect('dynamic_admin_model_list')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{model_name.lower()}_list.csv"'
    
    writer = csv.writer(response)
    
    queryset = model.objects.all()
    
    fields = [field.name for field in model._meta.fields]
    
    writer.writerow(fields)
    
    for obj in queryset:
        row = []
        for field in fields:
            value = getattr(obj, field)
            if hasattr(value, '__str__'):
                value = str(value)
            row.append(value)
        writer.writerow(row)
    
    return response


def statistical_reports(request):
    """Vue pour les rapports statistiques"""
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    
    if not user_id or user_role != 'ADMIN':
        messages.error(request, "Vous n'êtes pas autorisé à effectuer cette action.")
        return redirect('dynamic_admin_model_list')
    
    app = apps.get_app_config('BibloApp')
    models = list(app.get_models())
    model_tuples = [(model.__name__, model) for model in models]
    
    connected_user = None
    try:
        connected_user = Utilisateur.objects.get(id=user_id)
    except Utilisateur.DoesNotExist:
        pass
    
    most_borrowed_books = Livre.objects.annotate(
        emprunts_count=Count('emprunts')
    ).order_by('-emprunts_count')[:10]
    
    today = timezone.now().date()
    late_loans = Emprunt.objects.filter(
        dateRetourPrevue__lt=today,
        estRetourne=False
    ).select_related('utilisateur', 'livre').order_by('dateRetourPrevue')
    
    popular_categories = Livre.objects.values('categorie').annotate(
        total_emprunts=Count('emprunts')
    ).order_by('-total_emprunts')[:5]
    
    total_books = Livre.objects.count()
    total_users = Utilisateur.objects.count()
    total_active_loans = Emprunt.objects.filter(estRetourne=False).count()
    total_late_loans = late_loans.count()
    total_fines = Amende.objects.aggregate(Sum('montant'))['montant__sum'] or 0
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_loans = Emprunt.objects.filter(dateEmprunt__gte=thirty_days_ago).count()
    recent_returns = Emprunt.objects.filter(estRetourne=True, dateRetourEffective__gte=thirty_days_ago).count()
    recent_registrations = 0 
    
    context = {
        'model_tuples': model_tuples,
        'connected_user': connected_user,
        'most_borrowed_books': most_borrowed_books,
        'late_loans': late_loans,
        'popular_categories': popular_categories,
        'total_books': total_books,
        'total_users': total_users,
        'total_active_loans': total_active_loans,
        'total_late_loans': total_late_loans,
        'total_fines': total_fines,
        'recent_loans': recent_loans,
        'recent_returns': recent_returns,
        'recent_registrations': recent_registrations,
    }
    
    return render(request, 'dynamic_admin/statistical_reports.html', context)
