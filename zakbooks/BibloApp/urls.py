from django.urls import path
from . import views
from . import account_views
from . import Amende
from . import dynamic_admin
from . import dynamic_admin_views
from .views import aide_view

urlpatterns = [
    path('', dynamic_admin.model_list, name='dynamic_admin_model_list'),
    path('<str:model_name>/', dynamic_admin.object_list, name='dynamic_admin_object_list'),
    path('<str:model_name>/add/', dynamic_admin.object_create, name='dynamic_admin_object_create'),
    path('<str:model_name>/<int:pk>/edit/', dynamic_admin.object_edit, name='dynamic_admin_object_edit'),
    path('<str:model_name>/<int:pk>/delete/', dynamic_admin.object_delete, name='dynamic_admin_object_delete'),
    path('reservation/<int:reservation_id>/annuler/', dynamic_admin_views.admin_cancel_reservation, name='dynamic_admin_cancel_reservation'),
    path('<str:model_name>/export-csv/', dynamic_admin_views.export_csv, name='dynamic_admin_export_csv'),
]



urlpatterns += [
    path('compte/', views.mon_compte_view, name='mon-compte'),
    path('compte/reservations/', account_views.user_reservations, name='user-reservations'),
    path('compte/emprunts/', account_views.user_emprunts, name='user-emprunts'),
    path('compte/amendes/', Amende.user_amendes, name='user-amendes'),
    path('compte/messages/', account_views.user_messages, name='user-messages'),
    path('compte/messages/<int:message_id>/marquer-lu/', account_views.mark_message_read, name='mark-message-read'),
    path('compte/amendes/<int:amende_id>/payer/', Amende.pay_fine, name='pay-fine'),
    path('compte/reservations/<int:reservation_id>/annuler/', account_views.cancel_reservation, name='cancel-reservation'),
    path('compte/recu-paiement/<int:payment_id>/', account_views.download_receipt, name='download_receipt'),
    path('compte/recu-paiement/', account_views.user_receipts, name='RecuDePaiement'),
    path('admin/check-overdue-books/', Amende.check_overdue_books, name='check-overdue-books'),
]

urlpatterns += [
    path('admin/messages/', account_views.admin_messages, name='admin-messages'),
    path('admin/messages/envoyer/', account_views.send_message, name='admin-send-message'),
    path('admin/messages/envoyer/<int:user_id>/', account_views.send_message, name='admin-send-message-to-user'),
    path('admin/reservations/', account_views.user_reservations, name='admin-reservations'),  # Réutilisation de la vue user_reservations avec un template différent
]

urlpatterns += [
    path('aide/', aide_view, name='aide'),
]