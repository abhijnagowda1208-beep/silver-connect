from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from .models import (
    UserProfile, EmergencyContact, VoiceAction, ActiveMeeting,
    DailyWellnessLog, Medicine, HealthDocument, CommunityPost,
    Event, ServiceVendor, MarketplaceItem, PostComment, CallLog
)
# ==============================================================================
# 1. AUTHENTICATION & ONBOARDING
# ==============================================================================

def signup_view(request):
    """
    Handles new user registration and automatically creates an associated UserProfile.
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Auto-create profile to ensure consistent dashboard experience
            UserProfile.objects.create(
                user=user,
                member_since_year=timezone.now().year
            )
            login(request, user)
            messages.success(request, "Registration successful! Welcome to the community.")
            return redirect('home_dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def sign_out_view(request):
    """
    Safely logs the user out and redirects to the login page.
    """
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

# ==============================================================================
# 2. HOME & QUICK ACTIONS
# ==============================================================================

@login_required
def home_dashboard(request):
    """
    Displays the primary dashboard including greetings and quick action tiles.
    """
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Check for active meetings
    active_meeting = ActiveMeeting.objects.filter(is_active=True).first()
    
    # Get today's progress for the quick view
    today = timezone.now().date()
    log, _ = DailyWellnessLog.objects.get_or_create(user=request.user, date=today)
    
    return render(request, 'dashboard/home.html', {
        'profile': profile,
        'active_meeting': active_meeting,
        'wellness_progress': log.progress_percentage
    })

@login_required
def log_voice_command(request):
    """
    Captures and logs text from the 'Tap to Speak' voice interaction widget.
    """
    if request.method == "POST":
        command = request.POST.get('command', '').lower()
        
        # Basic logic to suggest target actions based on keywords
        target = "PENDING"
        redirect_url = None

        if "wellness" in command or "health" in command:
            target = "wellness_tracker"
            redirect_url = "/wellness/"
        elif "event" in command or "calendar" in command: 
            target = "event_list"
            redirect_url = "/community/events/"
        elif "emergency" in command or "help" in command:
            target = "trigger_emergency"
            # We don't auto-redirect to emergency for safety, just log it
            
        VoiceAction.objects.create(user=request.user, command_text=command, target_action=target)
        
        return JsonResponse({
            'status': 'success', 
            'redirect_suggestion': target,
            'redirect_url': redirect_url
        })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def trigger_emergency(request):
    """
    High-priority logic that triggers an SOS alert to the user's primary emergency contact.
    Creates a log of the SOS alert and sends email notification to the emergency contact.
    """
    from .models import SOSAlert
    from django.core.mail import send_mail
    
    primary = EmergencyContact.objects.filter(user=request.user, is_primary=True).first()
    
    if request.method == "POST":
        if primary:
            # Log the SOS alert in the database
            sos_alert = SOSAlert.objects.create(
                user=request.user,
                emergency_contact=primary,
                status='SENT',
                message=f"SOS! {request.user.get_full_name() or request.user.username} needs emergency help. Location: {request.user.profile.address or 'Address not set'}."
            )
            
            # Prepare email content
            user_name = request.user.get_full_name() or request.user.username
            user_address = request.user.profile.address or "Address not set in profile"
            user_email = request.user.email or "No email on file"
            alert_time = sos_alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            subject = f"EMERGENCY SOS ALERT from {user_name}"
            
            # HTML email body
            html_message = f"""<html><body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; background-color: #fff; padding: 20px; border: 2px solid #dc3545; border-radius: 8px;">
                    <h1 style="color: #dc3545;">EMERGENCY SOS ALERT</h1>
                    <p><strong>Person Needing Help:</strong> {user_name}</p>
                    <p><strong>Profile:</strong> {request.user.username}</p>
                    <p><strong>Email:</strong> {user_email}</p>
                    <p><strong>Your Relationship:</strong> {primary.relationship}</p>
                    <hr>
                    <p><strong>Location:</strong> {user_address}</p>
                    <hr>
                    <p><strong>Alert ID:</strong> #{sos_alert.id}</p>
                    <p><strong>Time:</strong> {alert_time}</p>
                    <p style="color: #28a745; font-weight: bold;">Status: ACTIVE</p>
                    <hr>
                    <h3 style="color: #dc3545;">URGENT ACTION NEEDED:</h3>
                    <ul>
                        <li>Contact {user_name} immediately</li>
                        <li>Verify emergency status and location</li>
                        <li>Call 911 if needed</li>
                        <li>Provide assistance if possible</li>
                    </ul>
                </div>
            </body></html>"""
            
            # Plain text fallback
            text_message = f"""EMERGENCY SOS ALERT

Person Needing Help: {user_name}
Profile: {request.user.username}
Email: {user_email}
Relationship: {primary.relationship}

