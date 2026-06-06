from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import *

# ==============================================================================
# 1. INLINE ADMIN CLASSES
# ==============================================================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('profile_photo', 'date_of_birth', 'blood_type', 'member_since_year', 'bio', 'address')
    readonly_fields = ('age', 'completion_percentage')

class EmergencyContactInline(admin.TabularInline):
    model = EmergencyContact
    extra = 1
    fields = ('name', 'relationship', 'phone_number', 'is_primary')

class MedicineInline(admin.TabularInline):
    model = Medicine
    extra = 1
    fields = ('name', 'instruction', 'time_of_day', 'is_taken', 'scheduled_date')

class HealthDocumentInline(admin.TabularInline):
    model = HealthDocument
    extra = 1
    fields = ('title', 'doc_type', 'file_attachment')
    readonly_fields = ('created_at',)

# ==============================================================================
# 2. CUSTOM USER ADMIN
# ==============================================================================

class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, EmergencyContactInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_info')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def profile_info(self, obj):
        if hasattr(obj, 'profile'):
            return f"{obj.profile.blood_type or 'N/A'} | {obj.profile.age} yrs"
        return "No Profile"
    profile_info.short_description = 'Profile Info'

# Unregister default User admin and register custom
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# ==============================================================================
# 3. WELLNESS & MEDICAL ADMIN
# ==============================================================================

@admin.register(DailyWellnessLog)
class DailyWellnessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'mood', 'steps_taken', 'sleep_hours', 'water_glasses', 'progress_percentage')
    list_filter = ('date', 'mood', 'user')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('progress_percentage',)
    date_hierarchy = 'date'
    
    fieldsets = (
        ('User & Date', {
            'fields': ('user', 'date')
        }),
        ('Activity Tracking', {
            'fields': ('steps_taken', 'steps_goal', 'progress_percentage')
        }),
        ('Health Metrics', {
            'fields': ('water_glasses', 'sleep_hours', 'mood')
        }),
    )

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'time_of_day', 'instruction', 'is_taken', 'scheduled_date')
    list_filter = ('time_of_day', 'is_taken', 'scheduled_date', 'user')
    search_fields = ('name', 'user__username', 'instruction')
    list_editable = ('is_taken',)
    actions = ['mark_as_taken', 'mark_as_not_taken']
    
    def mark_as_taken(self, request, queryset):
        queryset.update(is_taken=True)
    mark_as_taken.short_description = "Mark selected medicines as taken"
    
    def mark_as_not_taken(self, request, queryset):
        queryset.update(is_taken=False)
    mark_as_not_taken.short_description = "Mark selected medicines as not taken"

@admin.register(HealthDocument)
class HealthDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'doc_type', 'created_at', 'file_link')
    list_filter = ('doc_type', 'created_at', 'user')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at',)
    
    def file_link(self, obj):
        if obj.file_attachment:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file_attachment.url)
        return "No file"
    file_link.short_description = 'File'

# ==============================================================================
# 4. COMMUNITY & SOCIAL ADMIN
# ==============================================================================

class PostCommentInline(admin.TabularInline):
    model = PostComment
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('author', 'text', 'created_at')

@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'content_preview', 'created_at', 'likes_count', 'comments_count')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username', 'author__first_name')
    readonly_fields = ('created_at', 'likes_count', 'comments_count')
    inlines = [PostCommentInline]
    
    fieldsets = (
        (None, {
            'fields': ('author', 'content', 'image')
        }),
        ('Statistics', {
            'fields': ('likes_count', 'comments_count', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    # Actions
    def delete_comments(self, request, queryset):
        for post in queryset:
            post.comments.all().delete()
    delete_comments.short_description = "Delete all comments for selected posts"
    
    actions = [delete_comments]

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post_preview', 'text_preview', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('text', 'author__username', 'post__content')
    readonly_fields = ('created_at',)
    
    def post_preview(self, obj):
        return obj.post.content[:30] + '...' if len(obj.post.content) > 30 else obj.post.content
    post_preview.short_description = 'Post'
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Comment'

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'start_time', 'is_live', 'participants_count')
    list_filter = ('category', 'is_live', 'start_time')
    search_fields = ('title', 'category')
    list_editable = ('is_live',)
    filter_horizontal = ('participants',)
    readonly_fields = ('participants_count',)
    
    fieldsets = (
        ('Event Details', {
            'fields': ('title', 'category', 'image', 'start_time', 'join_link')
        }),
        ('Status & Participants', {
            'fields': ('is_live', 'participants', 'participants_count')
        }),
    )
    
    # Actions
    def make_live(self, request, queryset):
        queryset.update(is_live=True)
    make_live.short_description = "Mark selected events as live"
    
    def make_offline(self, request, queryset):
        queryset.update(is_live=False)
    make_offline.short_description = "Mark selected events as offline"
    
    actions = [make_live, make_offline]

# ==============================================================================
# 5. SERVICES & MARKETPLACE ADMIN
# ==============================================================================

@admin.register(ServiceVendor)
class ServiceVendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'rating', 'delivery_info', 'phone_contact')
    list_filter = ('category', 'rating')
    search_fields = ('name', 'category', 'delivery_info')
    list_editable = ('rating', 'delivery_info')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'category', 'image')
        }),
        ('Contact & Delivery', {
            'fields': ('phone_contact', 'delivery_info', 'rating')
        }),
    )

