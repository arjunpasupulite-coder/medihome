from django import forms
from .models import SystemSettings, Coupon, Offer, ContactMessage

class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = ['gst_percentage', 'platform_fee', 'home_collection_charge', 'support_email', 'support_phone']
        widgets = {
            'gst_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'platform_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'home_collection_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'support_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'support_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_percent', 'discount_max_amount', 'min_order_amount', 'valid_until', 'is_active', 'usage_limit']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_max_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_order_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
