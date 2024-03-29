from django.core.management.base import BaseCommand

from psycopg2 import OperationalError as psycopg2Error
from django.db.utils import OperationalError
import time


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write('waiting for db...')
        db_up = False

        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (psycopg2Error, OperationalError):
                self.stdout.write('database unavailable, waiting 1 sec')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('database available'))
