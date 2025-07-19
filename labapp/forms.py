from django import forms
from .models import Student, Component, IssueRecord, ReturnRecord

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'roll_number', 'course']

class IssueForm(forms.Form):
    component = forms.ModelChoiceField(queryset=Component.objects.all(), label="Select Component")
    quantity_issued = forms.IntegerField(min_value=1, label="Quantity")

class ReturnForm(forms.Form):
    issue = forms.ModelChoiceField(queryset=IssueRecord.objects.filter(returned=False))
    condition = forms.ChoiceField(choices=[('Working', 'Working'), ('Not Working', 'Not Working')])
