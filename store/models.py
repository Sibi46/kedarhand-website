import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

def validate_image_size(value):
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('Choose an image smaller than 5 MB.')

class Category(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='categories/', blank=True,
        validators=[validate_image_size, FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
        help_text='Upload JPG, PNG or WebP, up to 5 MB. Landscape images work best.')
    class Meta:
        verbose_name_plural = 'categories'
    def __str__(self):
        return self.name

class CategoryImage(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='categories/gallery/', validators=[validate_image_size, FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])])
    caption = models.CharField(max_length=160, blank=True)
    class Meta:
        ordering = ['id']
    def __str__(self):
        return self.caption or f'{self.category.name} image'

class Product(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=50)
    description = models.TextField()
    options_note = models.CharField(max_length=200, default='Pack sizes to be confirmed')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    subcategory = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, validators=[validate_image_size, FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])])
    class Meta:
        ordering = ['id']
    def __str__(self):
        return self.name

class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    def __str__(self):
        return f'{self.product}: {self.name}'

class SavedSelection(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cart = models.JSONField(default=dict)
    wishlist = models.JSONField(default=list)

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    line1 = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postcode = models.CharField(max_length=10)
    phone = models.CharField(max_length=20)

class Coupon(models.Model):
    code = models.CharField(max_length=40, unique=True)
    percent = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return self.code

class Order(models.Model):
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=30, default='enquiry', choices=[('enquiry', 'Availability enquiry'),
        ('pending', 'Pending confirmation'), ('confirmed', 'Confirmed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')])
    customer_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.JSONField(default=dict)
    note = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    coupon_code = models.CharField(max_length=40, blank=True)
    tracking = models.CharField(max_length=200, blank=True, help_text='Carrier and tracking reference')
    checkout_key = models.UUIDField(default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['user', 'checkout_key'], name='unique_customer_checkout')]
    def __str__(self):
        return str(self.reference)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=160)
    variant_name = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(max_length=2000)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'product'], name='one_review_per_customer_product')]

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class StoreConfiguration(models.Model):
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    free_shipping_above = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    shipping_note = models.CharField(max_length=300, default='Delivery availability and timelines will be confirmed by our team.')
    whatsapp = models.CharField(max_length=15, blank=True, help_text='International number with country code, digits only.')
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    def clean(self):
        super().clean()
        if self.whatsapp and (not self.whatsapp.isascii() or not self.whatsapp.isdigit() or not 8 <= len(self.whatsapp) <= 15):
            raise ValidationError({'whatsapp': 'Enter 8–15 digits including country code.'})
        for field in ['instagram', 'facebook']:
            if getattr(self, field) and not getattr(self, field).startswith('https://'):
                raise ValidationError({field: 'Use an HTTPS URL.'})
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
    def __str__(self):
        return 'Shipping and contact settings'

class ContactEnquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField(max_length=3000)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'contact enquiries'
    def __str__(self):
        return self.name
