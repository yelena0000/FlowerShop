from django.contrib import admin
from flowers.models import Buyer, Delivery, Consult, Bouquet, Flower, BouquetFlower, BouquetReason, Shop


@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ('buyer_name', 'buyer_phone')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('buyer_name', 'address', 'is_finished')


@admin.register(Consult)
class ConsultAdmin(admin.ModelAdmin):
    list_display = ('buyer_name', 'buyer_phone', 'is_finished')


class BouquetFlowerInline(admin.TabularInline):
    model = BouquetFlower
    extra = 5


class BouquetReasonInline(admin.TabularInline):
    model = BouquetReason
    extra = 5


@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    list_display = ('title',)
    inlines = (BouquetFlowerInline, BouquetReasonInline)


@admin.register(Flower)
class FlowerAdmin(admin.ModelAdmin):
    list_display = ('title',)


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('title', )