Location: {user_address}

Alert ID: #{sos_alert.id}
Time: {alert_time}

URGENT: Contact {user_name} immediately and call 911 if needed."""
            
            try:
                # Send email to emergency contact
                send_mail(
                    subject=subject,
                    message=text_message,
                    from_email='noreply@silverconnect.local',
                    recipient_list=[primary.phone_number],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                # Log to console
                print("\n" + "="*70)
                print("SOS ALERT TRIGGERED & NOTIFICATION SENT")
                print("="*70)
                print(f"Alert ID: {sos_alert.id}")
                print(f"From: {user_name} ({request.user.username})")
                print(f"To: {primary.name} ({primary.relationship})")
                print(f"Contact: {primary.phone_number}")
                print(f"Time: {alert_time}")
                print(f"Status: NOTIFICATION SENT")
                print("="*70 + "\n")
                
                # Show success message
                messages.error(request, f"SOS ALERT SENT to {primary.name}! Your emergency contact has been notified.")
            except Exception as e:
                print(f"\nError sending SOS email: {str(e)}\n")
                messages.warning(request, f"SOS Alert logged. Contact {primary.name} at {primary.phone_number} directly if needed.")
        else:
            messages.warning(request, "No primary contact set. Go to Profile > Safety Network > Manage to set one.")
            
    return redirect('home_dashboard')

# ==============================================================================
# 3. COMMUNITY & LIVE EVENTS
# ==============================================================================

@login_required
def community_feed(request):
    category = request.GET.get('category')
    now = timezone.now()

    # Base queryset: only upcoming events (removes 2025 & past)
    # Optimized query with pagination to prevent loading lag
    events = Event.objects.filter(start_time__gte=now).prefetch_related('participants')

    # Apply category filter IF selected
    if category:
        events = events.filter(category__iexact=category)
    
    # Limit to 50 events to prevent performance issues
    events = events[:50]

    # Live events (limited to 10 for performance)
    live_events = Event.objects.filter(
        is_live=True,
        start_time__lte=now
    ).prefetch_related('participants')

    if category:
        live_events = live_events.filter(category__iexact=category)
    
    # Limit to 10 live events
    live_events = live_events[:10]

    context = {
        'events': events,
        'live_events': live_events,
        'selected_category': category,
    }

    return render(request, 'community/events.html', context)

@login_required
def event_detail(request, id):
    event = get_object_or_404(Event.objects.prefetch_related('participants'), id=id)
    return render(request, 'community/event_detail.html', {'event':event})

@login_required
def create_post(request):
    """
    Handles the creation of new text or image posts for the Community Wall.
    """
    if request.method == "POST":
        content = request.POST.get('content')
        image = request.FILES.get('image')
        if content:
            CommunityPost.objects.create(
                author=request.user,
                content=content,
                image=image
            )
            messages.success(request, "Your post is live!")
        else:
            messages.error(request, "Post cannot be empty.")
    return redirect('community_feed')

@login_required
def like_post(request, post_id):
    """
    Toggles the like status for a post.
    """
    post = get_object_or_404(CommunityPost, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect('community_feed')

@login_required
def event_list(request):
    """
    Displays categorized lists of Live (Happening Now) and Upcoming events.
    Optimized with prefetch_related and limited results.
    """
    now = timezone.now()
    live = Event.objects.filter(is_live=True).prefetch_related('participants')[:10]
    upcoming = Event.objects.filter(is_live=False, start_time__gt=now).order_by('start_time').prefetch_related('participants')[:50]
    
    return render(request, 'community/events.html', {
        'live_events': live,
        'upcoming_events': upcoming
    })

@login_required
def join_event_room(request, event_id):
    """
    Increments participant counts and redirects the user to the event's meeting link.
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Add user to participants if not already added
    if request.user not in event.participants.all():
        event.participants.add(request.user)
        
    if event.join_link:
        return redirect(event.join_link)
    else:
        messages.info(request, "This event does not have a video link yet.")
        return redirect('event_list')

# ==============================================================================
# 4. WELLNESS & MEDICINE TRACKING (CRUD)
# ==============================================================================

@login_required
def wellness_tracker(request):
    """
    Displays daily wellness metrics and medicines.
    """
    today = timezone.now().date()
    log, _ = DailyWellnessLog.objects.get_or_create(user=request.user, date=today)
    
    # Get medicines, sorted by time of day (Morning -> Night)
    medicines = Medicine.objects.filter(user=request.user, scheduled_date=today).order_by('time_of_day')
    
    return render(request, 'wellness/tracker.html', {
        'log': log,
        'progress': log.progress_percentage,
        'medicines': medicines
    })

