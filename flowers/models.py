from django.db import models


class Reason(models.Model):
    VOLUME_CHOICES = [
        ('Свадьба'),
        ('Похороны'),
        ('День Рождения'),
    ]

    class Meta:
        verbose_name = "Повод для букета"
        verbose_name_plural = "Поводы для букетов"


class Buyer(models.Model):
    buyer_name = models.CharField(max_length=200, blank=True)
    buyer_phone = models.CharField(max_length=15, blank=True)


    class Meta:
        verbose_name = "Покупатель"
        verbose_name_plural = "Покупатели"


class Delivery(models.Model):
    buyer_name = models.ForeignKey(Buyer, on_delete=models.CASCADE,
        verbose_name='имя покупателя',
        related_name='buyer_name_deliveries')
    
    buyer_phone = models.ForeignKey(Buyer, on_delete=models.CASCADE,
        verbose_name='телефон покупателя',
        related_name='buyer_phone_deliveries', null=True)
    
    address = models.CharField(verbose_name="адрес",
                               max_length=200,
                               blank=True)
    
    delivery_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время доставки")
    
    #flowers = models.ManyToManyField(Flowers)

    is_finished = models.BooleanField(
        default=False,
        verbose_name="Выполнена ли доставка"
    )

    class Meta:
        verbose_name = "Доставка"
        verbose_name_plural = "Доставки"


class Consult(models.Model):
    buyer_name = models.ForeignKey(Buyer, on_delete=models.CASCADE,
        verbose_name='имя покупателя',
        related_name='buyer_name_consults')
    
    buyer_phone = models.ForeignKey(Buyer, on_delete=models.CASCADE,
        verbose_name='телефон покупателя',
        related_name='buyer_phone_consults', null=True)

    consult_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время консультации")
    
    is_finished = models.BooleanField(
        default=False,
        verbose_name="Выполнена ли консультация"
    )

    class Meta:
        verbose_name = "Консультация"
        verbose_name_plural = "Консультации"