from datetime import timedelta
import random

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from store.models import (
    CartItem,
    Category,
    CustomerProfile,
    MerchantProfile,
    Item,
    ItemVariant,
    Order,
    OrderStatus,
    Purchase,
)


class Command(BaseCommand):
    help = "This command populates the database with default db"

    def handle(self, *_, **__):
        PASSWORD = "shark@123"

        self.create_super_user(email="admin@example.com", password=PASSWORD)
        self.categories = self.create_categories()

        for i in range(10):
            name = "merchant" if i == 0 else f"merchant{i}"
            user = self.create_merchant(
                details=self.create_merchant_details(name, PASSWORD)
            )
            self.create_items(user)

        for i in range(10):
            name = "customer" if i == 0 else f"customer{i}"
            customer_details = self.create_customer_details(name, PASSWORD)
            user = self.create_customer(details=customer_details)
            self.create_random_transactions(user=user, size=5)
            self.create_random_cart(user=user, size=5)

    def create_customer_details(self, name, password):
        return {
            "password": password,
            "email": f"{name}@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "address": "Kathmandu, Nepal",
            "contact": "+9779840424012",
        }

    def create_merchant_details(self, name, password):
        return {
            "password": password,
            "email": f"{name}@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "address": "Kathmandu, Nepal",
            "contact": "+9779840424012",
            "reason_for_signup": "reason",
        }

    def create_merchant(self, details):
        user = get_user_model().objects.create_user(
            password=details["password"],
            email=details["email"],
            date_joined=timezone.now() - timedelta(days=random.randint(0, 10)),
        )
        user.save()

        MerchantProfile.objects.create(
            user=user,
            first_name=details["first_name"],
            last_name=details["last_name"],
            address=details["address"],
            contact=details["contact"],
            reason_for_signup=details["reason_for_signup"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created merchant '{details['email']}'"
                f", with password '{details['password']}'"
            )
        )
        return user

    def create_categories(self):
        categories = (
            {"name": "Greens", "description": "Your typical green vegetable"},
            {"name": "Beans", "description": "Seed that are meant to be eaten"},
            {
                "name": "Lentils",
                "description": "having flat pods containing lens-shaped, edible seeds.",
            },
            {"name": "Fruits", "description": "Sweet and high in fructose."},
            {"name": "Fresh", "description": "Brought in recently"},
            {"name": "Dried", "description": "Made of synthetic material"},
        )
        ret = [Category.objects.create(**category) for category in categories]
        self.stdout.write(self.style.SUCCESS(f"Added {len(categories)} categories"))
        return ret

    def create_items(self, merchant):
        items = (
            {"name": "Tomato", "description": "It is tomato."},
            {"name": "Potato", "description": "It is potato."},
            {"name": "Cabbage", "description": "It is cabbage."},
            {"name": "Peas", "description": "It is peas."},
            {"name": "Radish", "description": "It is radish."},
            {"name": "Carrot", "description": "It is carrot."},
            {"name": "Gourd", "description": "It is gourd."},
            {"name": "Spinach", "description": "It is spinach."},
            {"name": "Sweet Potato", "description": "It is sweet potato."},
            {"name": "Chilli", "description": "It is chilli."},
        )
        variants = (
            {"color": "Yellow"},
            {"color": "White"},
            {"color": "Red"},
            {"color": "Green"},
        )
        item_instances = []
        variant_instances = []
        for item in items:
            i = Item.objects.create(
                user=merchant, **item, subtitle=f"{item['description'][0:50]}..."
            )
            i.categories.set(random.sample(self.categories, 3))
            item_instances.append(i)

            for variant in variants:
                v = ItemVariant.objects.create(
                    item=i,
                    rate=random.randint(200, 1000) % 10,
                    stock=random.randint(0, 100) % 10,
                    **variant,
                )
                variant_instances.append(v)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Added {item['name']} variant {variant['color']}"
                    )
                )

        return item_instances, variant_instances

    def create_customer(self, details):
        user = get_user_model().objects.create_user(
            password=details["password"],
            email=details["email"],
            date_joined=timezone.now() - timedelta(days=random.randint(0, 10)),
        )
        user.save()

        CustomerProfile.objects.create(
            user=user,
            first_name=details["first_name"],
            last_name=details["last_name"],
            address=details["address"],
            contact=details["contact"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created customer '{details['email']}', "
                f"with password '{details['password']}'"
            )
        )
        return user

    def create_super_user(self, email, password):
        user = get_user_model().objects.create_user(
            password=password, email=email, email_verified=True
        )
        user.is_superuser = True
        user.is_staff = True
        user.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"Created superuser {email}, " "with password '{password}'"
            )
        )
        return user

    def create_random_transactions(self, user, size=1):
        for _ in range(size):
            order = Order.objects.create(
                user=user,
                timestamp=timezone.now() - timedelta(days=random.randint(0, 10)),
                status=random.randint(0, len(OrderStatus.values) - 1),
            )

            for item_variant in random.sample(list(ItemVariant.objects.all()), 5):
                Purchase.objects.create(
                    order=order,
                    item_variant=item_variant,
                    quantity=random.randint(1, 10),
                )
        self.stdout.write(self.style.SUCCESS(f"Created {size} random orders"))

    def create_random_cart(self, user, size=1):
        for item_variant in random.sample(list(ItemVariant.objects.all()), 5):
            CartItem.objects.create(
                cart=user.cart,
                item_variant=item_variant,
                quantity=random.randint(1, 10),
            )
        self.stdout.write(self.style.SUCCESS(f"Filled cart with {size} items"))
