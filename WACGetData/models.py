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

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('date', 'user', 'time')
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.date} - {self.user.user_id} - {self.time}"

# from datetime import date
# from app.models import UserProfile

# UserProfile.objects.create(
#     user_id=9143,
#     name="Rahul",
#     gender="M",
#     dob=date(1998, 5, 14)
# )



# 1️⃣ Get All Data For User X On Day M
# from datetime import date
# from app.models import UserProfile, DailyEntry

# def get_data_for_day(user_id, year, month, day):
#     target_date = date(year, month, day)

#     entries = DailyEntry.objects.filter(
#         user__user_id=user_id,
#         date=target_date
#     ).order_by("time")

#     return entries



# 2️⃣ Get Data From Day M To N
# def get_data_range(user_id, start_date, end_date):
#     entries = DailyEntry.objects.filter(
#         user__user_id=user_id,
#         date__range=(start_date, end_date)
#     ).order_by("date", "time")

#     return entries

# ✅ 3️⃣ Get Daily Total For User
# from django.db.models import Sum

# def get_daily_total(user_id, target_date):
#     totals = DailyEntry.objects.filter(
#         user__user_id=user_id,
#         date=target_date
#     ).aggregate(
#         total_v1=Sum("value1"),
#         total_v2=Sum("value2"),
#         total_v3=Sum("value3")
#     )

#     return totals


# ✅ 4️⃣ Weekly Summary For User
# from django.db.models import Sum

# def weekly_summary(user_id, start_date, end_date):
#     summary = (
#         DailyEntry.objects
#         .filter(
#             user__user_id=user_id,
#             date__range=(start_date, end_date)
#         )
#         .values("date")
#         .annotate(
#             total_v3=Sum("value3")
#         )
#         .order_by("date")
#     )

#     return summary


# 5️⃣ User Add
# from datetime import date

# def add_user(user_id, name, gender, dob):
#     user, created = UserProfile.objects.get_or_create(
#         user_id=user_id,
#         defaults={
#             "name": name,
#             "gender": gender,
#             "dob": dob
#         }
#     )

#     return user, created



# ✅ 6️⃣ Update Data
# Update User
# def update_user_name(user_id, new_name):
#     UserProfile.objects.filter(user_id=user_id).update(name=new_name)


# Delete Data
# Delete Single Entry
# def delete_entry(user_id, target_date, target_time):
#     DailyEntry.objects.filter(
#         user__user_id=user_id,
#         date=target_date,
#         time=target_time
#     ).delete()