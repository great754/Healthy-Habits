from django.contrib import admin
from habits.models import Log, Habit, User, Journal
# Register your models here.
admin.site.register(Log)
admin.site.register(Habit)
admin.site.register(User)
admin.site.register(Journal)