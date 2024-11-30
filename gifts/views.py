from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q
from .forms import CustomUserCreationForm, GiftForm
import math
from gifts.models import User, Gift, Family, Notification

# Create your views here.


def home(request):
    return render(request, "index.html")

@login_required
def account(request):
    # Gifts where the logged-in user is paired
    attached_gifts = Gift.objects.filter(user_paired=request.user)

    # Gifts claimed by the logged-in user
    claimed_gifts = Gift.objects.filter(user_claimed=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        gift_id = request.POST.get('gift_id')

        # Ensure the gift exists
        gift = get_object_or_404(Gift, id=gift_id)

        if action == 'delete':
            # Delete gift logic
            if gift.user_paired == request.user:
                notification = Notification(user_sent_to=gift.user_claimed, message=f"Gift '{gift.name}' has been deleted. You have automatically unclaimed this gift.")
                notification.save()
                gift.delete()
                
            else:
                pass

        elif action == 'unclaim':
            # Unclaim gift logic
            if gift.user_claimed == request.user:
                gift.user_claimed = None
                gift.is_claimed = False
                

                gift.save()
                
            else:
                pass

        return redirect('account')

    return render(request, 'account.html', {
        'attached_gifts': attached_gifts,
        'claimed_gifts': claimed_gifts,
    })

@login_required
def notifications(request):
    # Get all notifications for the logged-in user
    notifications = Notification.objects.filter(user_sent_to=request.user)

    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        notification = get_object_or_404(Notification, id=notification_id, user_sent_to=request.user)
        notification.delete()  # Delete the notification to mark it as read
        return redirect('notifications')

    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def add_gift(request):
    user = request.user
    if request.method == 'POST':
        form = GiftForm(request.POST)
        if form.is_valid():
            gift = form.save(commit=False)
            gift.family = request.user.family  # Assume user's family is accessible via user model
            gift.user_paired = request.user  # Pair the gift with the logged-in user
            gift.is_claimed = False  # Set the default value for is_claimed
            gift.save()
            
            return redirect('home')  # Replace 'gifts' with the name of your gift list view
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = GiftForm()

    return render(request, 'create_gift.html', {'form': form})

@login_required
def gift_list(request):
    user = request.user
    if user.family == None:
        return redirect("family-select")
    gifts = Gift.objects.filter(Q(family=user.family) & ~Q(user_paired=user) )
    users = User.objects.all()

    # Filter by dropdown value
    filter_by = request.GET.get('filter_by')
    if filter_by:
        gifts = gifts.filter(user_paired=filter_by)  # Adjust filter as needed

    # Filter by checkbox value
    include = request.GET.get('include')
    if include != "yes":
        gifts = gifts.filter(is_claimed=False)  # Adjust filter as needed

    if request.method == 'POST':
        action = request.POST.get('action')
        gift_id = request.POST.get('gift_id')
        if action == 'claim':
                gift = get_object_or_404(Gift, id=gift_id)
                if not gift.is_claimed:
                    gift.is_claimed = True
                    gift.user_claimed = request.user
                    gift.save()
                    
                else:
                    pass

        return redirect('home')  # Redirect to the same page after handling the action

    return render(request, 'index.html', {'gifts': gifts, 'users': users})

@login_required
def family_select(request):
    user = request.user
    if user.family == None:
        if request.method == 'POST':
            code = request.POST.get('code')

            # Validate that the code is 6 digits
            if not code or not code.isdigit() or len(code) != 6:
                return render(request, "join_family.html", {'error': 'Please enter a valid 6-digit code.'})

            family = Family.objects.filter(invite_code=code).first()
            if family:
                user.family = family
                user.save()
                return redirect("home")
            else:
                return render(request, "join_family.html", {'error': 'Couldnt Find Family, Try Again'})

        else:
            return render(request, "join_family.html", {'error': 'Invalid code. Please try again.'})

    return redirect("home")

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created successfully. Please log in.')
            return redirect('/accounts/login', {"messages": ["Account Created, Please Log In"]})  # Replace 'login' with the name of your login view
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()

    return render(request, 'create_account.html', {'form': form})