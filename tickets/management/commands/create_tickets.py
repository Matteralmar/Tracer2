from django.core.management.base import BaseCommand
from csv import DictReader
from tickets.models import *
import datetime
from django.utils.timezone import utc

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str)
        parser.add_argument('organizer_email', type=str)

    def handle(self, *args, **options):
        file_name = options['file_name']
        organizer_email = options['organizer_email']

        organisation = Account.objects.get(user__email=organizer_email)
        now = datetime.datetime.utcnow().replace(tzinfo=utc)

        with open(file_name, 'r') as read_obj:
            csv_reader = DictReader(read_obj)
            for row in csv_reader:
                title = row['title']
                assigned_to = row['assigned_to']
                author = row['author']
                project = row['project']
                deadline = row['deadline']

                Ticket.objects.create(
                    title=title,
                    assigned_to=Member.objects.get(user__username=assigned_to),
                    author=User.objects.get(username=author),
                    project=Project.objects.get(title=project),
                    deadline=deadline,
                    organisation=organisation,
                    created_date=now,
                )