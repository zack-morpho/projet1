from django.apps import apps
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import modelform_factory
from django.urls import reverse
from django.utils import timezone
from .models import Livre, Utilisateur, Emprunt, Amende, Commentaire, Reservation

def model_list(request):
    app = apps.get_app_config('BibloApp')
    models = list(app.get_models())
    model_tuples = [(model.__name__, model) for model in models]
    total_books = Livre.objects.count()
    total_users = Utilisateur.objects.count()
    total_loans = Emprunt.objects.filter(estRetourne=False).count()
    total_fines = Amende.objects.count()
    total_comments = Commentaire.objects.count()
    total_reservations = Reservation.objects.count()
    connected_user = None
    user_id = request.session.get('user_id')
    if user_id:
        try:
            connected_user = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            connected_user = None
    return render(request, 'dynamic_admin/model_list.html', {
        'model_tuples': model_tuples,
        'total_books': total_books,
        'total_users': total_users,
        'total_loans': total_loans,
        'total_fines': total_fines,
        'total_comments': total_comments,
        'total_reservations': total_reservations,
        'connected_user': connected_user,
    })

def object_list(request, model_name):
    app = apps.get_app_config('BibloApp')
    model = app.get_model(model_name)
    search_query = request.GET.get('search', '').strip()
    if model_name == 'Commentaire' and search_query:
        objects = model.objects.filter(
            livre__titre__icontains=search_query
        ) | model.objects.filter(
            livre__isbn__icontains=search_query
        )
    else:
        objects = model.objects.all()
    fields = [field for field in model._meta.fields]
    object_values = []
    for obj in objects:
        values = [getattr(obj, field.name) for field in fields]
        object_values.append((obj, values))
    models = list(app.get_models())
    model_tuples = [(m.__name__, m) for m in models]
    connected_user = None
    user_id = request.session.get('user_id')
    if user_id:
        try:
            connected_user = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            connected_user = None
    return render(request, 'dynamic_admin/object_list.html', {
        'model': model,
        'objects': objects,
        'model_name': model_name,
        'fields': fields,
        'object_values': object_values,
        'model_tuples': model_tuples,
        'search_query': search_query,
        'connected_user': connected_user,
    })

def object_create(request, model_name):
    app = apps.get_app_config('BibloApp')
    model = app.get_model(model_name)
    ModelForm = modelform_factory(model, exclude=[])
    if request.method == 'POST':
        form = ModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dynamic_admin_object_list', model_name=model_name)
    else:
        form = ModelForm()
    form.instance.pk = None
    models = list(app.get_models())
    model_tuples = [(m.__name__, m) for m in models]
    return render(request, 'dynamic_admin/object_form.html', {
        'form': form,
        'model': model,
        'model_name': model_name,
        'model_tuples': model_tuples,
    })

def object_edit(request, model_name, pk):
    app = apps.get_app_config('BibloApp')
    model = app.get_model(model_name)
    obj = get_object_or_404(model, pk=pk)
    
    if model_name == 'Emprunt' and request.GET.get('toggle_retourne'):
        if not obj.estRetourne:
            obj.estRetourne = True
            obj.save()
            
            livre = obj.livre
            
            reservation_en_attente = Reservation.objects.filter(
                livre=livre, 
                estEffectuee=False
            ).order_by('dateReservation').first()
            
            if reservation_en_attente:
                reservation_en_attente.estEffectuee = True
                reservation_en_attente.save()
                
                from django.utils import timezone
                import datetime
                Emprunt.objects.create(
                    utilisateur=reservation_en_attente.utilisateur,
                    livre=livre,
                    dateEmprunt=timezone.now(),
                    dateRetour=timezone.now() + datetime.timedelta(days=14),
                    estRetourne=False
                )
            else:
                livre.nbExemplaires += 1
                livre.save()
        else:
            obj.estRetourne = False
            obj.save()
        
        return redirect('dynamic_admin_object_list', model_name=model_name)
    
    ModelForm = modelform_factory(model, exclude=[])
    if request.method == 'POST':
        form = ModelForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('dynamic_admin_object_list', model_name=model_name)
    else:
        form = ModelForm(instance=obj)
    models = list(app.get_models())
    model_tuples = [(m.__name__, m) for m in models]
    return render(request, 'dynamic_admin/object_form.html', {
        'form': form,
        'model': model,
        'model_name': model_name,
        'model_tuples': model_tuples,
    })


def object_delete(request, model_name, pk):
    app = apps.get_app_config('BibloApp')
    model = app.get_model(model_name)
    obj = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        obj.delete()
        return redirect('dynamic_admin_object_list', model_name=model_name)
    return render(request, 'dynamic_admin/object_delete.html', {
        'model': model,
        'obj': obj,
        'model_name': model_name
    })


