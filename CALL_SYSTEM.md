# Call & Communication System Documentation

## Overview

SilverConnect now includes a comprehensive call logging and communication system that allows users to:
- Make phone calls directly to service vendors and emergency contacts
- Send WhatsApp messages
- Send SMS messages
- Track all communications in a centralized call history
- Format phone numbers consistently

## Features

### 1. **Multiple Communication Methods**

Users can now communicate with vendors and contacts through:
- **Phone Call** - Direct telephone call via `tel:` protocol
- **WhatsApp** - Direct message via WhatsApp web/mobile
- **SMS** - Text message via SMS protocol

### 2. **Phone Number Formatting**

All phone numbers are automatically formatted for better readability:
- Input: `5551234567`
- Output: `+1 (555) 123-4567`

The formatting utility handles various input formats and extracts only digits for call URLs.

### 3. **Call Logging System**

Every communication attempt is logged to the `CallLog` model, tracking:
- Who made the call
- Who they called
- Communication method (Phone/WhatsApp/SMS)
- Phone number called
- Timestamp
- Optional duration (for completed calls)
- User notes

### 4. **Call History**

Users can view their complete communication history at:
- **URL:** `/call/history/`
- **Features:**
  - Filter by type (Phone, WhatsApp, SMS)
  - View timestamps for each call
  - Track which vendors/contacts were called
  - Sort by most recent

## Implementation Details

### Database Models

#### CallLog Model
```python
class CallLog(models.Model):
    user = ForeignKey(User)
    vendor = ForeignKey(ServiceVendor, null=True)
    emergency_contact = ForeignKey(EmergencyContact, null=True)
    phone_number = CharField(max_length=20)
    call_type = CharField(choices=['PHONE_CALL', 'WHATSAPP', 'SMS', 'EMAIL'])
    duration_seconds = PositiveIntegerField(null=True)
    timestamp = DateTimeField(auto_now_add=True)
    notes = TextField(blank=True)
```

### Utilities (base/utils.py)

#### Phone Formatting Functions

**`format_phone_number(phone_number)`**
- Formats phone to consistent format
- Handles US (+1), Indian (+91), and other formats
- Returns formatted string

**`extract_digits(phone_number)`**
- Extracts only digits and leading +
- Used for tel: and WhatsApp links
- Returns clean digits string

**`get_call_url(phone_number, call_type)`**
- Generates appropriate URL for call type
- Returns: `tel:`, `sms:`, or `https://wa.me/` URLs

**`get_call_icon(call_type)`**
- Returns Bootstrap icon class for UI
- Options: bi-telephone-fill, bi-whatsapp, etc.

**`get_call_icon_color(call_type)`**
- Returns Bootstrap color class for styling

### Views

#### log_call() - AJAX Endpoint
- **URL:** `/call/log/<int:vendor_id>/` or `/call/log-contact/<int:contact_id>/`
- **Method:** POST
- **Parameters:**
  - `call_type` - Type of communication (PHONE_CALL, WHATSAPP, SMS)
  - `phone_number` - Phone number called
  - `duration` (optional) - Call duration in seconds
  - `notes` (optional) - User notes
- **Returns:** JSON response with success/error status

#### view_call_history() - User View
- **URL:** `/call/history/`
- **Features:** Displays all calls for logged-in user
- **Filtering:** Optional filter by `?type=PHONE_CALL`

### Templates

#### Service List (`services/service_list.html`)
- Shows formatted phone number
- Three call buttons: Phone, WhatsApp, SMS
- Logs calls via JavaScript

#### Services Hub (`services/hub.html`)
- Top-rated vendors with call options
- Same three communication methods
- Call logging on click

#### Emergency Contacts (`profile/contacts.html`)
- Quick call buttons for each contact
- Three communication methods
- View call history link

#### Call History (`profile/call_history.html`)
- Complete communication log
- Filter by type
- Shows vendor/contact name, phone, timestamp
- Optional duration and notes

