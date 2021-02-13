
from django import forms 
  
# creating a form  
class IPForm(forms.Form): 
    ip_address = forms.GenericIPAddressField(protocol='IPv4',)