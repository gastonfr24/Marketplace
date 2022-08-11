from itertools import product
from tkinter import Image
from django.db import models
from django.db.models import *
import os
from django.conf import settings
from django.utils import timezone


User = settings.AUTH_USER_MODEL

def marketplace_directory_path(instance, filename):
    banner_pic_name = 'marketplace/prodcuts/{0}/{1}'.format(instance.name, filename)
    full_path = os.path.join(settings.MEDIA_ROOT, banner_pic_name)

    if os.path.exists(full_path):
        os.remove(full_path)
    return banner_pic_name

class Product(Model):
    user = ForeignKey(User, on_delete=CASCADE, related_name='products')
    name = CharField(max_length=100)
    description = TextField()
    thumbnail = ImageField(blank = True, null= True, upload_to= marketplace_directory_path)
    slug = SlugField(unique=True)
    published = DateTimeField(default=timezone.now)

    content_url = URLField(blank=True, null=True)
    content_file = FileField(blank=True, null=True)

    active = BooleanField(default=False)

    price = PositiveIntegerField(default=100)

    class Meta:
        ordering = ('-published',)


    def __str__(self):
        return self.name

    def price_display(self):
        return "{0:.2f}".format(self.price/100)

class PurchasedProduct(Model):
    email = EmailField()
    product = ForeignKey(Product, on_delete=CASCADE)
    date_purchased = DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email