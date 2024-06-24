from django.db import models

class Configurations(models.Model):
    
    class Meta:
        app_label = 'core'
        db_table = 'configurations'
    
    config = models.JSONField(default=dict)
    
    def __str__(self):
        return f"Configurations object ({self.pk})"
    
