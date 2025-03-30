from django.contrib import admin
from flowers.models import (
    Shop, Occasion, Client,
    Flower, Bouquet, BouquetFlower, Order
)

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('title', 'address', 'phone_number')
    search_fields = ('title', 'address', 'phone_number')
    ordering = ('title',)

@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'is_consultation', 'created_at', 'consultation_status')
    list_filter = ('is_consultation', 'created_at')
    search_fields = ('name', 'phone')
    ordering = ('-created_at',)
    list_per_page = 20

    actions = ['mark_as_processed']

    @admin.display(description='Статус консультации')
    def consultation_status(self, obj):
        if obj.is_consultation:
            return 'Ожидает консультации'
        return 'Обычный клиент'

    def mark_as_processed(self, request, queryset):
        updated = queryset.filter(is_consultation=True).update(is_consultation=False)
        self.message_user(request, f"Отмечено {updated} консультаций как обработанные")

    mark_as_processed.short_description = "Пометить выбранные консультации как обработанные"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.GET.get('is_consultation__exact') == '1':
            return qs.filter(is_consultation=True).order_by('-created_at')
        return qs

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['consultation_count'] = Client.objects.filter(is_consultation=True).count()
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Flower)
class FlowerAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

class BouquetFlowerInline(admin.TabularInline):
    model = BouquetFlower
    extra = 1
    raw_id_fields = ('flower',)

@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'budget_category', 'is_recommended')
    list_filter = ('is_recommended', 'budget_category', 'occasions')
    search_fields = ('name', 'description')
    filter_horizontal = ('occasions',)
    inlines = (BouquetFlowerInline,)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'bouquet', 'display_bouquet_price', 'delivery_time', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'delivery_time')
    search_fields = ('client__name', 'client__phone', 'bouquet__name', 'address')
    raw_id_fields = ('client', 'bouquet')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def display_bouquet_price(self, obj):
        if obj.bouquet:
            return f"{obj.bouquet.price} руб."
        return "—"

    display_bouquet_price.short_description = 'Цена букета'
    display_bouquet_price.admin_order_field = 'bouquet__price'