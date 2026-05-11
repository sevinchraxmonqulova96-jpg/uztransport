from django.db import models

class Region(models.Model):
    name = models.CharField(max_length=100)
    name_uz = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    center_lat = models.FloatField()
    center_lng = models.FloatField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Viloyat'
        verbose_name_plural = 'Viloyatlar'
        ordering = ['name']

    def __str__(self):
        return self.name_uz
