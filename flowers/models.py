from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from flowers.telegram_bot import send_consultation_notification


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


class Shop(models.Model):
    '''Магазин'''
    title = models.CharField(max_length=100)
    address = models.CharField(max_length=200,
                               blank=True,
                               null=True,
                               verbose_name='адрес магазина')
    phone_number = models.CharField(max_length=12,
                                    blank=True,
                                    null=True,
                                    verbose_name='номер телефона')
    photo = models.ImageField(blank=True,
                              null=True,
                              verbose_name='Фото')

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ('title',)

    def __str__(self):
        return str(self.title)


class Flower(models.Model):
    '''Цветок'''
    title = models.CharField(max_length=200,
                            blank=True,
                            null=True,
                            verbose_name='Название цветка')

    class Meta:
        verbose_name = 'Цветок'
        verbose_name_plural = 'Цветки'

    def __str__(self):
        return str(self.title)


class Bouquet(models.Model):
    '''Букет'''
    title = models.CharField(max_length=200,
                             blank=True,
                             null=True,
                             verbose_name='Название букета')
    
    slug = models.SlugField("Название в виде url", max_length=200, default='')
    description = models.TextField(blank=True,
                                   null=True,
                                   verbose_name='Описание букета')
    reasons = models.ManyToManyField(Reason,
                                     through='BouquetReason',
                                     blank=True,
                                     verbose_name='Поводы')
    flowers = models.ManyToManyField(Flower,
                                     through="BouquetFlower",
                                     blank=True,
                                     verbose_name='Цветы',)
    price = models.IntegerField(blank=True,
                                null=True,
                                verbose_name='Цена букета')
    photo = models.ImageField(blank=True,
                              null=True,
                              verbose_name='Фото')
    width = models.IntegerField(null=True, verbose_name='Ширина')
    height = models.IntegerField(null=True, verbose_name='Высота')
    
    is_recommended = models.BooleanField('Входит ли в рекомендации', db_index=False, default=False)

    class Meta:
        verbose_name = 'Букет'
        verbose_name_plural = 'Букеты'

    def __str__(self):
        return str(self.title)


class BouquetReason(models.Model):
    '''Букет по поводу'''
    bouquet = models.ForeignKey(Bouquet,
                                on_delete=models.CASCADE,
                                blank=True,
                                null=True)
    reason = models.ForeignKey(Reason,
                               on_delete=models.CASCADE,
                               blank=True,
                               null=True)

    class Meta:
        verbose_name = 'Букет по поводу'
        verbose_name_plural = 'Букет по поводу'

    def __str__(self):
        result = self.bouquet, self.reason
        return str(result)


class BouquetFlower(models.Model):
    '''Букет с цветами'''
    bouquet = models.ForeignKey(Bouquet,
                                on_delete=models.CASCADE,
                                blank=True,
                                null=True,
                                verbose_name='Название букета')
    flower = models.ForeignKey(Flower,
                               on_delete=models.CASCADE,
                               blank=True,
                               null=True)
    amount = models.IntegerField(blank=True,
                                 null=True,
                                 verbose_name='Количество цветов')

    class Meta:
        verbose_name = 'Букет с цветами'
        verbose_name_plural = 'Букеты с цветами'

    def __str__(self):
        result = self.bouquet, self.flower
        return str(result)


class Delivery(models.Model):
    buyer_name = models.CharField(max_length=50,
                                  blank=True,
                                  null=True,
                                  verbose_name="Имя клиента")

    buyer_number = models.CharField(max_length=12,
                                    blank=True,
                                    null=True,
                                    verbose_name="Номер телефона клиента")
    
    address = models.CharField(verbose_name="адрес",
                               max_length=200,
                               blank=True)
    
    delivery_time = models.CharField(max_length=200,
                                     blank=True,
                                     null=True,
                                     verbose_name="Дата и время доставки")
    
    #flowers = models.ManyToManyField(Flowers)

    is_finished = models.BooleanField(
        default=False,
        verbose_name="Выполнена ли доставка"
    )
    # оплачена ли доставка (?)
    class Meta:
        verbose_name = "Доставка"
        verbose_name_plural = "Доставки"


class Consult(models.Model):
    '''Консультация'''
    name = models.CharField(max_length=50,
                                blank=True,
                                null=True,
                                verbose_name="Имя клиента")

    phone_number = models.CharField(max_length=12,
                                    blank=True,
                                    null=True,
                                    verbose_name="Номер телефона клиента")

    is_finished = models.BooleanField(default=False,
                                      blank=True,
                                      null=True,
                                      verbose_name="Выполнена ли консультация")

    consult_time = models.DateTimeField(auto_now_add=True,
                                        blank=True,
                                        null=True,
                                        verbose_name="Дата и время запроса консультации")


    class Meta:
        verbose_name = "Консультация"
        verbose_name_plural = "Консультации"
        
    def __str__(self):
        return str(self.name)
      

@receiver(post_save, sender=Consult)
def consult_created(sender, instance, created, **kwargs):
    if created:
         send_consultation_notification(instance.id)