## How to Use

### As a User

1. **Making a Call:**
   - Navigate to Services → Category (e.g., Grocery)
   - Click provider's phone number to see options
   - Click **Call**, **📱 WhatsApp**, or **💬 SMS**
   - Device will open appropriate app/call

2. **Viewing Call History:**
   - Go to Profile → Emergency Contacts
   - Click "Call History" button
   - Filter by communication type if desired

### As an Developer

1. **Using Phone Formatting:**
   ```python
   from base.utils import format_phone_number
   formatted = format_phone_number("5551234567")  # +1 (555) 123-4567
   ```

2. **Generating Call URLs:**
   ```python
   from base.utils import get_call_url
   # Phone
   url = get_call_url("5551234567", "PHONE_CALL")  # tel:5551234567
   # WhatsApp
   url = get_call_url("5551234567", "WHATSAPP")  # https://wa.me/5551234567?text=Hello
   # SMS
   url = get_call_url("5551234567", "SMS")  # sms:5551234567
   ```

3. **Using Template Filters:**
   ```django
   {% load phone_filters %}
   {{ phone_number|phone_format }}  {# Formatted display #}
   {{ phone_number|phone_digits }}  {# Extract digits #}
   {{ phone_number|call_url:'WHATSAPP' }}  {# Get WhatsApp URL #}
   ```

4. **Logging a Call:**
   ```python
   from base.models import CallLog
   CallLog.objects.create(
       user=request.user,
       vendor=vendor,
       phone_number="+1 (555) 123-4567",
       call_type="PHONE_CALL"
   )
   ```

## Admin Panel

Access call logs in Django admin:
- **URL:** `/admin/base/calllog/`
- **Features:**
  - View all user calls
  - Filter by type, date, user
  - Search by phone number or contact
  - Edit call notes and duration

## Technical Architecture

### AJAX Call Logging
```javascript
fetch('/call/log/<vendor_id>/', {
    method: 'POST',
    body: `call_type=PHONE_CALL&phone_number=+1-555-123-4567`
})
.then(response => response.json())
.then(data => console.log(data.status)); // 'success' or 'error'
```

### URL Routing
- `/call/log/<int:vendor_id>/` - Log vendor call
- `/call/log-contact/<int:contact_id>/` - Log emergency contact call
- `/call/history/` - View user's call history

### Database Indexing
- CallLog is indexed by user for fast history lookup
- Ordered by `-timestamp` for most recent first

## Future Enhancements

- Video call integration (Zoom/Google Meet)
- Call duration tracking from device
- Two-way SMS system
- Smart contact suggestions
- Call history export (PDF/CSV)
- Automatic vendor recommendation based on call history
- Voice-to-text for messages

## Troubleshooting

**WhatsApp links not working:**
- Extract only digits from phone number (remove symbols)
- Ensure country code is included for international numbers

**SMS not sending:**
- Verify phone number is correctly formatted
- Check device SMS app is default

**Call history shows no data:**
- Ensure you're logged in
- Check that calls are being made from within app
- Verify CSRF token is being sent with AJAX

**Phone formatting issues:**
- Ensure input is a string
- Remove any special characters before processing
- Check country code for non-US numbers

## Files Modified/Created

### Created:
- `base/utils.py` - Phone utilities
- `base/templatetags/phone_filters.py` - Template filters
- `base/templatetags/__init__.py` - Package init
- `base/templates/profile/call_history.html` - Call history page

### Modified:
- `base/models.py` - Added CallLog model
- `base/views.py` - Added call logging views, imported CallLog
- `base/urls.py` - Added call-related URL routes
- `base/admin.py` - Added CallLogAdmin
- `base/templates/services/service_list.html` - Added multi-communication buttons
- `base/templates/services/hub.html` - Added multi-communication buttons
- `base/templates/profile/contacts.html` - Added call buttons and history link

### Migrations:
- `0005_alter_servicevendor_category_calllog.py` - Create CallLog table
