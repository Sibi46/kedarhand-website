from django import forms
from django.utils.text import slugify
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods, require_POST
from .models import Category, Product, Order, NewsletterSubscriber
from .views import rate_limit, APIError

class CategoryImageForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['image']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image']
    def clean(self):
        data = super().clean()
        slug = slugify(data.get('name', ''))[:50]
        if not slug:
            self.add_error('name', 'Enter a name containing letters or numbers.')
        elif Category.objects.filter(slug=slug).exists():
            self.add_error('name', 'A category with this name already exists.')
        self.instance.slug = slug
        return data


def authorized(request):
    return request.user.is_authenticated and request.user.is_active and request.user.is_superuser

@require_http_methods(['GET', 'POST'])
def sign_in(request):
    if authorized(request):
        return redirect('superadmin-dashboard')
    error = ''
    if request.method == 'POST':
        try:
            rate_limit(request, 'superadmin-login', 15)
            user = authenticate(request, username=request.POST.get('username', '').strip(), password=request.POST.get('password', ''))
            if user is not None and user.is_active and user.is_superuser:
                login(request, user)
                return redirect('superadmin-dashboard')
            error = 'Username or password is incorrect, or this account does not have Super Admin access.'
        except APIError as exc:
            error = exc.message
    return render(request, 'store/superadmin.html', {'login_page': True, 'error': error})

@require_http_methods(['GET', 'POST'])
def dashboard(request):
    if not authorized(request):
        return redirect('superadmin-login')
    create_form = CategoryForm()
    if request.method == 'POST' and request.POST.get('action') == 'create-category':
        create_form = CategoryForm(request.POST, request.FILES)
        if create_form.is_valid():
            category = create_form.save()
            messages.success(request, f'{category.name} created. Add gallery images below.')
            return redirect('admin:store_category_change', category.pk)
    invalid_form = None
    invalid_id = None
    if request.method == 'POST' and request.POST.get('action') != 'create-category':
        category = Category.objects.filter(slug=request.POST.get('category')).first()
        if category is None:
            messages.error(request, 'Category not found.')
            return redirect('superadmin-dashboard')
        form = CategoryImageForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'{category.name} image updated.')
            return redirect('superadmin-dashboard')
        invalid_form, invalid_id = form, category.pk
    categories = [{'category': c, 'form': invalid_form if c.pk == invalid_id else CategoryImageForm(instance=c)} for c in Category.objects.all()]
    return render(request, 'store/superadmin.html', {'categories': categories, 'create_form': create_form,
        'product_count': Product.objects.count(), 'order_count': Order.objects.count(),
        'subscriber_count': NewsletterSubscriber.objects.count()})

@require_POST
def sign_out(request):
    logout(request)
    return redirect('superadmin-login')
