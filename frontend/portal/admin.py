from django.contrib import admin
from .models import Customer, ImportReport


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'city', 'state', 'email', 'customer_external_id', 'created_at')
    search_fields = ('full_name', 'email', 'customer_external_id', 'city')
    list_filter = ('state', 'city')
    readonly_fields = ('customer_external_id', 'created_at')
    ordering = ('-created_at',)


@admin.register(ImportReport)
class ImportReportAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'total_rows', 'inserted_rows', 'rejected_rows', 'created_at')
    search_fields = ('file_name',)
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
