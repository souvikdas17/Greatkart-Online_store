from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.contrib import messages
from django.db.models import Q
from store.models import Product, ReviewRating, Variation
from carts.models import Cart, CartItem
from orders.models import OrderProduct
from carts.views import _cart_id
from .forms import Reviewform
from category.models import Category
# Create your views here.
def store(request, category_slug=None):
    categories=None
    products=None
    
    if category_slug!=None:
        categories=get_object_or_404(Category, slug=category_slug)
        products=Product.objects.filter(category=categories, is_available=True)
        paginator=Paginator(products, 6)
        page=request.GET.get("page")
        paged_products=paginator.get_page(page)
        product_count=products.count()
    else:
        products=Product.objects.filter(is_available=True)
        paginator=Paginator(products, 6)
        page=request.GET.get("page")
        paged_products=paginator.get_page(page)
        product_count=products.count()
    
    context={
        'products':paged_products,
        'product_count':product_count,
    }
    return render(request, 'store/store.html', context) 

def product_detail(request, category_slug, product_slug):
    try:
        single_product= Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e
    if request.user.is_authenticated:
        try:
            orderproduct= OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except orderproduct.DoesNotExist:
            orderproduct=None
    else:
        orderproduct=None
    reviews= ReviewRating.objects.filter(product_id=single_product.id, status=True)

    context={
        'single_product':single_product,
        'in_cart':in_cart,
        'orderproduct':orderproduct,
        'reviews': reviews,
    }
    return render(request, 'store/product-detail.html', context)

def search(request):
    if "keyword" in request.GET:
        keyword=request.GET['keyword']
        if keyword:
            products=Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword ))
            product_count=products.count()
    context={
        'product_count':product_count,
        'products':products,
    }   
    return render(request, 'store/store.html',context)

def submit_review(request, product_id):
    url=request.META.get('HTTP_REFERER')
    if request.method=='POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = Reviewform(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank You! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form=Reviewform(request.POST)
            if form.is_valid:
                data=ReviewRating()
                data.subject=form.cleaned_data['subject']
                data.rating=form.cleaned_data['rating']
                data.review=form.cleaned_data['review']
                data.ip=request.META.get('REMOTE_ADDR')
                data.product_id=product_id
                data.user_id=request.user.id
                data.save()
                messages.success(request, 'Thank You! Your review has been submitted.')
                return redirect(url)

def product_list(request):
    selected_sizes = request.GET.getlist('size')

    sizes_list = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

    size_variations = Variation.objects.sizes().values_list('variation_value', flat=True).distinct()
    print("Size variations:", list(size_variations))  # This should now print ['SM', ...]

    # Filter products if sizes selected
    if selected_sizes:
        products = Product.objects.filter(
            variation__variation_value__in=selected_sizes,
            variation__variation_category='size',
            variation__is_active=True
        ).distinct()
    else:
        products = Product.objects.all()

    context={
        'products': products,
        'size_variations': size_variations,
        'selected_sizes': selected_sizes,
        'sizes_list': sizes_list,
    }

    return render(request, 'store/store.html', context)

def filter_price(request):
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    price_range=[0, 50, 100, 150, 200, 500, 1000]
    # Apply filtering logic:
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    context= {
    'products': products,
    'min_price': min_price,
    'max_price': max_price,
    'price_range':price_range,
    }
    return render(request, 'store/store.html', context )