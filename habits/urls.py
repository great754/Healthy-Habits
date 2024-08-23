from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="create"),
    path("habit/<int:id>", views.habit, name="habit"),
    path("log", views.log, name="log"),
    path("calculate/<int:id>", views.calculate, name="calculate"),
    path("journal/<int:id>", views.journal, name="journal"),
    path("streak/<int:id>", views.streak, name="streak"),
    path("delete/<int:id>", views.delete, name="delete"),
    path("edit/<int:id>", views.edit, name="edit")
]

