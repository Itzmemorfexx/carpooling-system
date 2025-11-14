from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Ride, RideRequest, RideReview, Notification
import datetime
from datetime import date

class TimeInput(forms.TimeInput):
    input_type = 'time'

    def __init__(self, attrs=None, format=None):
        attrs = attrs or {}
        attrs.update({
            'class': 'form-control',
            'placeholder': 'HH:MM AM/PM',
            'step' : '300',    
        })
        super().__init__(attrs, format='%H:%M')

    def format_value(self, value):
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                if ':' in value and len(value.split(':')) == 2:
                    return value
                time_obj = datetime.datetime.strptime(value, '%I:%M %p').time()
                return time_obj.strftime('%H:%M')
            except ValueError:
                return value
        
        return value.strftime('%H:%M')
        

    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)
        if not value:
            return None
        
        try:
            if ':' in value and len(value.split(':')) == 2:
                hours, minutes = value.split(':')
                return datetime.time(int(hours), int(minutes))
        except (ValueError, IndexError):
            pass
        
        return None
                                                            

class RideForm(forms.ModelForm):
    class Meta:
        model = Ride
        fields = ['pickup_location', 'destination', 'departure_date', 'departure_time', 
                 'available_seats', 'price_per_seat', 'car_model', 'car_color', 'car_number']
        widgets = {
            'departure_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),
            'departure_time': TimeInput(attrs={
                'class': 'form-control',
                'step': '900',  # 15-minute intervals
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        departure_date = cleaned_data.get('departure_date')
        departure_time = cleaned_data.get('departure_time')

        if departure_date and departure_time:
            
            print(f"Raw date input: {departure_date}")
            print(f"Raw time input: {departure_time}")
            # Combine date and time into a datetime object
            departure_datetime = timezone.datetime.combine(departure_date, departure_time)
            
            # Make departure_datetime timezone-aware
            departure_datetime = timezone.make_aware(departure_datetime)
            
            # Get current datetime (already timezone-aware)
            current_datetime = timezone.now()
            
            print(f"Combined datetime: {departure_datetime}")
            print(f"Current datetime: {current_datetime}")
            print(f"Is Future? {departure_datetime > current_datetime}")
            
            # If the departure is in the past, raise validation error
            if departure_datetime <= current_datetime:
                raise ValidationError("Departure date and time must be in the future.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set minimum date to today
        self.fields['departure_date'].widget.attrs['min'] = timezone.now().date().isoformat()
        
        # Add Bootstrap classes to all fields
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class RideRequestForm(forms.ModelForm):
    class Meta:
        model = RideRequest
        fields = ['pickup_location', 'dropoff_location', 'number_of_seats', 'special_requests'] 
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pickup_location'].widget.attrs.update({
            'placeholder': 'Enter your pickup location'
        })
        self.fields['dropoff_location'].widget.attrs.update({
            'placeholder': 'Enter your dropoff location'
        })                                               
        
class RideSearchForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
    def clean_date(self):
        date_value = self.cleaned_date.get('date')
        if date_value and date_value < date.today():
            raise forms.ValidationError("Date must be in the future.")
        return date_value
            