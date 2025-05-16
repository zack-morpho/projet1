from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.urls import reverse
from .models import Utilisateur, Reservation, Emprunt, Amende, Message, Payment
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import io

def user_reservations(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    if not user_id:
        return redirect('login')    
    if user_role == 'ADMIN' and 'admin-reservations' not in request.resolver_match.url_name:
        messages.info(request, "Les administrateurs doivent utiliser l'interface d'administration.")
        return redirect('dynamic_admin_object_list', model_name='Reservation')
    
    user = get_object_or_404(Utilisateur, id=user_id)
    is_admin = user_role == 'ADMIN'
    
    admin_mode = 'admin-reservations' in request.resolver_match.url_name
    
    if admin_mode and not is_admin:
        messages.error(request, "Vous n'avez pas les droits d'administrateur.")
        return redirect('user-reservations')
    
    if admin_mode:
        reservations = Reservation.objects.all().select_related('livre', 'utilisateur')
    else:
        reservations = user.reservations.all().select_related('livre')
    
    status = request.GET.get('status')
    if status == 'active':
        reservations = reservations.filter(estEffectuee=False, estAnnulee=False)
    elif status == 'completed':
        reservations = reservations.filter(estEffectuee=True)
    elif status == 'cancelled':
        reservations = reservations.filter(estAnnulee=True)

    reservations = reservations.order_by('-dateReservation')

    template = 'dynamic_admin/admin_reservations.html' if admin_mode else 'accounts/reservations.html'

    return render(request, template, {
        'user': user,
        'reservations': reservations,
        'active_tab': 'reservations',
        'is_admin': is_admin
    })

def user_emprunts(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    if not user_id:
        return redirect('login')
    
    if user_role == 'ADMIN':
        messages.info(request, "Les administrateurs doivent utiliser l'interface d'administration.")
        return redirect('dynamic_admin_object_list', model_name='Emprunt')
    
    user = get_object_or_404(Utilisateur, id=user_id)
    emprunts = user.emprunts.all().select_related('livre').prefetch_related('amendes')
    
    from django.utils import timezone
    today = timezone.now().date()
    
    for emprunt in emprunts:
        emprunt.is_overdue = emprunt.estEnRetard
        
        if emprunt.is_overdue:
            emprunt.joursRetard = (today - emprunt.dateRetourPrevue).days
            emprunt.montantAmende = emprunt.joursRetard * 5  # 5 DH par jour
    
    status = request.GET.get('status')
    if status == 'current':
        emprunts = [e for e in emprunts if not e.estRetourne]
    elif status == 'returned':
        emprunts = [e for e in emprunts if e.estRetourne]
    elif status == 'overdue':
        emprunts = [e for e in emprunts if getattr(e, 'is_overdue', False)]
    
    return render(request, 'accounts/emprunts.html', {
        'user': user,
        'emprunts': emprunts,
        'active_tab': 'emprunts'
    })


def user_messages(request):
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    if not user_id:
        return redirect('login')
    
    if user_role == 'ADMIN':
        messages.info(request, "Les administrateurs doivent utiliser l'interface d'administration.")
        return redirect('admin-messages')
    
    user = get_object_or_404(Utilisateur, id=user_id)
    user_messages = user.messages.all().order_by('-dateEnvoi')
    
    status = request.GET.get('status')
    if status == 'unread':
        user_messages = user_messages.filter(estLu=False)
    elif status == 'read':
        user_messages = user_messages.filter(estLu=True)
    
    unread_count = user.messages.filter(estLu=False).count()
    
    return render(request, 'accounts/messages.html', {
        'user': user,
        'user_messages': user_messages,
        'unread_count': unread_count,
        'active_tab': 'messages'
    })

def mark_message_read(request, message_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    message = get_object_or_404(Message, id=message_id, destinataire_id=user_id)
    message.estLu = True
    message.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, "Message marqué comme lu.")
    return redirect('user-messages')


def cancel_reservation(request, reservation_id):
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    
    if not user_id:
        return redirect('login')
    
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    is_owner = str(reservation.utilisateur.id) == str(user_id)
    is_admin = user_role == 'ADMIN'
    
    if not (is_owner or is_admin):
        messages.error(request, "Vous n'êtes pas autorisé à annuler cette réservation.")
        return redirect('user-reservations')
    
    if reservation.estAnnulee:
        messages.warning(request, "Cette réservation a déjà été annulée.")
        return redirect('user-reservations')
    
    if reservation.estEffectuee:
        messages.warning(request, "Cette réservation a déjà été effectuée et ne peut pas être annulée.")
        return redirect('user-reservations')
    
    if request.method == 'POST':
        reservation.estAnnulee = True
        reservation.save()
        
        if is_admin and not is_owner:
            reason = request.POST.get('reason', 'Aucune raison spécifiée')
            Message.objects.create(
                expediteur="Administrateur",
                destinataire=reservation.utilisateur,
                sujet="Annulation de votre réservation",
                contenu=f"Votre réservation pour le livre '{reservation.livre.titre}' a été annulée par l'administrateur. Raison: {reason}"
            )
            messages.success(request, f"Réservation annulée et message envoyé à {reservation.utilisateur.prenom} {reservation.utilisateur.nom}.")
            return redirect('admin-reservations')
        else:
            messages.success(request, "Votre réservation a été annulée avec succès.")
            return redirect('user-reservations')
    
    return render(request, 'accounts/Annule_reservation.html', {
        'reservation': reservation,
        'is_admin': is_admin
    })

def admin_messages(request):
    """View for displaying all messages sent by admin"""
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    
    if not user_id:
        return redirect('login')
    
    if user_role != 'ADMIN':
        messages.error(request, "Vous n'êtes pas autorisé à accéder à cette page.")
        return redirect('mon-compte')
    
    messages_list = Message.objects.filter(expediteur="Administrateur").select_related('destinataire').order_by('-dateEnvoi')
    
    from django.apps import apps
    app = apps.get_app_config('BibloApp')
    models = list(app.get_models())
    model_tuples = [(model.__name__, model) for model in models]
    
    return render(request, 'dynamic_admin/admin_messages.html', {
        'messages_list': messages_list,
        'active_tab': 'messages',
        'model_tuples': model_tuples,
        'connected_user': Utilisateur.objects.get(id=user_id)
    })

def send_message(request, user_id=None):
    """Send a message to a user (admin only)"""
    sender_id = request.session.get('user_id')
    sender_role = request.session.get('role')
    
    if not sender_id:
        return redirect('login')
    
    if sender_role != 'ADMIN':
        messages.error(request, "Vous n'êtes pas autorisé à envoyer des messages.")
        return redirect('mon-compte')
    
    recipient = None
    if user_id:
        recipient = get_object_or_404(Utilisateur, id=user_id)
    
    users = Utilisateur.objects.filter(role='USER').order_by('nom', 'prenom')
    
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        
        if not all([recipient_id, subject, content]):
            messages.error(request, "Tous les champs sont obligatoires.")
            return render(request, 'accounts/send_message.html', {
                'users': users,
                'selected_user': recipient
            })
        
        try:
            recipient = Utilisateur.objects.get(id=recipient_id)
            
            Message.objects.create(
                expediteur="Administrateur",
                destinataire=recipient,
                sujet=subject,
                contenu=content
            )
            
            messages.success(request, f"Message envoyé à {recipient.prenom} {recipient.nom}.")
            return redirect('admin-messages')
            
        except Utilisateur.DoesNotExist:
            messages.error(request, "Utilisateur introuvable.")
    
    from django.apps import apps
    app = apps.get_app_config('BibloApp')
    models = list(app.get_models())
    model_tuples = [(model.__name__, model) for model in models]
    
    return render(request, 'dynamic_admin/send_message.html', {
        'users': users,
        'selected_user': recipient,
        'model_tuples': model_tuples,
        'connected_user': Utilisateur.objects.get(id=sender_id)
    })


def user_receipts(request):
    """View for displaying user payment receipts"""
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    if not user_id:
        return redirect('login')
    
    if user_role == 'ADMIN':
        messages.info(request, "Les administrateurs doivent utiliser l'interface d'administration.")
        return redirect('dynamic_admin_object_list', model_name='Payment')
    
    user = get_object_or_404(Utilisateur, id=user_id)
    
    payments = Payment.objects.filter(utilisateur=user).select_related('livre', 'utilisateur').order_by('-created_at')
    
    return render(request, 'accounts/RecuDePaiement.html', {
        'user': user,
        'payments': payments,
        'active_tab': 'RecuDePaiement'
    })

def download_receipt(request, payment_id):
    """Generate and download a PDF receipt for a payment"""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    user = get_object_or_404(Utilisateur, id=user_id)
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.utilisateur.id != user.id and user.role != 'ADMIN':
        messages.error(request, "Vous n'êtes pas autorisé à accéder à ce reçu.")
        return redirect('mon-compte')
    
    buffer = io.BytesIO()
    
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4  
    
    blue_color = colors.HexColor('#3498db')  
    dark_blue = colors.HexColor('#2c3e50')   
    green_color = colors.HexColor('#2ecc71')  
    light_gray = colors.HexColor('#f8f9fa')  
    medium_gray = colors.HexColor('#bdc3c7') 
    
    p.setFillColor(blue_color)
    p.rect(0, height-80, width, 80, fill=1, stroke=0)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 28)
    p.drawCentredString(width/2, height-50, "ZakBooks")
    
    p.setFillColor(dark_blue)
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, height-110, f"Reçu de Paiement #{payment.id}")
    
    p.setFont("Helvetica", 11)
    p.setFillColor(colors.gray)
    date_text = f"Date: {payment.created_at.strftime('%d/%m/%Y %H:%M')}"
    p.drawRightString(width-50, height-130, date_text)
    
    p.setStrokeColor(medium_gray)
    p.line(50, height-150, width-50, height-150)
    
    p.setFillColor(dark_blue)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height-180, "Information Client")
    
    p.setFillColor(light_gray)
    p.rect(50, height-240, width-100, 40, fill=1, stroke=0)
    
    p.setFillColor(dark_blue)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, height-200, "Nom:")
    p.drawString(60, height-220, "Email:")
    
    p.setFont("Helvetica", 12)
    p.drawString(150, height-200, f"{payment.utilisateur.prenom} {payment.utilisateur.nom}")
    p.drawString(150, height-220, f"{payment.utilisateur.email}")
    
    p.setFillColor(dark_blue)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height-270, "Détails du Paiement")
    
    p.setFillColor(blue_color)
    p.rect(50, height-300, width-100, 20, fill=1, stroke=0)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, height-295, "Article")
    p.drawString(200, height-295, "Description")
    p.drawRightString(width-60, height-295, "Prix")
    
    p.setFillColor(light_gray)
    p.rect(50, height-350, width-100, 50, fill=1, stroke=0)
    
    p.setFillColor(dark_blue)
    p.setFont("Helvetica", 12)
    p.drawString(60, height-320, "Livre")
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(200, height-320, f"{payment.livre.titre}")
    p.setFont("Helvetica", 11)
    p.drawString(200, height-335, f"par {payment.livre.auteur}")
    p.setFont("Helvetica", 9)
    p.setFillColor(colors.gray)
    p.drawString(200, height-350, f"ISBN: {payment.livre.isbn}")
    
    p.setFillColor(dark_blue)
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(width-60, height-320, f"{payment.prix} DH")
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height-380, "Méthode de paiement:")
    p.setFont("Helvetica", 12)
    p.drawString(200, height-380, f"{payment.payment_method}")
    
    p.setFillColor(dark_blue)
    p.rect(50, height-420, width-100, 30, fill=1, stroke=0)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, height-415, "Total")
    p.drawRightString(width-60, height-415, f"{payment.prix} DH")
    
    p.saveState()
    p.setFillColor(green_color)
    p.setFont("Helvetica-Bold", 36)
    p.translate(width/2, height-500)
    p.rotate(15)  # Rotate 15 degrees
    p.drawCentredString(0, 0, "PAYÉ")
    p.restoreState()
    
    p.setFillColor(dark_blue)
    p.setFont("Helvetica", 12)
    thank_you_text = "Merci pour votre paiement. Nous espérons que vous apprécierez votre lecture !"
    p.drawCentredString(width/2, height-550, thank_you_text)
    
    p.setFillColor(colors.gray)
    p.setFont("Helvetica", 9)
    p.drawCentredString(width/2, 50, "ZakBooks - Bibliothèque numérique")
    p.drawCentredString(width/2, 35, "www.zakbooks.com | contact@zakbooks.com | +212 5XX-XXXXXX")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recu_paiement_{payment.id}.pdf"'
    
    return response