@admin.register(MarketplaceItem)
class MarketplaceItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'price', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'seller')
    search_fields = ('title', 'description', 'seller__username')
    list_editable = ('status', 'price')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Item Details', {
            'fields': ('seller', 'title', 'description', 'price', 'image')
        }),
        ('Status', {
            'fields': ('status', 'created_at')
        }),
    )
    
    # Actions
    def mark_as_sold(self, request, queryset):
        queryset.update(status='SOLD')
    mark_as_sold.short_description = "Mark selected items as sold"
    
    def mark_as_available(self, request, queryset):
        queryset.update(status='AVAILABLE')
    mark_as_available.short_description = "Mark selected items as available"
    
    actions = [mark_as_sold, mark_as_available]

# ==============================================================================
# 6. HOME & INTERACTIVE ADMIN
# ==============================================================================

@admin.register(VoiceAction)
class VoiceActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'command_preview', 'target_action', 'timestamp')
    list_filter = ('target_action', 'timestamp', 'user')
    search_fields = ('command_text', 'target_action', 'user__username')
    readonly_fields = ('timestamp',)
    
    def command_preview(self, obj):
        return obj.command_text[:30] + '...' if len(obj.command_text) > 30 else obj.command_text
    command_preview.short_description = 'Command'

@admin.register(ActiveMeeting)
class ActiveMeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'is_active', 'started_at', 'meeting_link')
    list_filter = ('is_active', 'started_at')
    search_fields = ('title', 'host__username', 'meeting_url')
    list_editable = ('is_active',)
    readonly_fields = ('started_at',)
    
    def meeting_link(self, obj):
        return format_html('<a href="{}" target="_blank">Join Meeting</a>', obj.meeting_url)
    meeting_link.short_description = 'Link'
    
    # Actions
    def end_meeting(self, request, queryset):
        queryset.update(is_active=False)
    end_meeting.short_description = "End selected meetings"
    
    def start_meeting(self, request, queryset):
        queryset.update(is_active=True)
    start_meeting.short_description = "Start selected meetings"
    
    actions = [end_meeting, start_meeting]

# ==============================================================================
# 6. CALL LOGGING ADMIN
# ==============================================================================

@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'call_type', 'timestamp', 'duration_seconds')
    list_filter = ('call_type', 'timestamp', 'user')
    search_fields = ('user__username', 'phone_number', 'vendor__name', 'emergency_contact__name')
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        ('Communication', {
            'fields': ('user', 'phone_number', 'call_type', 'duration_seconds')
        }),
        ('Related', {
            'fields': ('vendor', 'emergency_contact', 'notes')
        }),
        ('Timestamp', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

# ==============================================================================
# 7. ADMIN SITE CUSTOMIZATION
# ==============================================================================

# Customize admin header
admin.site.site_header = "Senior Care Platform Admin"
admin.site.site_title = "Senior Care Admin Portal"
admin.site.index_title = "Welcome to Senior Care Administration"

admin.site.register(EmergencyContact)

# Register SOSAlert for tracking emergency alerts
@admin.register(SOSAlert)
class SOSAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'emergency_contact', 'status', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('user__username', 'emergency_contact__name')
    readonly_fields = ('user', 'emergency_contact', 'timestamp', 'message')