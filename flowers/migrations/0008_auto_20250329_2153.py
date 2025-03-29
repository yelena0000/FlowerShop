# Generated by Django 3.2.25 on 2025-03-29 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flowers', '0007_bouquet_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='bouquet',
            name='heigt',
            field=models.IntegerField(null=True, verbose_name='Высота'),
        ),
        migrations.AddField(
            model_name='bouquet',
            name='width',
            field=models.IntegerField(null=True, verbose_name='Ширина'),
        ),
        migrations.AlterField(
            model_name='shop',
            name='phone_number',
            field=models.CharField(blank=True, max_length=12, null=True, verbose_name='номер телефона'),
        ),
    ]
