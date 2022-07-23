from django.contrib import admin

from .models import *

admin.site.register(Type)
admin.site.register(User)
admin.site.register(Priority)
admin.site.register(Project)
admin.site.register(Account)
admin.site.register(Ticket)
admin.site.register(Member)
admin.site.register(Status)
admin.site.register(Comment)
admin.site.register(Notification)