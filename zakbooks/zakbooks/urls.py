"""
URL configuration for zakbooks project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from BibloApp import views
from django.contrib.auth import views as auth_views
from BibloApp.views import signup_view, login_view, logout_view, mon_compte_view, aide_view
from django.conf import settings
from django.conf.urls.static import static
from BibloApp import views
from BibloApp.views import home_view, signup_view, login_view, logout_view
from BibloApp.books import book_detail, search, livres_par_categorie, book_par_cat
from BibloApp.emprunt import emprunter_livre, payer_emprunt, payment_emprunt
from BibloApp import Reserver
from BibloApp.dynamic_admin_views import statistical_reports

urlpatterns = [
    path('home/', views.home_view, name='home'),
    path('signup/', signup_view, name='signup'),
    path('', login_view, name='login'),  
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('search/', search, name='search'),
    path('book/<str:isbn>/', book_detail, name='book_detail'),
    path('categorie/<str:categorie_code>/', livres_par_categorie, name='livres_par_categorie'),
    path('emprunter/<str:isbn>/', emprunter_livre, name='emprunter_livre'),
    path('dynamic-admin/rapports-statistiques/', statistical_reports, name='statistical_reports'),
    path('dynamic-admin/', include('BibloApp.urls')),
    path('payer-emprunt/<str:isbn>/', payer_emprunt, name='payer_emprunt'),
    path('payment-emprunt/<str:isbn>/', payment_emprunt, name='payment_emprunt'),
    path('mon-compte/', mon_compte_view, name='mon-compte'),  # Changed from 'mon_compte' to 'mon-compte'
    path('reserver_livre/<str:isbn>/', Reserver.reserver_livre, name='reserver_livre'),
    path('payer_reservation/<str:isbn>/', Reserver.payer_reservation, name='payer_reservation'),
    path('book_par_cat/<str:categorie_code>/', book_par_cat, name='book_par_cat'),
    path('aide/', aide_view, name='aide'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
