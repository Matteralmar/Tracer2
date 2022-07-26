from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser



class User(AbstractUser):
    ROLE_CHOICES = [
        ('tester', 'Tester'),
        ('developer', 'Developer'),
        ('project_manager', 'Project Manager'),
    ]
    username = models.CharField(max_length=30, unique=True)
    email = models.CharField(max_length=90, unique=True)
    is_organizer = models.BooleanField(default=True)
    is_member = models.BooleanField(default=False)
    role = models.TextField(choices=ROLE_CHOICES)
    ticket_flow = models.ForeignKey('Project', null=True, blank=True, on_delete=models.SET_NULL)
    #ticket_flow = models.ManyToManyField('Project')

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Account, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

class Project(models.Model):
    PROGRESS_CHOICES = [
        ('opened', 'Opened'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]
    title = models.CharField(max_length=32, blank=False, null=False, unique=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    progress = models.TextField(choices=PROGRESS_CHOICES, null=True)
    organisation = models.ForeignKey(Account, on_delete=models.CASCADE, blank=False, null=False)
    project_manager = models.ForeignKey("Member", null=True, blank=True, on_delete=models.SET_NULL)
    color_code = models.CharField(max_length=100, default='#563d7c')
    archive = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Status(models.Model):
    name = models.CharField(max_length=30)
    organisation = models.ForeignKey(Account, on_delete=models.CASCADE)
    color_code = models.CharField(max_length=100, default='#563d7c')
    test_status = models.BooleanField(default=False)

    def __str__(self):
        if self.name:
            return self.name


class Priority(models.Model):
    name = models.CharField(max_length=30)
    organisation = models.ForeignKey(Account, on_delete=models.CASCADE)
    color_code = models.CharField(max_length=100, default='#563d7c')

    def __str__(self):
        if self.name:
            return self.name

class Type(models.Model):
    name = models.CharField(max_length=30)
    organisation = models.ForeignKey(Account, on_delete=models.CASCADE)
    color_code = models.CharField(max_length=100, default='#563d7c')

    def __str__(self):
        if self.name:
            return self.name

class Ticket(models.Model):
    title = models.CharField(max_length=32)
    organisation = models.ForeignKey(Account, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey("Member", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.ForeignKey("Status", null=True, blank=True, on_delete=models.SET_NULL)
    priority = models.ForeignKey("Priority", null=True, blank=True, on_delete=models.SET_NULL)
    type = models.ForeignKey("Type", null=True, blank=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(default=timezone.now)
    due_to = models.DateTimeField(auto_now_add=False, auto_now=False, blank=True, null=True, default=timezone.now)
    description = models.TextField(max_length=1000, blank=False, null=False)
    author = models.ForeignKey("User", null=True, blank=True, on_delete=models.SET_NULL, related_name='tickets')
    project = models.ForeignKey('Project', related_name='tickets', on_delete=models.CASCADE)
    tester = models.ForeignKey("User", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.title

def handle_upload_comments(instance, filename):
    return f"ticket_comments/ticket_{instance.ticket.pk}/{filename}"

class Notification(models.Model):
    title = models.TextField()
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    recipient = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications')


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey("User", null=True, blank=True, on_delete=models.SET_NULL)
    date_added = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    file = models.FileField(null=True, blank=True, upload_to=handle_upload_comments)

    def __str__(self):
        return self.ticket.title




def post_user_created_signal(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(user=instance)

post_save.connect(post_user_created_signal, sender=User)