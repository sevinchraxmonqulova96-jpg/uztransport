from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'transport/index.html'


class DriverView(TemplateView):
    template_name = 'transport/driver.html'


class AdminDashView(TemplateView):
    template_name = 'transport/dashboard.html'
