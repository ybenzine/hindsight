from django.http import HttpResponse


def home(request):
    """Placeholder landing page until the projects app provides a real one."""
    return HttpResponse("Hindsight is running.")
