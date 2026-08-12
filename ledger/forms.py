from django import forms
from .models import Sale, Expense, ShopSettings


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['product_name', 'purchase_price', 'selling_price', 'quantity', 'date', 'notes']
        widgets = {
            'product_name': forms.TextInput(attrs={
                'list': 'product-list',
                'class': 'input',
                'placeholder': 'Type to search or add new product…',
                'autocomplete': 'off',
            }),
            'purchase_price': forms.NumberInput(attrs={'class': 'input'}),
            'selling_price': forms.NumberInput(attrs={'class': 'input'}),
            'quantity': forms.NumberInput(attrs={'class': 'input'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'input'}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'category', 'amount', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'input')


class SettingsForm(forms.ModelForm):
    class Meta:
        model = ShopSettings
        fields = ['shop_name', 'currency', 'opening_balance']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'input')