import re

from django import forms
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from core.models import StaffProfile
from core.permissions import role_required, user_role
from enquiries.models import Enquiry

FIELD = (
    "mt-1 w-full rounded-md border border-garden-900/20 bg-white px-3 py-2 text-sm "
    "focus:border-garden-600 focus:outline-none focus:ring-1 focus:ring-garden-600"
)
CLOSED = [Enquiry.Status.CONFIRMED, Enquiry.Status.NOT_CONVERTED, Enquiry.Status.CANCELLED]


def style(form):
    for field in form.fields.values():
        field.widget.attrs["class"] = FIELD
    return form


class ProfileForm(forms.Form):
    first_name = forms.CharField(label="First name", max_length=150)
    last_name = forms.CharField(label="Last name", max_length=150, required=False)
    email = forms.EmailField(label="Email", required=False)
    phone = forms.CharField(label="Phone", max_length=20, required=False)
    job_title = forms.CharField(label="Job title", max_length=80, required=False)

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if phone and not re.fullmatch(r"[+0-9 ()\-]{7,20}", phone):
            raise forms.ValidationError("Enter a phone number, for example 0712 345 678.")
        return phone


@never_cache
@role_required("reception", "manager")
def profile(request):
    user = request.user
    prof = StaffProfile.for_user(user)
    info = ProfileForm(initial={
        "first_name": user.first_name, "last_name": user.last_name, "email": user.email,
        "phone": prof.phone, "job_title": prof.job_title,
    })
    pwd = PasswordChangeForm(user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "details":
            info = ProfileForm(request.POST)
            if info.is_valid():
                d = info.cleaned_data
                user.first_name, user.last_name, user.email = d["first_name"], d["last_name"], d["email"]
                user.save(update_fields=["first_name", "last_name", "email"])
                prof.phone, prof.job_title = d["phone"], d["job_title"]
                prof.save()
                messages.success(request, "Your details are saved.")
                return redirect("staff_profile")
        elif action == "password":
            pwd = PasswordChangeForm(user, request.POST)
            if pwd.is_valid():
                user = pwd.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password is changed.")
                return redirect("staff_profile")

    return render(request, "staff/profile.html", {
        "role": user_role(user), "nav": "profile",
        "info": style(info), "pwd": style(pwd),
        "open_count": Enquiry.objects.filter(assigned_to=user).exclude(status__in=CLOSED).count(),
    })
