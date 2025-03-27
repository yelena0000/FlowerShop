from django.contrib import admin
from flowers.models import Buyer, Delivery, Consult

@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ('buyer_name', 'buyer_phone')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('buyer_name', 'address', 'is_finished')


@admin.register(Consult)
class ConsultAdmin(admin.ModelAdmin):
    list_display = ('buyer_name', 'buyer_phone', 'is_finished')
