import re

from django import forms
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from core import team
from core.models import StaffProfile
from core.permissions import role_required, user_role
from core.profile_views import style

ROLE_CHOICES = [("reception", "Reception"), ("manager", "Manager")]


class NewMemberForm(forms.Form):
    first_name = forms.CharField(label="First name", max_length=150)
    last_name = forms.CharField(label="Last name", max_length=150, required=False)
    username = forms.CharField(label="Username", max_length=150, help_text="Used to sign in. Letters, numbers, dots, dashes and underscores.")
    email = forms.EmailField(label="Email", required=False)
    phone = forms.CharField(label="Phone", max_length=20, required=False)
    job_title = forms.CharField(label="Job title", max_length=80, required=False)
    role = forms.ChoiceField(label="Role", choices=ROLE_CHOICES)
    password = forms.CharField(
        label="Starting password", widget=forms.PasswordInput(render_value=False),
        help_text="Share it with them in person. They can change it under My profile.",
    )

    def clean_username(self):
        name = self.cleaned_data["username"].strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]{3,150}", name):
            raise ValidationError("Use at least 3 letters, numbers, dots, dashes or underscores.")
        if User.objects.filter(username__iexact=name).exists():
            raise ValidationError("That username is already taken.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if phone and not re.fullmatch(r"[+0-9 ()\-]{7,20}", phone):
            raise ValidationError("Enter a phone number, for example 0712 345 678.")
        return phone

    def clean(self):
        data = super().clean()
        if data.get("password"):
            try:
                validate_password(data["password"])
            except ValidationError as exc:
                self.add_error("password", exc)
        return data


class RoleForm(forms.Form):
    role = forms.ChoiceField(label="Role", choices=ROLE_CHOICES)


@never_cache
@role_required("manager")
def team_list(request):
    members = list(
        team.team_queryset().annotate(
            open_count=Count(
                "assigned_enquiries",
                filter=~Q(assigned_enquiries__status__in=team.CLOSED),
                distinct=True,
            )
        )
    )
    for m in members:
        m.role_name = user_role(m)
    return render(request, "team/list.html", {"role": "manager", "nav": "team", "members": members})


@never_cache
@role_required("manager")
def team_new(request):
    form = NewMemberForm(request.POST or None, initial={"role": "reception"})
    if request.method == "POST" and form.is_valid():
        user = team.create_member(form.cleaned_data)
        messages.success(
            request,
            f"{user.get_full_name() or user.username} can now sign in. Give them the password you set; "
            "they can change it under My profile.",
        )
        return redirect("staff_team_member", pk=user.pk)
    return render(request, "team/new.html", {"role": "manager", "nav": "team", "form": style(form)})


@never_cache
@role_required("manager")
def team_member(request, pk):
    member = get_object_or_404(team.team_queryset(), pk=pk)
    name = member.get_full_name() or member.username

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "role":
                form = RoleForm(request.POST)
                if form.is_valid():
                    team.set_role(member, form.cleaned_data["role"], request.user)
                    messages.success(request, f"{name} is now {form.cleaned_data['role']}.")
            elif action == "deactivate":
                released = team.deactivate(member, request.user)
                extra = f" Their {released} open enquiries were unassigned." if released else ""
                messages.success(request, f"{name} can no longer sign in.{extra}")
            elif action == "reactivate":
                team.reactivate(member)
                messages.success(request, f"{name} can sign in again.")
            elif action == "password":
                pwd = SetPasswordForm(member, request.POST)
                if pwd.is_valid():
                    pwd.save()
                    if member.pk == request.user.pk:
                        update_session_auth_hash(request, member)
                    messages.success(request, f"New password set for {name}.")
                else:
                    messages.error(request, " ".join(e for errs in pwd.errors.values() for e in errs))
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
        return redirect("staff_team_member", pk=member.pk)

    return render(request, "team/member.html", {
        "role": "manager", "nav": "team", "member": member, "name": name,
        "member_role": user_role(member),
        "profile": StaffProfile.objects.filter(user=member).first(),
        "role_form": style(RoleForm(initial={"role": user_role(member)})),
        "pwd": style(SetPasswordForm(member)),
        "open_count": member.assigned_enquiries.exclude(status__in=team.CLOSED).count(),
        "is_self": member.pk == request.user.pk,
    })