@login_required
def add_medicine(request):
    """
    CRUD: Add a new medicine.
    """
    if request.method == "POST":
        name = request.POST.get('name')
        instruction = request.POST.get('instruction')
        time_of_day = request.POST.get('time_of_day') # Morning, Evening, etc.
        
        Medicine.objects.create(
            user=request.user,
            name=name,
            instruction=instruction,
            time_of_day=time_of_day,
            scheduled_date=timezone.now().date()
        )
        messages.success(request, "Medicine added to schedule.")
        return redirect('wellness_tracker')
    return render(request, 'wellness/add_medicine.html')

@login_required
def delete_medicine(request, med_id):
    """
    CRUD: Delete a medicine entry.
    """
    med = get_object_or_404(Medicine, id=med_id, user=request.user)
    med.delete()
    messages.success(request, "Medicine removed.")
    return redirect('wellness_tracker')

@login_required
def toggle_medicine(request, med_id):
    """
    Updates the status of a specific medicine as taken or not taken.
    """
    med = get_object_or_404(Medicine, id=med_id, user=request.user)
    med.is_taken = not med.is_taken
    med.save()
    return redirect('wellness_tracker')

@login_required
def update_wellness_metric(request, metric_type):
    """
    Increments metrics like water intake or steps for the current day.
    """
    today = timezone.now().date()
    log, _ = DailyWellnessLog.objects.get_or_create(user=request.user, date=today)
    
    if metric_type == 'water':
        log.water_glasses += 1
    elif metric_type == 'steps':
        log.steps_taken += 500
    
    log.save()
    return redirect('wellness_tracker')

# ==============================================================================
# 5. SERVICES & MARKETPLACE (CRUD)
# ==============================================================================

@login_required
def services_hub(request):
    """
    Displays service vendor categories and recommended providers.
    """
    vendors = ServiceVendor.objects.all().order_by('-rating')
    return render(request, 'services/hub.html', {'vendors': vendors})

@login_required
def marketplace_list(request):
    """
    Displays marketplace items with optional search filtering.
    """
    query = request.GET.get('q')
    items = MarketplaceItem.objects.filter(status='AVAILABLE').order_by('-created_at')
    
    if query:
        items = items.filter(Q(title__icontains=query) | Q(description__icontains=query))
    
    return render(request, 'services/marketplace.html', {'items': items, 'query': query})

@login_required
def service_list(request, category):
    CATEGORY_MAP = {
        'grocery': 'GROCERY',
        'medical': 'MEDICAL',
        'transport': 'TRANSPORT',
        'home-care': 'HOME CARE',
    }

    db_category = CATEGORY_MAP.get(category)

    vendors = ServiceVendor.objects.filter(category=db_category).order_by('-rating')

    print("URL category:", category)
    print("DB category used:", db_category)
    print("Vendors found:", vendors.count())

    return render(request, 'services/service_list.html', {
        'category': db_category,
        'vendors': vendors
    })

@login_required
def add_marketplace_item(request):
    """
    CRUD: Handles the creation of new marketplace items.
    """
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        
        MarketplaceItem.objects.create(
            seller=request.user,
            title=title,
            description=description,
            price=price,
            image=image,
            status='AVAILABLE'
        )
        messages.success(request, "Your craft is now live in the marketplace!")
        return redirect('marketplace_list')
    return render(request, 'services/sell_form.html')

@login_required
def mark_item_sold(request, item_id):
    """
    CRUD: Update item status to SOLD.
    """
    item = get_object_or_404(MarketplaceItem, id=item_id, seller=request.user)
    item.status = 'SOLD'
    item.save()
    messages.success(request, "Item marked as sold.")
    return redirect('marketplace_list')

# ==============================================================================
# 6. PROFILE & RECORDS (CRUD)
# ==============================================================================

@login_required
def profile_view(request):
    """
    Renders the main profile view showing age, blood type, and health record summaries.
    """
    profile = get_object_or_404(UserProfile, user=request.user)
    doc_count = HealthDocument.objects.filter(user=request.user).count()
    
    return render(request, 'profile/view.html', {
        'profile': profile,
        'doc_count': doc_count
    })

@login_required
def edit_profile(request):
    """
    CRUD: Edit user profile details.
    """
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == "POST":
        profile.bio = request.POST.get('bio')
        profile.address = request.POST.get('address')
        # Handle date parsing safely in a real app
        dob = request.POST.get('date_of_birth')
        if dob: profile.date_of_birth = dob
        
        if request.FILES.get('profile_photo'):
            profile.profile_photo = request.FILES.get('profile_photo')
            
        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('profile_view')
        
    return render(request, 'profile/edit.html', {'profile': profile})

@login_required
def manage_emergency_contacts(request):
    """
    Logic for users to view and manage their emergency contact list.
    """
    contacts = EmergencyContact.objects.filter(user=request.user)
    return render(request, 'profile/contacts.html', {'contacts': contacts})

