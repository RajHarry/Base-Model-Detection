from django.db import models


# class StaticUpload(models.Model):
#     image = models.ImageField(upload_to="gallery/static/", null=True, blank=True)
#     name = models.CharField(max_length=32, blank=True)

#     def __str__(self):
#         return self.name

class DynamicUpload(models.Model):
    image = models.ImageField(upload_to="dynamic/", null=True, blank=True)
    name = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return self.name
