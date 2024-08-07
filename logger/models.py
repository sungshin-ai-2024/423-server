from django.db import models


class PPGData(models.Model):
    data = models.JSONField()

    def __str__(self):
        return str(self.data)

