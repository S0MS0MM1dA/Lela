from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def home(request):
    return render(request, 'blog/home.html')
def post_detail(request):
    return render(request, 'blog/post_detail.html')
def dashboard(request):
    return render(request, 'dashboard/dashboard.html')
def inkwell_auth(request):
    return render(request, 'accounts/inkwell-auth.html')