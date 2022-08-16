from distutils.sysconfig import customize_compiler
from itertools import product
from json import JSONEncoder
from msilib.schema import Signature
from multiprocessing import context
from pydoc import describe
from signal import Signals
from tracemalloc import get_object_traceback
from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from marketplace.models import Product, PurchasedProduct
from django.views import View
from django.core.paginator import Paginator
from marketplace.forms import ProductModelForm, EditProductModelForm
from django.views.generic.edit import UpdateView
from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import stripe
from django.conf import settings
from django.http.response import JsonResponse, HttpResponse
from stripe.error import SignatureVerificationError
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from accounts.models import UserLibrary
User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY


class HomeView(View):
    def get(self,request,*args, **kwargs):
        products = Product.objects.filter(active=True)

        form = ProductModelForm()

        products_data= None

        if products:
            paginator = Paginator(products, 9)
            page_number = request.GET.get('page')
            products_data = paginator.get_page(page_number)

        context = {
            'products':products_data,
            'form':form,
        }

        return render(request, 'pages/index.html', context)
    
    def post(self,request,*args, **kwargs):
        products = Product.objects.filter(active=True)

        form = ProductModelForm()

        if request.method == "POST":
            form = ProductModelForm(request.POST, request.FILES)

            if form.is_valid():
                form.user = request.user
                name = form.cleaned_data.get('name')
                description = form.cleaned_data.get('description')
                thumbnail = form.cleaned_data.get('thumbnail')
                slug = form.cleaned_data.get('slug')
                content_url = form.cleaned_data.get('content_url')
                content_file = form.cleaned_data.get('content_file')
                price = form.cleaned_data.get('price')
                active = form.cleaned_data.get('active')

                p, created = Product.objects.get_or_create(user = form.user, name= name, description= description,
                thumbnail= thumbnail, slug= slug, content_url= content_url, content_file= content_file, price=price, active= active)
                p.save()
                return redirect('home')

        products_data= None

        if products:
            paginator = Paginator(products, 9)
            page_number = request.GET.get('page')
            products_data = paginator.get_page(page_number)

        context = {
            'products':products_data,
        }
        return render(request, 'pages/index.html', context)

class UserProductListView(View):
    def get(self,request,*args, **kwargs):

        products = Product.objects.filter(user = self.request.user)
        context= {
            'products':products
        }

        return render(request, 'pages/products/user_productlist.html', context)

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    template_name= "pages/products/edit_product.html"
    form_class = EditProductModelForm
    
    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse('product-list')


class ProductDetailView(View):
    def get(self,request, slug, *args, **kwargs):
        product = get_object_or_404(Product, slug=slug)
        has_acces=None
        if self.request.user.is_authenticated:
            if product in self.request.user.library.products.all():
                has_acces = True

        context ={
            'product': product,
            'has_acces': has_acces
        }
        context.update({
            'STRIPE_PUBLIC_KEY':settings.STRIPE_PUBLIC_KEY
        })

        return render(request,'pages/products/detail.html' , context,)



class CreateCheckoutSessionView(View):
    def post(self,request, *args, **kwargs):
        product = Product.objects.get(slug=self.kwargs['slug'])

        domain = "https://mkgames.com"
        if settings.DEBUG:
            domain = 'http://127.0.0.1:8000'

        customer = None
        customer_email = None   
        if request.user.is_authenticated:
            if request.user.stripe_customer_id: 
                customer = request.user.stripe_customer_id
            else:
                customer_email = request.user.email

        session = stripe.checkout.Session.create(
            customer = customer,
            customer_email = customer_email,
            payment_method_types=['card'],
            line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                'name': product.name,
                },
                'unit_amount': product.price,
            },
            'quantity': 1,
            }],
            mode='payment',
            success_url=domain + reverse('success'),
            cancel_url=domain +reverse('home'),
            customer_creation= "always",
            metadata = {
                "product_id": product.id
            }
        )

        return JsonResponse({
            "id":session.id
        })

class SuccessView(TemplateView):
    template_name='pages/products/success.html'

@csrf_exempt
def stripe_webhook(request, *args, **kwargs):

        CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
        payload = request.body
        sig_header = request.META["HTTP_STRIPE_SIGNATURE"]

        try:
            event= stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            print(e)
            return HttpResponse(status=400)

        except SignatureVerificationError as e:
            print(e)
            return HttpResponse(status=400)

        # Escuchar pago exitoso  
        if event["type"] == CHECKOUT_SESSION_COMPLETED:
            print(event)

        
        # Quien pago y que cosa
        product_id = event["data"]["object"]["metadata"]["product_id"]
        product= Product.objects.get(id = product_id)
        stripe_customer_id = event["data"]["object"]["customer"]
        
        # Dar acceso al producto
        
        try:
            # Revisar si el user tiene un customer_id
            user = User.objects.get(stripe_customer_id=stripe_customer_id)
            user.library.products.add(product)
            user.library.save
        except User.DoesNotExist:
            # El ususario no tiene customed_id pero está registrado
            stripe_customer_email = event["data"]["object"]["customer_details"]["email"]
            try:
                user = User.objects.get(email = stripe_customer_email)
                user.stripe_customer_id = stripe_customer_id
                user.library.products.add(product)
                user.library.save
            except User.DoesNotExist:
                PurchasedProduct.objects.create(
                    email = stripe_customer_email,
                    product= product
                )
                send_mail(
                    subject="Create una cuenta para acceder a tu contenido",
                    message="Por favor, create una cuenta para recibir tus productos",
                    recipient_list=[stripe_customer_email],
                    from_email="Marketplace <mkgames@gmail.com>"
                )
                pass

        return HttpResponse()



class UserLibraryView(LoginRequiredMixin,View):
        def get(self,request, username,*args, **kwargs):
            user = get_object_or_404(User, username = username)
            userlibrary = UserLibrary.objects.get(user=user)
            context={
                'userlibrary':userlibrary,
            }

            return render(request, 'pages/products/library.html', context)