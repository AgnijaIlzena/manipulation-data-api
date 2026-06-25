from django.db import models


class Customer(models.Model):
    customer_external_id = models.CharField(max_length=255, unique=True)
    full_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f"{self.full_name} ({self.city}, {self.state})"


class ImportReport(models.Model):
    file_name = models.CharField(max_length=255)
    total_rows = models.PositiveIntegerField(default=0)
    inserted_rows = models.PositiveIntegerField(default=0)
    rejected_rows = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Rapport d'import"
        verbose_name_plural = "Rapports d'import"

    def __str__(self):
        return f"{self.file_name} — {self.inserted_rows}/{self.total_rows} lignes ({self.created_at.strftime('%Y-%m-%d')})"
