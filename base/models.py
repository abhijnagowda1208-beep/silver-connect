from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import admin
from datetime import date

# ==============================================================================
# 1. PROFILE & SECURITY
# ==============================================================================

class UserProfile(models.Model):
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    member_since_year = models.PositiveIntegerField(default=2024)
    bio = models.TextField(blank=True, max_length=500, help_text="Short bio for the community profile")
    address = models.TextField(blank=True, help_text="For service deliveries")

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def age(self):
        """Calculates age dynamically for the Medical ID card."""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return "--"
    
    @property
    def completion_percentage(self):
        """Returns how complete the profile is (for gamification)."""
        fields = [self.profile_photo, self.date_of_birth, self.blood_type, self.bio, self.address]
        filled = len([f for f in fields if f])
        return int((filled / len(fields)) * 100)

class EmergencyContact(models.Model):
    RELATIONSHIP_CHOICES = [
        ('Daughter', 'Daughter'), ('Son', 'Son'), 
        ('Spouse', 'Spouse'), ('Doctor', 'Doctor'), 
        ('Neighbor', 'Neighbor'), ('Other', 'Other')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50, choices=RELATIONSHIP_CHOICES)
    phone_number = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False, help_text="This contact receives SOS alerts")

    class Meta:
        ordering = ['-is_primary', 'name']

    def save(self, *args, **kwargs):
        # Ensure only one contact is primary per user
        if self.is_primary:
            EmergencyContact.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.relationship})"

class SOSAlert(models.Model):
    """Model to track SOS alert events sent to emergency contacts."""
    STATUS_CHOICES = [
        ('SENT', 'Sent Successfully'),
        ('FAILED', 'Failed to Send'),
        ('PENDING', 'Pending'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sos_alerts')
    emergency_contact = models.ForeignKey(EmergencyContact, on_delete=models.SET_NULL, null=True, related_name='sos_alerts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SENT')
    message = models.TextField(default="SOS! Emergency help needed.")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"SOS Alert from {self.user.username} to {self.emergency_contact.name} - {self.status}"

# ==============================================================================
# 2. HOME & INTERACTIVE
# ==============================================================================

class VoiceAction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    command_text = models.CharField(max_length=255)
    target_action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

class ActiveMeeting(models.Model):
    title = models.CharField(max_length=100)
    host = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting_url = models.URLField(help_text="Link to Zoom/Google Meet")
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# ==============================================================================
# 3. WELLNESS & MEDICAL
# ==============================================================================

class DailyWellnessLog(models.Model):
    MOOD_CHOICES = [('Happy', 'Happy'), ('Neutral', 'Neutral'), ('Tired', 'Tired'), ('Anxious', 'Anxious')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    
    # Activity
    steps_taken = models.PositiveIntegerField(default=0)
    steps_goal = models.PositiveIntegerField(default=4000)
    
    # Hydration & Sleep
    water_glasses = models.PositiveIntegerField(default=0)
    sleep_hours = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    
    # Vitals
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, default='Neutral')

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    @property
    def progress_percentage(self):
        if self.steps_goal == 0: return 0
        return min(int((self.steps_taken / self.steps_goal) * 100), 100)

class Medicine(models.Model):
    TIME_CHOICES = [
        ('Morning', 'Morning'), ('Afternoon', 'Afternoon'), 
        ('Evening', 'Evening'), ('Night', 'Night')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicines')
    name = models.CharField(max_length=100) 
    instruction = models.CharField(max_length=100, help_text="e.g., After Lunch")
    time_of_day = models.CharField(max_length=20, choices=TIME_CHOICES, default='Morning')
    is_taken = models.BooleanField(default=False)
    scheduled_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['scheduled_date', 'time_of_day']

    def __str__(self):
        return f"{self.name} - {self.time_of_day}"

class HealthDocument(models.Model):
    DOC_TYPES = [('RECORD', 'Health Record'), ('PRESCRIPTION', 'Prescription')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_documents')
    title = models.CharField(max_length=100)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    file_attachment = models.FileField(upload_to='health_docs/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

# ==============================================================================
# 4. COMMUNITY & SOCIAL
# ==============================================================================

# ==============================================================================
# 4. COMMUNITY & SOCIAL
# ==============================================================================

class CommunityPost(models.Model):
    # Relates to User model instead of just storing a string name
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ManyToMany to track exactly WHO liked the post
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comments.count()
    
    # --- FIX FOR ADMIN ERROR ---
    # This property mimics the old 'author_name' field so admin.py doesn't crash
    @admin.display(description='Author Name')
    def author_name(self):
        return self.author.get_full_name() or self.author.username

    def __str__(self):
        return f"Post by {self.author.username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class PostComment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class Event(models.Model):
    CATEGORIES = [('health', 'Health'), ('music', 'Music'), ('spiritual', 'Spiritual'), ('social', 'Social')]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORIES, db_index=True)
    image = models.ImageField(upload_to='events/')
    is_live = models.BooleanField(default=False, db_index=True) 
    start_time = models.DateTimeField(db_index=True)
    join_link = models.URLField(blank=True, help_text="Zoom/Meet Link")
    
    # Tracks actual users who joined
    participants = models.ManyToManyField(User, related_name='joined_events', blank=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['is_live', 'start_time']),
            models.Index(fields=['category', 'start_time']),
        ]

    @property
    def participants_count(self):
        return self.participants.count()

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

# ==============================================================================
# 5. SERVICES & MARKETPLACE
# ==============================================================================

class ServiceVendor(models.Model):
    CAT_CHOICES = [('MEDICAL', 'Medical'), ('GROCERY', 'Grocery'), ('TRANSPORT', 'Transport'), ('HOME CARE', 'Home Care'), ('PHYSIOTHERAPY', 'Physiotherapy')]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CAT_CHOICES)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
    delivery_info = models.CharField(max_length=50, help_text="e.g., '30 mins' or 'Free Delivery'")
    phone_contact = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to='vendors/')

    def __str__(self):
        return self.name

class MarketplaceItem(models.Model):
    STATUS_CHOICES = [('AVAILABLE', 'Available'), ('SOLD', 'Sold')]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_items')
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='marketplace/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (${self.price})"

# ==============================================================================
# 6. CALL LOGGING & COMMUNICATION
# ==============================================================================

class CallLog(models.Model):
    CALL_TYPE_CHOICES = [
        ('PHONE_CALL', 'Phone Call'),
        ('WHATSAPP', 'WhatsApp'),
        ('SMS', 'SMS'),
        ('EMAIL', 'Email'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='call_logs')
    vendor = models.ForeignKey(ServiceVendor, on_delete=models.CASCADE, related_name='call_logs', null=True, blank=True)
    emergency_contact = models.ForeignKey(EmergencyContact, on_delete=models.CASCADE, related_name='call_logs', null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    call_type = models.CharField(max_length=20, choices=CALL_TYPE_CHOICES)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds (for completed calls)")
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="User notes about the call")
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_call_type_display()} to {self.phone_number} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"