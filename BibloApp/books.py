from django.shortcuts import render, redirect
from BibloApp.models import Livre as Book
from .models import Livre
from django.shortcuts import get_object_or_404
from .forms import CommentaireForm
from .models import Commentaire, Utilisateur, Reservation
from django.contrib import messages


def search(request):
    query = request.GET.get('query', '')
    result = None
    
    if query:
        books = Book.objects.all().values()
        for book in books:
            if (query.lower() in book['titre'].lower() or
                query.lower() in book['auteur'].lower() or
                query == str(book['isbn'])):
                result = book
                break
    
    return render(request, 'application/search_result.html', {'result': result, 'query': query})



def book_detail(request, isbn):
    book = get_object_or_404(Livre, isbn=isbn)
    commentaires = Commentaire.objects.filter(livre=book)
    form = CommentaireForm()
    user_id = request.session.get('user_id')
    utilisateur = None
    if user_id:
        try:
            utilisateur = Utilisateur.objects.get(id=user_id)
            book.is_reserved_by_user = Reservation.objects.filter(
                livre=book,
                utilisateur=utilisateur
            ).exists()
        except Utilisateur.DoesNotExist:
            utilisateur = None
            book.is_reserved_by_user = False
    else:
        book.is_reserved_by_user = False
    
    if request.method == 'POST' and utilisateur:
        form = CommentaireForm(request.POST)
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.livre = book
            commentaire.utilisateur = utilisateur
            commentaire.save()
            return redirect('book_detail', isbn=book.isbn)
        else:
            messages.error(request, "Erreur lors de l'ajout du commentaire.")
    elif request.method == 'POST' and not utilisateur:
        return redirect('book_detail', isbn=book.isbn)

    return render(request, 'application/book_detail.html', {
        'book': book,
        'commentaires': commentaires,
        'form': form
    })

def categories_processor(request):
    categories = dict(Livre.CATEGORY_CHOICES)
    return {'categories': categories.items()}

def livres_par_categorie(request, categorie_code):
    categories = dict(Livre.CATEGORY_CHOICES)
    
    if categorie_code == 'ALL':
        livres = Livre.objects.all()
        categorie_nom = 'Tous les livres'
    else:
        livres = Livre.objects.filter(categorie=categorie_code)
        categorie_nom = categories.get(categorie_code, categorie_code)
    
    return render(request, 'application/livres_par_categorie.html', {
        'livres': livres,
        'categorie_nom': categorie_nom,
    })

def book_par_cat(request, categorie_code):
    categories = dict(Livre.CATEGORY_CHOICES)
    
    if categorie_code == 'ALL':
        books_by_category = {}
        
        for cat_code, cat_name in categories.items():
            cat_books = Livre.objects.filter(categorie=cat_code)
            if cat_books.exists():  
                books_by_category[cat_name] = cat_books
        
        user_id = request.session.get('user_id')
        if user_id:
            from .models import Reservation
            for category_books in books_by_category.values():
                for book in category_books:
                    book.is_reserved_by_user = Reservation.objects.filter(
                        livre=book, utilisateur_id=user_id, estEffectuee=False, estAnnulee=False
                    ).exists()
        
        return render(request, 'application/book_par_cat.html', {
            'books_by_category': books_by_category,
        })
    else:
        livres = Livre.objects.filter(categorie=categorie_code)
        categorie_nom = categories.get(categorie_code, categorie_code)
        
        return render(request, 'application/livres_par_categorie.html', {
            'livres': livres,
            'categorie_nom': categorie_nom,
        })