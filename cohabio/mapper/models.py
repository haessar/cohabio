from django.db import models


class User(models.Model):
    workplace = models.CharField(max_length=200)
    transport = models.CharField(max_length=200)
    max_commute = models.IntegerField()
    elements = models.IntegerField()


class SearchResults(models.Model):
    time_stamp = models.DateTimeField(auto_now_add=True)
    you = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='results_you')
    them = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='results_them')
    results = models.IntegerField(default=0)

    class Meta:
        ordering = ['time_stamp']


class PlaceData(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=20, decimal_places=8)
    longitude = models.DecimalField(max_digits=20, decimal_places=8)
    population = models.IntegerField(null=True)
    usage = models.FloatField(null=True)
    country_code = models.CharField(max_length=5)
    source = models.CharField(max_length=10)

    def __str__(self):
        return self.name
