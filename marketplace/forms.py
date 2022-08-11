from tkinter import Widget
from django import forms
from .models import Product

class ProductModelForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class':'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 mb-3 leading-tight focus:outline-none focus:bg-white focus:border-gray-500'}),required=True)
    description = forms.CharField(widget=forms.TextInput(attrs={'class':' no-resize appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 mb-3 leading-tight focus:outline-none focus:bg-white focus:border-gray-500 h-38 resize-none'}),required=True)
    slug = forms.CharField(widget=forms.TextInput(attrs={'class':'w-full max-w-lg rounded-lg border border-slate-200 px-2 py-1 hover:border-blue-500 focus:outline-none focus:ring focus:ring-blue-500/40 active:ring active:ring-blue-500/40'}),required=True)
    price = forms.CharField(widget=forms.TextInput(attrs={'class':'w-full max-w-[150px] rounded-lg border border-slate-200 px-2 py-1 hover:border-blue-500 focus:outline-none focus:ring focus:ring-blue-500/40 active:ring active:ring-blue-500/40'}),required=True)
    thumbnail = forms.ImageField(widget= forms.FileInput(attrs={'class':'hidden', 'id':'dropzone-file'}), required=True)
    content_url = forms.CharField(widget=forms.TextInput(attrs={'class':'w-full max-w-lg rounded-lg border border-slate-200 px-2 py-1 hover:border-blue-500 focus:outline-none focus:ring focus:ring-blue-500/40 active:ring active:ring-blue-500/40'}),required=True)
    content_file = forms.CharField(widget=forms.FileInput(attrs={'class':'w-full max-w-lg rounded-lg border border-slate-200 px-2 py-1 hover:border-blue-500 focus:outline-none focus:ring focus:ring-blue-500/40 active:ring active:ring-blue-500/40'}),required=True)


    class Meta:
        model = Product
        fields = (
            'name',
            'description',
            'thumbnail',
            'slug',
            'content_url',
            'content_file',
            'price',
            'active'
        )

    def clean_price(self,*args, **kwargs):
        price = self.cleaned_data.get('price')
        price = int(price)

        if price >99:
            return price
        else:
            raise forms.ValidationError("Price must be equal or higher than $100")


