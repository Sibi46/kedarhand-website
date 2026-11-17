from django.http import HttpResponse, HttpResponseRedirect
from django.test import RequestFactory, SimpleTestCase, override_settings

from kedarmart.prefix import StorePrefixMiddleware
from .views import storefront


@override_settings(FORCE_SCRIPT_NAME='/kedarhand')
class StorePrefixTests(SimpleTestCase):
    def test_storefront_assets_and_api_base_are_mounted(self):
        request = RequestFactory().get('/')
        response = StorePrefixMiddleware(storefront)(request)
        html = response.content.decode()
        self.assertIn('window.KEDARMART_BASE_PATH="/kedarhand"', html)
        self.assertIn('src="/kedarhand/static/backend.js"', html)
        self.assertIn('href="/kedarhand/shop/"', html)
        self.assertNotIn('src="/static/', html)

    def test_existing_prefixed_and_external_links_are_unchanged(self):
        body = '<a href="/kedarhand/admin/">Admin</a><a href="https://example.com/">External</a><form action="/api/contact/">'
        response = StorePrefixMiddleware(lambda request: HttpResponse(body))(RequestFactory().get('/'))
        self.assertIn('href="/kedarhand/admin/"', response.content.decode())
        self.assertIn('href="https://example.com/"', response.content.decode())
        self.assertIn('action="/kedarhand/api/contact/"', response.content.decode())
        self.assertNotIn('/kedarhand/kedarhand/', response.content.decode())

    def test_redirects_stay_in_project(self):
        response = StorePrefixMiddleware(lambda request: HttpResponseRedirect('/super-admin/'))(RequestFactory().get('/'))
        self.assertEqual(response['Location'], '/kedarhand/super-admin/')

    @override_settings(FORCE_SCRIPT_NAME=None)
    def test_default_root_deployment_is_unchanged(self):
        response = StorePrefixMiddleware(lambda request: HttpResponse('<a href="/shop/">Shop</a>'))(RequestFactory().get('/'))
        self.assertEqual(response.content.decode(), '<a href="/shop/">Shop</a>')
