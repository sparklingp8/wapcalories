from django.db import models

# Create your models here.
class Event(models.Model):
    creator_id = models.CharField(max_length=255)
    data = models.JSONField(default=dict)
    
    def __str__(self):
        return f"Event for Creator {self.creator_id}, Countdowns List: {self.data["events"]}"
    
    class Meta:
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
