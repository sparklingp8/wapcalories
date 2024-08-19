from django.db import models
import time

from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField

class PersonData(models.Model):
    person_id = models.IntegerField(unique=True)
    cal_data = models.JSONField()  # Use JSONField to store a list of dictionaries

    def add_data(self, cal):
        """
        Adds a dictionary with today's date in 'dd/mm/yyyy' format as the key and a list of integers as the value.
        """
        today_date = time.strftime('%d/%m/%Y')  # Get today's date in 'dd/mm/yyyy' format
        if today_date not in self.cal_data:
            self.cal_data[today_date]=[cal]
        else:
            self.cal_data[today_date].append(cal)


        # Append new data

        self.save()
    def __str__(self):
        return f"Data for person {self.person_id} calories data {self.cal_data}"