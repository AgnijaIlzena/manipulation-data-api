from django.core.cache import cache
from django.db.models import Count, Sum

from portal.models import Customer, ImportReport


DASHBOARD_STATS_CACHE_KEY = "dashboard:stats"
DASHBOARD_STATS_TTL = 300


def get_dashboard_stats():
    cached_stats = cache.get(DASHBOARD_STATS_CACHE_KEY)

    if cached_stats is not None:
        return cached_stats

    stats = {
        "total_customers": Customer.objects.count(),
        "total_reports": ImportReport.objects.count(),
        "total_inserted_rows": ImportReport.objects.aggregate(
            total=Sum("inserted_rows")
        )["total"] or 0,
        "total_rejected_rows": ImportReport.objects.aggregate(
            total=Sum("rejected_rows")
        )["total"] or 0,
        "customers_by_city": list(
            Customer.objects
            .values("city")
            .annotate(total=Count("id"))
            .order_by("-total")
        ),
    }

    cache.set(DASHBOARD_STATS_CACHE_KEY, stats, DASHBOARD_STATS_TTL)

    return stats
