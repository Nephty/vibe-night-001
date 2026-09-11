from django.urls import path

from . import views

app_name = "vibenight"

urlpatterns = [
    path("", views.index, name="index"),
    path("sudoku/", views.sudoku, name="sudoku"),
]
