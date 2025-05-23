from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse
from .forms import RegistrationForm
from carts.views import _cart_id
from carts.models import Cart, CartItem
from .models import Account
import requests

#Verification import 
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

# Create your views here.
def register(request):
    if request.method=="POST":
        form=RegistrationForm(request.POST)
        if form.is_valid():
            first_name=form.cleaned_data['first_name']
            last_name=form.cleaned_data['last_name']
            phone_number=form.cleaned_data['phone_number']
            email=form.cleaned_data['email']
            username=email.split("@")[0]
            password=form.cleaned_data['password']
            user=Account.objects.create_user(first_name=first_name, last_name=last_name, email=email,  username=username, password=password)
            user.phone_number= phone_number
            user.save()
            #User Activation
            current_site=get_current_site(request)
            mail_subject="Please activate your Account!"
            message=render_to_string('accounts/verification_email.html', {
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email=email
            send_email=EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            # messages.success(request, 'Registration Successful')
            return redirect('/accounts/login/?command=verification&email='+email )
    else:
        form=RegistrationForm()
    context={
        'form':form,
    }
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method=='POST':
        email=request.POST['email']
        password=request.POST['password']
        
        user=auth.authenticate(request, email=email, password=password)
        if user is not None:
            try:
                cart= Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists= CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item=CartItem.objects.filter(cart=cart, user=None)
                    product_variation=[]
                    for item in cart_item:
                        variation= item.variations.all()
                        product_variation.append(list(variation))
                    cart_item= CartItem.objects.filter(user=user)
                    existing_variations_list=[]
                    id=[]
                    for item in cart_item:
                        existing_variations=item.variations.all()
                        existing_variations_list.append(list(existing_variations))
                        id.append(item.id)
                        
                    for pr in product_variation:
                        if pr in existing_variations_list:
                            index=existing_variations_list.index(pr)
                            item_id=id[index]
                            item=CartItem.objects.get(id=item_id)
                            item.quantity+=1
                            item.user=user
                            item.save()
                        else:
                            cart_item=CartItem.objects.filter(cart=cart, user=None)
                            for item in cart_item:
                                item.user=user
                                item.save()
            except:
                pass
            auth.login(request,user)
            if not request.session.get('seen_login_msg'):
                messages.success(request, "You are now logged In.")
                request.session['seen_login_msg'] = True
            url= request.META.get('HTTP_REFERER')
            try:
                query= requests.utils.urlparse(url).query
                params= dict(x.split('=')for x in query.split('&'))
                if 'next' in params:
                    nextPage= params['next']
                    return redirect(nextPage)
                
            except:
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid login Credentials")
            return redirect('login')
    return render(request, 'accounts/login.html')

@login_required(login_url='login')
def logout_view(request):
    auth_logout(request)
    request.session.pop('seen_login_msg', None)
    list(messages.get_messages(request))
    messages.success(request, "You are logged Out!")
    return redirect('login')


def activate(request, uidb64, token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user=None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active=True
        user.save()
        messages.success(request, "Your Account is activated!")
        return redirect('login')
    else:
        messages.error(request, 'Invalid Activation Link')
        return redirect('register')
        
@login_required(login_url='login')
def dashboard(request ):
    return render(request, 'accounts/dashboard.html')

def forgotPassword(request):
    if request.method=='POST':
        email=request.POST['email']
        if Account.objects.filter(email=email).exists():
            user=Account.objects.get(email__iexact=email)
        # Reset Password Email
            current_site=get_current_site(request)
            mail_subject="Reset your Password!"
            message=render_to_string('accounts/reset_password_email.html', {
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email=email
            send_email=EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'A password reset email has been sent to your registered email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account Does not Exist!')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user=None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid']= uid
        messages.success(request, "Please Reset your Password!")
        return redirect('ResetPassword')
    else:
        messages.error(request, "This link has been expired.")
        return redirect('login')
    
def Resetpassword(request):
    if request.method=='POST':
        password=request.POST['password']
        confirm_password= request.POST['confirm_password']
        if password == confirm_password:
            uid=request.session.get('uid')
            user= Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Password has been changed.")
            return redirect('login')
        else:
            messages.error(request, "Password do not match!")
            return redirect('ResetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')