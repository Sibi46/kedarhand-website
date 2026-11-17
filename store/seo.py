from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.html import escape, format_html
from .models import Product, Category
from .views import storefront


def catalog_page(request, category=None, slug=None):
    product = get_object_or_404(Product, slug=slug, active=True) if slug else None
    labels = dict(Category.objects.values_list('slug', 'name'))
    if category and category not in labels:
        from django.http import Http404
        raise Http404
    title = product.name if product else labels.get(category, 'All products')
    description = product.description if product else f'Shop {title.lower()} from Kedarmart.'
    route = 'product/' + product.slug if product else category or 'shop'
    content = format_html('<section class="page"><h1>{}</h1><p>{}</p>', title, description)
    if product:
        if product.image:
            content += format_html('<img src="{}" alt="{}" width="400">', product.image.url, product.name)
        content += format_html('<p>{}</p>', f'INR {product.price}' if product.price is not None else 'Contact us for pricing')
    else:
        products = Product.objects.filter(active=True)
        if category:
            products = products.filter(category=category)
        for item in products:
            content += format_html('<p><a href="/products/{}/">{}</a> — {}</p>', item.slug, item.name, item.description)
    content += '</section>'
    response = storefront(request)
    html = response.content.decode()
    html = html.replace('<main id="app"></main>', '<main id="app">' + content + '</main>')
    start, end = html.index('<title>'), html.index('</title>') + 8
    html = html[:start] + f'<title>{escape(title)} | Kedarmart</title>' + html[end:]
    import re
    html = re.sub(r'<meta name="description"[^>]*>', str(format_html('<meta name="description" content="{}">', description[:300])), html)
    html = html.replace('</head>', str(format_html('<link rel="canonical" href="{}"></head>', request.build_absolute_uri(request.path))))
    # Literal routes consist only of validated slugs. Leave hash navigation intact.
    import json
    html = html.replace('<script src="/static/app.js', '<script>if(!location.hash)history.replaceState(null,"",'+json.dumps('#'+route)+');</script><script src="/static/app.js')
    response.content = html
    return response


def sitemap(request):
    paths = ['/', '/shop/'] + ['/categories/' + c + '/' for c in Category.objects.values_list('slug', flat=True)]
    paths += ['/products/' + slug + '/' for slug in Product.objects.filter(active=True).values_list('slug', flat=True)]
    body = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    body += ''.join('<url><loc>' + escape(request.build_absolute_uri(p)) + '</loc></url>' for p in paths)
    return HttpResponse(body + '</urlset>', content_type='application/xml')


def robots(request):
    return HttpResponse('User-agent: *\nDisallow: /admin/\nDisallow: /super-admin/\nDisallow: /api/\nSitemap: ' + request.build_absolute_uri('/sitemap.xml') + '\n', content_type='text/plain')
