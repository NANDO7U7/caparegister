from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_not_required


class SigecapLoginView(LoginView):
    template_name = 'registration/login.html'


class SigecapLogoutView(LogoutView):
    def get_success_url(self):
        # Logout always returns to the login, regardless of supplied next.
        return '/login/'


@login_not_required
def admin_login(request):
    from django.contrib.auth.views import redirect_to_login
    if request.user.is_authenticated:
        return redirect('admin:index') if request.user.is_staff else redirect('core:dashboard')
    return redirect_to_login(request.GET.get('next') or '/admin/')
