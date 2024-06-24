from django import forms

class URLForm(forms.Form):
    urls = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter URLs separated by spaces'}),
        label='Website URLs',
        help_text='Enter the URLs of the websites you want to scrape.'
    )

class HunterEmailForm(forms.Form):
    domain = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter domain (e.g., example.com)'}),
        label='Domain',
        help_text='Enter the domain to search for emails using Hunter.io.'
    )

class SearchForm(forms.Form):
    department = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter department (e.g., IOT)'}),
        label='Department',
        help_text='Enter the department to search companies by.'
    )
    location = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter location (e.g., New York)'}),
        label='Location',
        help_text='Enter the location to search companies by.'
    )
