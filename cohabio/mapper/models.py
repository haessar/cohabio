from django.db import models


class UserInfo(models.Model):
    time_stamp = models.DateTimeField('date published', auto_now_add=True)
    entries = models.IntegerField(default=0)
    work1 = models.CharField(max_length=200, default="-")
    work2 = models.CharField(max_length=200, default="-")
    trans1 = models.CharField(max_length=200, default="-")
    trans2 = models.CharField(max_length=200, default="-")
    mcom1 = models.IntegerField(default=0)
    mcom2 = models.IntegerField(default=0)
    results = models.IntegerField(default=0)
    def __str__(self):
        return str(self.time_stamp)
    def entry_count(self):
        return self.entries
    def location_1(self):
        return self.work1
    def location_2(self):
        return self.work2
    def transport_1(self):
        return self.trans1
    def transport_2(self):
        return self.trans2
    def max_commute_1(self):
        return self.mcom1
    def max_commute_2(self):
        return self.mcom2
    def rslts(self):
        return self.results
    class Meta:
        app_label = 'mapper'
        ordering = ['time_stamp']

class PlaceData(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=20, decimal_places=8)
    longitude = models.DecimalField(max_digits=20, decimal_places=8)
    population = models.IntegerField(null=True)
    usage = models.IntegerField(null=True)
    country_code = models.CharField(max_length=5)
    def __str__(self):
        return self.name
    class Meta:
        app_label = 'mapper'
        verbose_name = 'Place Data'
        verbose_name_plural = verbose_name
