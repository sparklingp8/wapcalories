from django.db import models

class Quote(models.Model):
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "created_at": self.created_at.isoformat()
        }

    def __str__(self):
        return f"{self.text}"
