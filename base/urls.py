from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from . import views

def redirect_home_or_login(request):
    """Redirect to login page"""
    return redirect('login')

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('members/<str:status>/', views.members_list, name='members_list'),
    # ==========================================================================
    # 0. ADMIN & AUTHENTICATION
    # ==========================================================================
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.sign_out_view, name='logout'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),

    # ==========================================================================
    # 1. HOME & DASHBOARD
    # ==========================================================================
    path('', redirect_home_or_login, name='home'),
    path('dashboard/', views.home_dashboard, name='home_dashboard'),
    path('voice-command/', views.log_voice_command, name='log_voice_command'),
    path('emergency/trigger/', views.trigger_emergency, name='trigger_emergency'),

    # ==========================================================================
    # 2. WELLNESS TRACKER
    # ==========================================================================
    path('wellness/', views.wellness_tracker, name='wellness_tracker'),
    path('wellness/update/<str:metric_type>/', views.update_wellness_metric, name='update_wellness_metric'),
    path('wellness/medicine/add/', views.add_medicine, name='add_medicine'),
    path('wellness/medicine/toggle/<int:med_id>/', views.toggle_medicine, name='toggle_medicine'),
    path('wellness/medicine/delete/<int:med_id>/', views.delete_medicine, name='delete_medicine'),

    # ==========================================================================
    # 3. COMMUNITY & EVENTS
    # ==========================================================================
    path('community/', views.community_feed, name='community_feed'),
    path('community/post/create/', views.create_post, name='create_post'),
    path('community/post/like/<int:post_id>/', views.like_post, name='like_post'),
    path('community/events/', views.event_list, name='event_list'),
    path('community/events/join/<int:event_id>/', views.join_event_room, name='join_event_room'),
    path('community/event/<int:id>/', views.event_detail, name='event_detail'),
    

    # ==========================================================================
    # 4. MARKETPLACE & SERVICES
    # ==========================================================================
    path('services/', views.services_hub, name='services_hub'),
    path('services/<str:category>/', views.service_list, name='service_list'),

    path('marketplace/', views.marketplace_list, name='marketplace_list'),
    path('marketplace/sell/', views.add_marketplace_item, name='add_marketplace_item'),
    path('marketplace/sold/<int:item_id>/', views.mark_item_sold, name='mark_item_sold'),

    # ==========================================================================
    # 5. PROFILE & RECORDS
    # ==========================================================================
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/upload/', views.upload_record, name='upload_record'),

    path('profile/contacts/', views.manage_emergency_contacts, name='manage_emergency_contacts'),
    path('profile/contacts/add/', views.add_emergency_contact, name='add_emergency_contact'),
    path('profile/contacts/primary/<int:contact_id>/', views.set_primary_contact, name='set_primary_contact'),
    path('profile/contacts/delete/<int:contact_id>/', views.delete_contact, name='delete_contact'),
    path('sos/history/', views.sos_history, name='sos_history'),

    # ==========================================================================
    # 6. CALL LOGGING & COMMUNICATION
    # ==========================================================================
    path('call/log/<int:vendor_id>/', views.log_call, name='log_call_vendor'),
    path('call/log-contact/<int:contact_id>/', views.log_call, name='log_call_contact'),
    path('call/history/', views.view_call_history, name='call_history'),
]

# ==========================================================================
# 6. MEDIA & STATIC FILES (DEV ONLY)
# ==========================================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)