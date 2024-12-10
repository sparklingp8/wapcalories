from django.db import models

# Create your models here.
class Event(models.Model):
    event_name = models.CharField(max_length=255)
    target_time = models.DateTimeField()

    def __str__(self):
        return f"{self.event_name} - {self.target_time}"

    class Meta:
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        ordering = ['target_time']
