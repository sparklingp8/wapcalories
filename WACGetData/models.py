from django.db import models
import time

from django.db import models
from datetime import date


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]

    user_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    dob = models.DateField()

    # Physical measurements
    weight = models.FloatField(null=True, blank=True, help_text="Current weight in kg")
    height = models.FloatField(null=True, blank=True, help_text="Height in cm")
    weight_last_updated = models.DateField(null=True, blank=True, help_text="Date when weight was last updated")

    # Weight and nutrition goals
    desired_weight = models.FloatField(null=True, blank=True, help_text="Target weight in kg")
    calories_needed = models.FloatField(null=True, blank=True, help_text="Total calories needed to achieve desired weight")
    target_protein = models.FloatField(null=True, blank=True, help_text="Target protein in grams per day")
    target_carbs = models.FloatField(null=True, blank=True, help_text="Target carbs in grams per day")
    target_fat = models.FloatField(null=True, blank=True, help_text="Target fat in grams per day")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} - {self.name}"

    @property
    def age(self):
        today = date.today()
        return today.year - self.dob.year - (
            (today.month, today.day) < (self.dob.month, self.dob.day)
        )


class PhoneNumberMapping(models.Model):
    phone_number = models.CharField(max_length=20, unique=True, db_index=True)
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="phone_mapping"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.phone_number} - {self.user.user_id}"


class DailyEntry(models.Model):
    date = models.DateField(db_index=True)
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="entries"
    )
    time = models.TimeField()

    value1 = models.FloatField() #protien
    value2 = models.FloatField() #carbs
    value3 = models.FloatField() #fat
    current_calories = models.FloatField(null=True, blank=True, help_text="Sum of all calories for this day before this entry")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('date', 'user', 'time')
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.date} - {self.user.user_id} - {self.time}"

