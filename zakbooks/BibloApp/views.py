from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from BibloApp.forms import SignupForm, LoginForm
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from BibloApp.models import Livre, Utilisateur, Reservation, Emprunt, Amende, Message
from BibloApp.models import Livre as Book
from django.contrib.auth import logout as auth_logout
from django.db.models import Exists, OuterRef, Value
from django.contrib import messages
from django.utils import timezone


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = Utilisateur(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                nom=form.cleaned_data['nom'],
                prenom=form.cleaned_data['prenom'],
                role='USER',  
                password=make_password(form.cleaned_data['password'])  
            )
            user.save()
            
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['role'] = user.role
            request.session['connected_user'] = {
                'id': user.id,
                'username': user.username,
                'nom': user.nom,
                'prenom': user.prenom,
                'email': user.email,
                'role': user.role
            }
            
            return redirect('home')
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                user = Utilisateur.objects.get(username=username)

                if check_password(password, user.password):
                    request.session['user_id'] = user.id
                    request.session['username'] = user.username
                    request.session['role'] = user.role
                    request.session['connected_user'] = {
                        'id': user.id,
                        'username': user.username,
                        'nom': user.nom,
                        'prenom': user.prenom,
                        'email': user.email,
                        'role': user.role
                    }

                    return redirect('home')
                else:
                    form.add_error(None, "Invalid username or password")
            except Utilisateur.DoesNotExist:
                form.add_error(None, "user does not exist")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    request.session.flush()
    auth_logout(request)
    return redirect('login')

def home_view(request):
    user_id = request.session.get('user_id')
    
    books = Book.objects.annotate(
        is_reserved_by_user=Exists(
            Reservation.objects.filter(
                livre=OuterRef('pk'),
                utilisateur_id=user_id
            )
        ) if user_id else Value(False)
    )
    
    return render(request, 'application/home.html', {'books': books})


def mon_compte_view(request):
    """View for user account management"""
    if not request.session.get('user_id'):
        return redirect('login')
    
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')
    
    if user_role == 'ADMIN':
        messages.info(request, "Les administrateurs doivent utiliser l'interface d'administration.")
        return redirect('dynamic_admin_model_list')
    
    user = get_object_or_404(Utilisateur, id=user_id)
    form_errors = []
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            email = request.POST.get('email')
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            username = request.POST.get('username')
            
            if email != user.email and Utilisateur.objects.filter(email=email).exists():
                form_errors.append("Cet email est déjà utilisé par un autre compte.")
            
            if username != user.username and Utilisateur.objects.filter(username=username).exists():
                form_errors.append("Ce nom d'utilisateur est déjà utilisé par un autre compte.")
            
            if not form_errors:
                user.email = email
                user.nom = nom
                user.prenom = prenom
                user.username = username
                user.save()
                
                request.session['connected_user'] = {
                    'id': user.id,
                    'username': user.username,
                    'nom': user.nom,
                    'prenom': user.prenom,
                    'email': user.email,
                    'role': user.role
                }
                messages.success(request, "Votre profil a été mis à jour avec succès.")
        
        elif 'change_password' in request.POST:
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not check_password(current_password, user.password):
                form_errors.append("Le mot de passe actuel est incorrect.")
            
            if new_password != confirm_password:
                form_errors.append("Les nouveaux mots de passe ne correspondent pas.")
            
            if len(new_password) < 8:
                form_errors.append("Le nouveau mot de passe doit contenir au moins 8 caractères.")
            
            if not form_errors:
                user.password = make_password(new_password)
                user.save()
                messages.success(request, "Votre mot de passe a été changé avec succès.")

    reservations = user.reservations.all().select_related('livre')

    emprunts = user.emprunts.all().select_related('livre')

    from django.utils import timezone
    today = timezone.now().date()
    
    for emprunt in emprunts:
        emprunt.is_overdue = emprunt.estEnRetard
    
    amendes = user.amendes.all()
    
    user_messages = user.messages.all()
    
    context = {
        'user': user,
        'reservations': reservations,
        'emprunts': emprunts,
        'amendes': amendes,
        'user_messages': user_messages,
        'form_errors': form_errors,
        'active_tab': 'profile',
    }
    
    return render(request, 'accounts/MonCompte.html', context)


def aide_view(request):
    return render(request, 'application/aide.html')
