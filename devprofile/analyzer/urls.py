from django.urls import path
from analyzer.views.analyzer_view import analyzer_home
from analyzer.views.readme_view import readme_generator

urlpatterns = [

    path("analyzer/", analyzer_home, name="home"),

    path("readme/", readme_generator, name="readme_generator"),

]