from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'core/index.html')


def handler404(request, exception):
    return render(request, 'core/404.html', status=404)


def handler500(request):
    return render(request, 'core/500.html', status=500)
