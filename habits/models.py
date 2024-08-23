from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date, datetime
from django.utils import timezone

# Create your models here.

class User(AbstractUser):
    pass

class Habit(models.Model):
    choices = [
        ('weekly', 'Weekly'),
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ]
    times = [
    (str(i), str(i)) for i in range(1, 11)
] + [
    ('custom', 'Custom')
]
    
    current_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="current_user")
    name = models.CharField(max_length=30, default="custom")
    description = models.TextField()
    date_started = models.DateField(default=timezone.now)
    time_started = models.TimeField(default=timezone.now)
    how_often = models.CharField(max_length=30, choices = choices, default="daily")
    time_often = models.CharField(max_length=10, choices=times, default="1")

    def __str__(self):
        return f"{self.current_user} started a new habit {self.name} on {self.date_started}"
    
def calculate(id):
    log = Log.objects.get(pk=id)
    started = str(log.started)
    ended = str(log.ended)
    hour1, minute1, second1 = started.split(":")
    hour2, minute2, second2 = ended.split(":")
    minutes1 = (int(hour1)*60)+int(minute1)
    minutes2 = (int(hour2)*60)+int(minute2)
    return minutes2 - minutes1

class Log(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    when = models.DateField(default=timezone.now)
    started = models.TimeField()
    ended = models.TimeField(default=timezone.now)

    def __str__(self):
        time = calculate(self.id)
        return f"{self.user} {self.habit.name} on {self.when} for {time} minutes"
    

class Journal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    log = models.OneToOneField(Log, on_delete=models.CASCADE)
    title = models.CharField(max_length=30)
    entry = models.TextField(max_length=720)
