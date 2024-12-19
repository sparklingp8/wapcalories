from django.db import models

# Create your models here.
class Event(models.Model):
    creator_id = models.CharField(max_length=255)
    data = models.JSONField(default=dict)
    creator_pin =  models.IntegerField(default=0, null=False, blank=False) 
    
    def __str__(self):
        return f"Event for Creator {self.creator_id}, Countdowns List: {self.data["events"]}"
    
    class Meta:
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
