from django.db import models
from django.utils.timezone import now
import pytz


def get_india_time():
    return now().astimezone(pytz.timezone('Asia/Kolkata'))

condition_choices = [
    ('Working', 'Working'),
    ('Not Working', 'Not Working'),
]

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20)
    course = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=get_india_time)  

    def __str__(self):
        return f"{self.name} ({self.roll_number})"

class Component(models.Model):
    name = models.CharField(max_length=100)
    quantity_available = models.IntegerField()

    def __str__(self):
        return self.name

class IssueRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    quantity_issued = models.IntegerField()
    date_issued = models.DateTimeField(auto_now_add=True)
    returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student} issued {self.component} x{self.quantity_issued}"

class ReturnRecord(models.Model):
    issue = models.ForeignKey(IssueRecord, on_delete=models.CASCADE)
    condition = models.CharField(max_length=20, choices=condition_choices)
    date_returned = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Return of {self.issue} as {self.condition}"
