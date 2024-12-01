from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
import random
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

        if action == "leave_family":
            user = request.user
            user.family = None
            user.save()
            return redirect("family-select")

        # Ensure the gift exists
        gift = get_object_or_404(Gift, id=gift_id)

        if action == 'delete':
            # Delete gift logic
            if gift.user_paired == request.user and gift.is_claimed:
                notification = Notification(user_sent_to=gift.user_claimed, message=f"Gift '{gift.name}' has been deleted. You have automatically unclaimed this gift.")
                notification.save()
                gift.delete()
                
            elif gift.user_paired == request.user:
                gift.delete()
            

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
    user = request.user
    if user.family == None:
        return redirect("family-select")
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
    if user.family == None:
        return redirect("family-select")
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
    users = User.objects.filter(family=user.family)
    users = users.exclude(id=user.id)

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

    if user.family:
        return redirect("home")  # Redirect if the user is already in a family

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "join_family":
            code = request.POST.get("code")

            # Validate the invite code
            if not code or not code.isdigit() or len(code) != 6:
                return render(request, "join_family.html", {
                    "error": "Please enter a valid 6-digit code."
                })

            family = Family.objects.filter(invite_code=code).first()
            if family:
                user.family = family
                user.save()
                messages.success(request, "Successfully joined the family!")
                return redirect("home")
            else:
                return render(request, "join_family.html", {
                    "error": "Family not found. Please try again."
                })

        elif action == "create_family":
            family_name = request.POST.get("family_name")

            # Validate the family name
            if not family_name or len(family_name.strip()) == 0:
                return render(request, "join_family.html", {
                    "error": "Please enter a valid family name."
                })

            # Create a new family
            family = Family.objects.create(name=family_name, invite_code=random.randint(1, 999999))
            if Family.objects.filter(name=family_name).count() > 1:
                family.delete()
                return render(request, "join_family.html", {
                    "error": "Family name already exists. Please try again."
                })
            if Family.objects.filter(invite_code=family.invite_code).count() > 1:
                family.delete()
                return render(request, "join_family.html", {
                    "error": "There was an error. Please try again."
                })
            user.family = family
            user.save()
            return redirect("home")

    return render(request, "join_family.html")

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
        form = CustomUserCreationForm()

    return render(request, 'create_account.html', {'form': form})