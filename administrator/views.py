from datetime import timedelta

from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from store import models


def brief_info(request):
    pending_orders = models.Order.objects.filter(
        status=models.OrderStatus.Pending
    ).count()
    completed_orders = models.Order.objects.filter(
        status=models.OrderStatus.Delivered
    ).count()

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    active_users = (
        get_user_model()
        .objects.filter(last_login__gte=today - timedelta(days=30))
        .count()
    )

    return render(
        request,
        "admin/addons/index/brief_info.html",
        {
            "infos": [
                {
                    "title": _("Pending Orders"),
                    "statistic": pending_orders,
                    "icon": "fa-shopping-cart",
                },
                {
                    "title": _("Completed Orders"),
                    "statistic": completed_orders,
                    "icon": "fa-carrot",
                },
                {
                    "title": _("Active Users"),
                    "statistic": active_users,
                    "icon": "fa-user-check",
                },
            ]
        },
    )


def recent_orders(request, count):
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    orders_all = models.Order.objects.all()
    sales = []
    for i in range(count):
        date = today - timedelta(days=i)
        orders = orders_all.filter(
            timestamp__gte=date, timestamp__lte=date + timedelta(days=1)
        )
        sales.append(sum(order.total_items() for order in orders))
    sales = list(reversed(sales))
    return render(
        request, "admin/addons/index/charts/recent_orders.html", {"orders": sales}
    )


def top_items(request, count):
    items_sales = {}
    for purchase in models.Purchase.objects.all():
        pk = purchase.item_variant.item.pk
        item_sales = items_sales.get(pk, 0)
        items_sales[pk] = item_sales + purchase.quantity

    sorted_sales = sorted(items_sales.items(), key=lambda x: x[1], reverse=True)

    for i, (pk, cnt) in enumerate(sorted_sales):
        sorted_sales[i] = (models.Item.objects.get(pk=pk).name, cnt)

    sorted_sales = list(sorted_sales[:count])
    labels, values = zip(*sorted_sales) if sorted_sales else ((), ())
    return render(
        request,
        "admin/addons/index/charts/top_items.html",
        {"labels": labels, "values": values},
    )


def top_categories(request, count):
    items_sales = {}
    for purchase in models.Purchase.objects.all():
        for category in purchase.item_variant.item.categories.all():
            pk = category.pk
            item_sales = items_sales.get(pk, 0)
            items_sales[pk] = item_sales + purchase.quantity

    sorted_sales = sorted(items_sales.items(), key=lambda x: x[1], reverse=True)

    for i, (pk, cnt) in enumerate(sorted_sales):
        sorted_sales[i] = (models.Category.objects.get(pk=pk).name, cnt)

    sorted_sales = list(sorted_sales[:count])
    labels, values = zip(*sorted_sales) if sorted_sales else ((), ())
    return render(
        request,
        "admin/addons/index/charts/top_categories.html",
        {"labels": labels, "values": values},
    )


def user_activity(request, count):
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    users_all = get_user_model().objects.all()
    new_users = []
    for i in range(count):
        date = today - timedelta(days=i)
        new_users.append(
            users_all.filter(
                date_joined__gte=date, date_joined__lte=date + timedelta(days=1)
            ).count()
        )
    new_users = list(reversed(new_users))

    return render(
        request,
        "admin/addons/index/charts/user_activity.html",
        {"new_users": new_users},
    )
