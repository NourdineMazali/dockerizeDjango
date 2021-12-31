from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django_rest_passwordreset.models import ResetPasswordToken

from Users.models import User

# remove these lines if you want these models on admin
admin.site.unregister(Group)
admin.site.unregister(ResetPasswordToken)


class UserAdmin(BaseUserAdmin):
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = (
        'email',
        'first_name',
        'id',
    )

    list_filter = (
        'is_admin',
        'is_verified',
        'is_premium'
    )

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name','last_name','phone_number')}),
        ('Account status', {'fields': ('is_verified', 'is_premium')}),
        ('Permissions', {'fields': ('is_admin',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = (['created_at', 'updated_at', 'id'])

    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2'),
        }),
    )
    search_fields = ('email','id')

    ordering = (
        'id',
        'email',
        'first_name'
    )

    filter_horizontal = ()


admin.site.register(User, UserAdmin)
