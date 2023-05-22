from django.views.generic.base import TemplateView


class about_author(TemplateView):
    template_name = 'about/author.html'


class about_tech(TemplateView):
    template_name = 'about/tech.html'
