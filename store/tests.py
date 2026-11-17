import json
import uuid
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from .models import Product, Variant, Address, Order, Coupon, Review, NewsletterSubscriber

class StoreTests(TestCase):
    def test_contact_is_persisted_validated_and_rate_limited(self):
        from .models import ContactEnquiry
        self.assertEqual(self.post('contact', {'name': 'A', 'email': 'invalid', 'message': 'Hello'}).status_code, 400)
        payload = {'name': 'Customer', 'email': 'customer@example.com', 'message': 'Delivery question'}
        self.assertEqual(self.post('contact', payload).status_code, 201)
        self.assertEqual(ContactEnquiry.objects.get().message, 'Delivery question')
        for _ in range(3):
            self.post('contact', payload)
        self.assertEqual(self.post('contact', payload).status_code, 429)

    def test_shipping_is_calculated_and_snapshotted(self):
        from .models import StoreConfiguration
        config = StoreConfiguration.objects.create(shipping_fee=50, free_shipping_above=200)
        self.product.price = Decimal('100')
        self.product.stock = 10
        self.product.save()
        self.client.force_login(self.user)
        self.add()
        response = self.checkout()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['total'], '150.00')
        self.assertEqual(Order.objects.get().shipping, Decimal('50'))
        self.add(2)
        response = self.checkout()
        self.assertEqual(response.json()['total'], '200.00')
        config.shipping_fee = 99
        config.save()
        self.assertEqual(Order.objects.order_by('id').first().shipping, Decimal('50'))

    def test_crawlable_catalog_and_subcategory_filter(self):
        from .models import Category
        Category.objects.get_or_create(slug='coffee', defaults={'name': 'Coffee'})
        self.product.subcategory = 'Ground coffee'
        self.product.save()
        self.assertEqual(len(self.client.get('/api/products/?subcategory=Ground%20coffee').json()['products']), 1)
        self.assertContains(self.client.get('/products/coffee/'), '<title>Coffee | Kedarmart</title>', html=True)
        self.assertContains(self.client.get('/categories/coffee/'), '/products/coffee/')
        self.assertContains(self.client.get('/sitemap.xml'), '/products/coffee/')
        self.product.active = False
        self.product.save()
        self.assertEqual(self.client.get('/products/coffee/').status_code, 404)
        self.assertNotContains(self.client.get('/sitemap.xml'), '/products/coffee/')

    def setUp(self):
        cache.clear()
        self.product = Product.objects.create(slug='coffee', name='Coffee', category='coffee', description='Coffee')
        self.user = get_user_model().objects.create_user('test@example.com','test@example.com','Str0ng-test-pass!',first_name='Test')
        self.other = get_user_model().objects.create_user('other@example.com','other@example.com','Str0ng-test-pass!')
        self.address = Address.objects.create(user=self.user,name='Test',line1='Street',city='Dehradun',state='Uttarakhand',postcode='248003',phone='1234567890')
    def post(self, path, data, client=None):
        return (client or self.client).post('/api/'+path+'/',json.dumps(data),content_type='application/json')
    def add(self, qty=1, variant=None):
        return self.post('cart',{'product':'coffee','quantity':qty,'variant':variant})
    def checkout(self, key=None, **extra):
        return self.post('checkout',{'address_id':self.address.id,'checkout_key':str(key or uuid.uuid4()),**extra})
    def test_catalog_filters_and_hidden_products(self):
        Product.objects.create(slug='hidden',name='Hidden',category='tea',description='',active=False)
        self.assertEqual(len(self.client.get('/api/products/').json()['products']),1)
        self.assertEqual(self.client.get('/api/products/?category=tea').json()['products'],[])
        self.assertEqual(len(self.client.get('/api/products/?q=Coffee').json()['products']),1)
        self.assertEqual(self.client.get('/api/products/hidden/').status_code,404)
    def test_registration_password_hashing_and_guest_merge(self):
        self.add(2)
        self.post('wishlist',{'product':'coffee'})
        response=self.post('register',{'email':'new@example.com','name':'New','password':'New-str0ng-pass!456'})
        self.assertEqual(response.status_code,200)
        user=get_user_model().objects.get(username='new@example.com')
        self.assertTrue(user.check_password('New-str0ng-pass!456'))
        self.assertNotEqual(user.password,'New-str0ng-pass!456')
        self.assertEqual(response.json()['cart']['coffee']['quantity'],2)
        self.post('logout',{})
        result=self.post('login',{'email':'new@example.com','password':'New-str0ng-pass!456'})
        self.assertEqual(result.json()['wishlist'],['coffee'])
    def test_login_and_weak_password_validation(self):
        self.assertEqual(self.post('login',{'email':self.user.email,'password':'wrong'}).status_code,401)
        self.assertEqual(self.post('register',{'email':'new@example.com','name':'New','password':'12345678'}).status_code,400)
        self.assertEqual(self.client.get('/api/register/').status_code,405)
    def test_csrf_is_required_for_mutations(self):
        c=Client(enforce_csrf_checks=True)
        self.assertEqual(self.post('cart',{'product':'coffee','quantity':1},c).status_code,403)
        token=c.get('/api/session/').json()['csrf']
        response=c.post('/api/cart/',json.dumps({'product':'coffee','quantity':1}),content_type='application/json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,200)
    def test_quantity_and_variant_validation(self):
        for qty in [0,100,-1,1.2,True,'3']:
            self.assertEqual(self.add(qty).status_code,400)
        another=Product.objects.create(slug='tea',name='Tea',category='tea',description='Tea')
        variant=Variant.objects.create(product=another,name='250g',price='100.00',stock=10)
        self.assertEqual(self.add(1,variant.id).status_code,404)
    def test_customer_address_and_order_isolation(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get('/api/addresses/').json()['addresses'],[])
        self.assertEqual(self.client.delete(f'/api/addresses/{self.address.id}/',content_type='application/json').status_code,404)
        self.add()
        self.assertEqual(self.checkout().status_code,404)
        o=Order.objects.create(user=self.user,customer_name='Test',email=self.user.email)
        self.assertEqual(self.client.get(f'/api/orders/{o.reference}/').status_code,404)
    def test_unpriced_checkout_saves_enquiry_and_is_idempotent(self):
        self.client.force_login(self.user)
        self.add(3)
        key=uuid.uuid4()
        response=self.checkout(key)
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.json()['status'],'Availability enquiry')
        self.assertIsNone(response.json()['total'])
        self.assertEqual(self.checkout(key).json()['reference'],response.json()['reference'])
        self.assertEqual(Order.objects.count(),1)
        self.assertEqual(Order.objects.first().items.get().quantity,3)
        self.assertEqual(self.client.get('/api/cart/').json()['cart'],{})
        self.assertEqual(self.checkout().status_code,400)
    def test_priced_checkout_reserves_stock_and_recalculates_coupon(self):
        self.client.force_login(self.user)
        self.product.price=Decimal('125.50');self.product.stock=5;self.product.save()
        Coupon.objects.create(code='SAVE',percent=10)
        self.add(2)
        response=self.checkout(coupon='SAVE',total='1.00')
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.json()['total'],'225.90')
        self.assertEqual(response.json()['status'],'Pending confirmation')
        self.product.refresh_from_db();self.assertEqual(self.product.stock,3)
    def test_out_of_stock_checkout_is_atomic(self):
        self.client.force_login(self.user)
        self.product.price=Decimal('10');self.product.stock=1;self.product.save()
        self.add(2)
        self.assertEqual(self.checkout().status_code,400)
        self.assertEqual(Order.objects.count(),0)
        self.assertEqual(self.client.get('/api/cart/').json()['cart']['coffee']['quantity'],2)
    def test_variant_checkout_uses_variant_price_and_stock(self):
        self.client.force_login(self.user)
        v=Variant.objects.create(product=self.product,name='250g',price='150',stock=3)
        self.add();self.assertEqual(self.checkout().status_code,400)
        self.add(2,v.id)
        response=self.checkout();self.assertEqual(response.json()['total'],'300.00')
        v.refresh_from_db();self.assertEqual(v.stock,1)
        self.assertEqual(Order.objects.get().items.get().variant_name,'250g')
    def test_expired_coupon_and_review_moderation(self):
        Coupon.objects.create(code='OLD',percent=10,expires_at=timezone.now()-timedelta(days=1))
        self.assertEqual(self.post('coupon',{'code':'OLD'}).status_code,400)
        self.assertEqual(self.post('reviews',{'product':'coffee','rating':5,'text':'Good'}).status_code,401)
        self.client.force_login(self.user)
        self.assertEqual(self.post('reviews',{'product':'coffee','rating':5,'text':'Good'}).status_code,201)
        self.assertEqual(self.client.get('/api/reviews/coffee/').json()['reviews'],[])
        Review.objects.update(approved=True)
        self.assertEqual(self.client.get('/api/reviews/coffee/').json()['reviews'][0]['text'],'Good')
    def test_newsletter_validation_dedup_and_malformed_json(self):
        self.assertEqual(self.post('newsletter',{'email':'bad'}).status_code,400)
        self.post('newsletter',{'email':'person@example.com'});self.post('newsletter',{'email':'person@example.com'})
        self.assertEqual(NewsletterSubscriber.objects.count(),1)
        response=self.client.post('/api/cart/','[1]',content_type='application/json')
        self.assertEqual(response.status_code,400)
    def test_storefront_connects_backend(self):
        response=self.client.get('/')
        self.assertContains(response,'/static/backend.js')
        self.assertContains(response,'/static/style.css')
        self.assertIn('csrftoken',response.cookies)
        self.assertContains(response, 'href="/super-admin/">Super Admin')
    def test_custom_superadmin_access_and_login(self):
        self.assertRedirects(self.client.get('/super-admin/'), '/super-admin/login/')
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get('/super-admin/'), '/super-admin/login/')
        self.client.logout()
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        response = self.client.post('/super-admin/login/', {'username': self.user.username, 'password': 'Str0ng-test-pass!'})
        self.assertRedirects(response, '/super-admin/')
        self.assertContains(self.client.get('/super-admin/'), 'Super Admin dashboard')
        self.assertEqual(self.client.get('/super-admin/logout/').status_code, 405)
        self.assertRedirects(self.client.post('/super-admin/logout/'), '/super-admin/login/')
    def test_custom_superadmin_rejects_invalid_image(self):
        from .models import Category
        from django.core.files.uploadedfile import SimpleUploadedFile
        Category.objects.create(slug='coffee', name='Coffee')
        self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.post('/super-admin/', {'category': 'coffee', 'image': SimpleUploadedFile('fake.jpg', b'bad', content_type='image/jpeg')})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Category.objects.get().image)
    def test_admin_category_upload_and_catalog_image(self):
        import tempfile
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Category
        buffer = BytesIO()
        Image.new('RGB', (80, 60), 'green').save(buffer, format='PNG')
        from django.conf import settings
        with tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as directory, self.settings(MEDIA_ROOT=directory):
            self.user.is_staff = True
            self.user.is_superuser = True
            self.user.save()
            self.client.force_login(self.user)
            response = self.client.post('/admin/store/category/add/', {
                'name': 'Coffee', 'slug': 'coffee', 'gallery-TOTAL_FORMS': '0', 'gallery-INITIAL_FORMS': '0',
                'image': SimpleUploadedFile('coffee.png', buffer.getvalue(), content_type='image/png'), '_save': 'Save'})
            self.assertEqual(response.status_code, 302)
            category = Category.objects.get(slug='coffee')
            self.assertTrue(category.image.storage.exists(category.image.name))
            data = self.client.get('/api/products/').json()['categories']
            self.assertEqual(data[0]['image'], category.image.url)
            self.assertTrue(category.image.url.startswith('/media/categories/'))
            self.client.logout()
            self.assertEqual(self.client.get('/admin/store/category/').status_code, 302)
    def test_admin_rejects_non_image_upload(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Category
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.post('/admin/store/category/add/', {
            'name': 'Coffee', 'slug': 'coffee', 'gallery-TOTAL_FORMS': '0', 'gallery-INITIAL_FORMS': '0',
            'image': SimpleUploadedFile('fake.jpg', b'not an image', content_type='image/jpeg'), '_save': 'Save'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Category.objects.exists())
    def test_storefront_asset_markup_and_resources(self):
        from html.parser import HTMLParser
        class Assets(HTMLParser):
            urls = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'link' and attrs.get('rel') == 'stylesheet':
                    self.urls.append(attrs['href'])
                if tag == 'script':
                    self.urls.append(attrs['src'])
        parser = Assets()
        parser.feed(self.client.get('/').content.decode())
        self.assertEqual(len(parser.urls), 5)
        for url in parser.urls:
            self.assertTrue(url.startswith('/static/'), url)
            self.assertNotIn('<', url)
            self.assertNotIn('>', url)
        self.assertTrue(any(url.startswith('/static/style.css?') for url in parser.urls))
        self.assertTrue(any(url.startswith('/static/app.js?') for url in parser.urls))


class FlexibleCategoryTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser('category-admin', password='test-admin-secret')
        self.client.force_login(self.admin_user)

    def test_new_category_products_and_gallery(self):
        from .models import Category, CategoryImage
        from .admin import ProductForm
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from PIL import Image
        import io, tempfile
        from django.conf import settings
        response = self.client.post('/super-admin/', {'action': 'create-category', 'name': 'Snacks'})
        category = Category.objects.get(slug='snacks')
        self.assertRedirects(response, f'/admin/store/category/{category.pk}/change/', fetch_redirect_response=False)
        form = ProductForm(data={'name': 'Roasted nuts', 'slug': 'roasted-nuts', 'category': 'snacks', 'description': 'Fresh nuts', 'options_note': '100g', 'stock': 10, 'active': True})
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        with tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as directory, override_settings(MEDIA_ROOT=directory):
            buffer = io.BytesIO()
            Image.new('RGB', (2, 2)).save(buffer, format='PNG')
            for i in range(7):
                CategoryImage.objects.create(category=category, caption=f'Photo {i}', image=SimpleUploadedFile(f'image{i}.png', buffer.getvalue(), content_type='image/png'))
            payload = self.client.get('/api/products/').json()
            data = next(c for c in payload['categories'] if c['slug'] == 'snacks')
            self.assertEqual(len(data['gallery']), 7)
            self.assertEqual(self.client.get('/categories/snacks/').status_code, 200)
            self.assertContains(self.client.get('/sitemap.xml'), '/categories/snacks/')

    def test_category_creation_requires_superuser(self):
        self.client.logout()
        self.client.post('/super-admin/', {'action': 'create-category', 'name': 'Unauthorized'})
        from .models import Category
        self.assertFalse(Category.objects.filter(slug='unauthorized').exists())
