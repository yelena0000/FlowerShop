from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse

from flowers.telegram_bot import send_consultation_notification, send_delivery_notification


class Shop(models.Model):
    '''Магазин'''
    title = models.CharField(
        max_length=100,
        verbose_name='Название магазина',
        null=True,
        blank=True
    )
    address = models.CharField(
        max_length=200,
        verbose_name='Адрес магазина',
        null=True,
        blank=True
    )
    phone_number = models.CharField(
        max_length=20,
        verbose_name='Телефон магазина',
        blank=True,
        default=''
    )

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ('title',)

    def __str__(self):
        return self.title


class Occasion(models.Model):
    """Упрощенная модель повода"""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Повод"
        verbose_name_plural = "Поводы"

    def __str__(self):
        return self.name


class Client(models.Model):
    """Объединенная модель клиента"""
    name = models.CharField(max_length=200, verbose_name="Имя")
    phone = models.CharField(max_length=15, verbose_name="Телефон")
    is_consultation = models.BooleanField(default=False, verbose_name="Заявка на консультацию")
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Flower(models.Model):
    """Упрощенная модель цветка"""
    name = models.CharField(max_length=200, unique=True, verbose_name="Название", default="Без названия")

    class Meta:
        verbose_name = 'Цветок'
        verbose_name_plural = 'Цветы'

    def __str__(self):
        return self.name


class Bouquet(models.Model):
    """Оптимизированная модель букета"""
    BUDGET_CHOICES = [
        ('low', 'До 1 000 руб'),
        ('medium', '1 000 - 5 000 руб'),
        ('high', 'От 5 000 руб'),
    ]

    name = models.CharField(max_length=200, verbose_name="Название", default="Без названия")
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(
        verbose_name="Описание",
        blank=True,
        default=''
    )
    price = models.PositiveIntegerField(verbose_name="Цена", default=0)
    photo = models.ImageField(
        upload_to='bouquets/',
        verbose_name="Фото",
        null=True,
        blank=True
    )
    occasions = models.ManyToManyField(
        Occasion,
        verbose_name="Поводы",
        blank=True
    )
    flowers = models.ManyToManyField(
        Flower,
        through='BouquetFlower',
        verbose_name='Цветы в букете',
        blank=True
    )
    budget_category = models.CharField(
        max_length=10,
        choices=BUDGET_CHOICES,
        default='medium',
        verbose_name="Категория бюджета"
    )
    is_recommended = models.BooleanField(default=False, verbose_name="Рекомендуемый")

    def get_absolute_url(self):
        return reverse('card', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = 'Букет'
        verbose_name_plural = 'Букеты'
        ordering = ['name']

    def __str__(self):
        return self.name


class BouquetFlower(models.Model):
    """Количество цветов в букете"""
    bouquet = models.ForeignKey(
        Bouquet,
        on_delete=models.CASCADE,
        default=1,
        verbose_name="Букет"
    )
    flower = models.ForeignKey(
        Flower,
        on_delete=models.CASCADE,
        default=1,
        verbose_name="Цветок"
    )
    amount = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Количество",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Цветок в букете'
        verbose_name_plural = 'Цветы в букетах'

    def __str__(self):
        return f"{self.flower.name} ({self.amount}) в {self.bouquet.name}"


class Order(models.Model):
    """Модель заказа"""
    DELIVERY_TIME_CHOICES = [
        ('ASAP', 'Как можно скорее'),
        ('10-12', 'с 10:00 до 12:00'),
        ('12-14', 'с 12:00 до 14:00'),
        ('14-16', 'с 14:00 до 16:00'),
        ('16-18', 'с 16:00 до 18:00'),
        ('18-20', 'с 18:00 до 20:00'),
    ]

    client = models.ForeignKey(Client, on_delete=models.PROTECT, verbose_name="Клиент")
    bouquet = models.ForeignKey(
        Bouquet,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Букет"
    )
    address = models.TextField(verbose_name="Адрес доставки")
    delivery_time = models.CharField(
        max_length=5,
        choices=DELIVERY_TIME_CHOICES,
        verbose_name="Время доставки",
        blank=True,
        default='ASAP'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_completed = models.BooleanField(default=False, verbose_name="Завершено")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} от {self.client.name}"


@receiver(post_save, sender=Client)
def client_created(sender, instance, created, **kwargs):
    if created and instance.is_consultation:
        send_consultation_notification(instance.id)

@receiver(post_save, sender=Order)
def order_created(sender, instance, created, **kwargs):
    if created:
        send_delivery_notification(instance.id)
