from django.db import models

class Contest(models.Model):
    description = models.ForeignKey('system.Post')
    verification = models.ForeignKey('base.DataGrader', related_name='+')
    test = models.ForeignKey('base.DataGrader', related_name='+')
