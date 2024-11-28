from django import forms
import datetime

class AcademicYearForm(forms.Form):
    
    def generate_years():
        start_year = 2024 
        num_years = 5   
        years = [(str(year), str(year)) for year in range(start_year, start_year + num_years)]
        return years

    academic_year = forms.ChoiceField(
        choices=generate_years(),
        label='Select Academic Year',
        widget=forms.Select(attrs={'class': 'form-control'}) 
    )
