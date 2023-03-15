import urllib.request
from os.path import isfile
import csv
import io
from PIL import Image
from datetime import timedelta
import random

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.base import ContentFile


from store.models import (
    CartItem,
    Category,
    CustomerProfile,
    MerchantProfile,
    Item,
    ItemVariant,
    ItemVariantImage,
    Order,
    OrderStatus,
    Purchase,
    Rating,
)


class Command(BaseCommand):
    help = "This command populates the database with default db"

    def handle(self, *_, **__):
        if not self.download_images():
            return False

        if get_user_model().objects.count() != 0:
            self.stderr.write(self.style.ERROR("Database is not empty. Aborting."))
            return False

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

        self.create_random_ratings()

    def get_image_filename(self, item_id, variant_id):
        return f"res/downloaded_images/{item_id}_{variant_id}.webp"

    def download_images(self):
        encountered_errors = False
        with open("res/vegetables.csv", newline="") as crops_file:
            crops_reader = csv.reader(crops_file)
            next(crops_reader, None)
            for item_id, crop in enumerate(crops_reader):
                _, __, ___, *variants = crop

                for variant_id, variant in enumerate(variants):
                    _, url = variant.split(",", 1)
                    filename = self.get_image_filename(item_id, variant_id)
                    if not isfile(filename):
                        try:
                            response = urllib.request.urlopen(
                                urllib.request.Request(
                                    url, headers={"User-Agent": "Mozilla/5.0"}
                                )
                            )
                            image = Image.open(io.BytesIO(response.read()))
                            image.save(filename)
                            self.stdout.write(
                                self.style.SUCCESS(f"Saved image {filename}")
                            )
                        except Exception as e:
                            self.stderr.write(
                                self.style.ERROR(f"Failed to download image {url}: {e}")
                            )
                            encountered_errors = True
        return not encountered_errors

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
        categories = []
        with open("res/vegetables.csv", newline="") as crops_file:
            crops_reader = csv.reader(crops_file)
            next(crops_reader, None)
            for crop in crops_reader:
                _, __, _categories, *___ = crop
                categories.extend(x.strip() for x in _categories.split(","))
        categories_ = [
            {"name": x, "description": f"This is description for {x}"}
            for x in set(categories)
        ]
        ret = [Category.objects.create(**category) for category in categories_]
        self.stdout.write(self.style.SUCCESS(f"Added {len(categories_)} categories"))
        return ret

    def create_items(self, merchant):
        items = []
        with open("res/vegetables.csv", newline="") as crops_file:
            crops_reader = csv.reader(crops_file)
            next(crops_reader, None)
            for crop_id, crop in enumerate(crops_reader):
                item_name, description, categories, *_variants = crop
                variants = []
                for variant_id, variant in enumerate(_variants):
                    name, _ = (x.strip() for x in variant.split(",", 1))
                    filename = self.get_image_filename(crop_id, variant_id)
                    variants.append(
                        {
                            "color": name,
                            "rate": random.randint(200, 1000) % 10,
                            "stock": random.randint(0, 100) % 10,
                            "images": [filename],
                        }
                    )
                items.append(
                    {
                        "name": item_name,
                        "description": description,
                        "categories": [x.strip() for x in categories.split(",")],
                        "variants": variants,
                    }
                )

        item_instances = []
        variant_instances = []
        for item in items:
            variants = item.pop("variants")
            categories = item.pop("categories")
            i = Item.objects.create(
                user=merchant, **item, subtitle=f"{item['description'][0:50]}..."
            )
            for category_name in categories:
                i.categories.add(Category.objects.filter(name=category_name).first())
            item_instances.append(i)

            for variant in variants:
                images = variant.pop("images")
                v = ItemVariant.objects.create(item=i, **variant)
                variant_instances.append(v)
                for image_path in images:
                    with open(image_path, "rb") as f:
                        data = f.read()
                        ii = ItemVariantImage.objects.create(item_variant=v)
                        ii.image.save(filename, ContentFile(data))
            self.stdout.write(self.style.SUCCESS(f"Added {item['name']}"))
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

    def create_random_ratings(self):
        for item in Item.objects.all():
            customers = CustomerProfile.objects.all()
            for customer in customers:
                p = 0.5
                if random.random() < p:
                    Rating.objects.create(
                        user=customer.user,
                        item=item,
                        rating=random.randint(1, 5),
                    )
        self.stdout.write(self.style.SUCCESS("Created random ratings"))

    def create_random_cart(self, user, size=1):
        for item_variant in random.sample(list(ItemVariant.objects.all()), 5):
            CartItem.objects.create(
                cart=user.cart,
                item_variant=item_variant,
                quantity=random.randint(1, 10),
            )
        self.stdout.write(self.style.SUCCESS(f"Filled cart with {size} items"))