@login_required
def add_emergency_contact(request):
    """
    CRUD: Add a new emergency contact.
    """
    if request.method == "POST":
        name = request.POST.get('name')
        relationship = request.POST.get('relationship')
        phone = request.POST.get('phone_number')
        
        # If this is their first contact, make it primary automatically
        is_first = not EmergencyContact.objects.filter(user=request.user).exists()
        
        EmergencyContact.objects.create(
            user=request.user,
            name=name,
            relationship=relationship,
            phone_number=phone,
            is_primary=is_first
        )
        messages.success(request, "Emergency contact added.")
        return redirect('manage_emergency_contacts')
    return render(request, 'profile/add_contact.html')

@login_required
def set_primary_contact(request, contact_id):
    """
    CRUD: Update which contact is primary.
    """
    contact = get_object_or_404(EmergencyContact, id=contact_id, user=request.user)
    contact.is_primary = True
    contact.save() # The model's save() method handles unsetting other primaries
    messages.success(request, f"{contact.name} is now your primary SOS contact.")
    return redirect('manage_emergency_contacts')

@login_required
def delete_contact(request, contact_id):
    """
    CRUD: Remove an emergency contact.
    """
    contact = get_object_or_404(EmergencyContact, id=contact_id, user=request.user)
    contact.delete()
    messages.success(request, "Contact removed.")
    return redirect('manage_emergency_contacts')

@login_required
def upload_record(request):
    """
    Handles uploading of lab reports or prescriptions.
    """
    if request.method == "POST":
        HealthDocument.objects.create(
            user=request.user,
            title=request.POST.get('title'),
            doc_type=request.POST.get('doc_type'),
            file_attachment=request.FILES.get('file')
        )
        messages.success(request, "Document uploaded successfully.")
        return redirect('profile_view')
    return render(request, 'profile/upload.html')

# ==============================================================================
# 7. ADMIN DASHBOARD (MEMBERS OVERVIEW)
# ==============================================================================

@login_required
def admin_dashboard(request):
    # 🔒 Allow ONLY this username
    if request.user.username != "admin23":
        messages.error(request, "You are not authorized to access this dashboard.")
        return redirect('home_dashboard')

    total_members = User.objects.count()
    active_members = User.objects.filter(is_active=True).count()
    inactive_members = User.objects.filter(is_active=False).count()

    context = {
        'total_members': total_members,
        'active_members': active_members,
        'inactive_members': inactive_members,
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
def members_list(request, status):
    if status == "active":
        users = User.objects.filter(is_active=True)
        title = "Active Members"
    elif status == "inactive":
        users = User.objects.filter(is_active=False)
        title = "Inactive Members"
    else:
        users = User.objects.all()
        title = "All Members"

    context = {
        "users": users,
        "title": title
    }

    return render(request, "admin/members_list.html", context)

# ==============================================================================
# 6. CALL LOGGING & COMMUNICATION
# ==============================================================================

@login_required
def log_call(request, vendor_id=None, contact_id=None):
    """
    Logs a call made through the app (phone, WhatsApp, SMS, etc).
    Called via AJAX from service and contact pages.
    """
    if request.method == "POST":
        call_type = request.POST.get('call_type', 'PHONE_CALL')
        phone_number = request.POST.get('phone_number')
        duration = request.POST.get('duration')
        notes = request.POST.get('notes', '')
        
        vendor = None
        emergency_contact = None
        
        if vendor_id:
            vendor = get_object_or_404(ServiceVendor, id=vendor_id)
        elif contact_id:
            emergency_contact = get_object_or_404(EmergencyContact, id=contact_id, user=request.user)
        
        if phone_number:
            CallLog.objects.create(
                user=request.user,
                vendor=vendor,
                emergency_contact=emergency_contact,
                phone_number=phone_number,
                call_type=call_type,
                duration_seconds=int(duration) if duration else None,
                notes=notes
            )
            
            return JsonResponse({
                'status': 'success',
                'message': f'{call_type.replace("_", " ")} logged successfully'
            })
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def view_call_history(request):
    """
    Displays the user's call history and communication logs.
    """
    calls = CallLog.objects.filter(user=request.user)
    
    # Optional filtering
    call_type = request.GET.get('type')
    if call_type:
        calls = calls.filter(call_type=call_type)
    
    return render(request, 'profile/call_history.html', {'calls': calls})

@login_required
def sos_history(request):
    """
    Displays all SOS alerts triggered by the user.
    """
    from .models import SOSAlert
    
    sos_alerts = SOSAlert.objects.filter(user=request.user).order_by('-timestamp')
    
    return render(request, 'profile/sos_history.html', {
        'sos_alerts': sos_alerts,
        'total_sos_count': sos_alerts.count()
    })