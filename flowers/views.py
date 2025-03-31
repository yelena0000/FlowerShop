from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
import folium
from django.core.paginator import Paginator
import random
import re

from .models import Bouquet, Flower, Occasion, Client, Order, Shop, BouquetFlower

DELIVERY_TIME_CHOICES = [
    ('ASAP', 'Как можно скорее'),
    ('10-12', 'с 10:00 до 12:00'),
    ('12-14', 'с 12:00 до 14:00'),
    ('14-16', 'с 14:00 до 16:00'),
    ('16-18', 'с 16:00 до 18:00'),
    ('18-20', 'с 18:00 до 20:00'),
]
MOSCOW_CENTER = [55.751244, 37.618423]


def is_valid_phone(phone):
    phone = re.sub(r'\D', '', phone)
    return len(phone) == 11 and phone[0] in ['7', '8']


def is_valid_card(card_number):
    card_number = card_number.replace(' ', '')
    return len(card_number) == 16 and card_number.isdigit()


def add_shop(map_obj, lat, lon, address):
    folium.Marker(
        location=[lat, lon],
        popup=address,
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(map_obj)


def serialize_bouquet(bouquet):
    return {
        'id': bouquet.id,
        'name': bouquet.name,
        'slug': bouquet.slug,
        'price': bouquet.price,
        'photo': bouquet.photo.url if bouquet.photo else None,
        'description': bouquet.description,
    }


def serialize_shop(shop):
    return {
        'id': shop.id,
        'address': shop.address,
        'phone_number': shop.phone_number,
    }


def index(request):
    recommended_bouquets = Bouquet.objects.filter(is_recommended=True)[:3]
    shops = Shop.objects.all()
    shops_map = folium.Map(location=MOSCOW_CENTER, zoom_start=12)

    for shop in shops:
        folium.Marker(
            location=[shop.latitude, shop.longitude],
            popup=shop.address,
            icon=folium.Icon(color="green", icon="info-sign")
        ).add_to(shops_map)

    map_html = shops_map._repr_html_()

    context = {
        'recommended_bouquets': [serialize_bouquet(bouquet) for bouquet in recommended_bouquets],
        'shops': [serialize_shop(shop) for shop in shops],
        'map': map_html
    }

    return render(request, 'index.html', context)


def catalog(request):
    bouquets = Bouquet.objects.all().prefetch_related(
        'occasions',
        'bouquetflower_set__flower'
    )

    serialized_bouquets = []
    for bouquet in bouquets:
        flowers_info = [
            {'title': bf.flower.name, 'amount': bf.amount}
            for bf in bouquet.bouquetflower_set.all()
        ]

        serialized_bouquets.append({
            'id': bouquet.id,
            'title': bouquet.name,
            'slug': bouquet.slug,
            'price': bouquet.price,
            'photo': bouquet.photo.url if bouquet.photo else None,
            'description': bouquet.description,
            'budget_category': bouquet.get_budget_category_display(),
            'is_recommended': bouquet.is_recommended,
            'flowers': flowers_info,
            'url': reverse('card', kwargs={'slug': bouquet.slug})
        })

    chunk_bouquets = [
        serialized_bouquets[i:i + 3]
        for i in range(0, len(serialized_bouquets), 3)
    ]

    return render(request, 'catalog.html', {
        'chunk_bouquets': chunk_bouquets,
        'bouquets': serialized_bouquets,
        'budget_categories': Bouquet.BUDGET_CHOICES
    })


def quiz(request):
    occasions = Occasion.objects.all()
    return render(request, 'quiz.html', {'occasions': occasions})


def quiz_step(request):
    if request.method == 'POST':
        if not request.POST.get('occasion'):
            messages.error(request, 'Пожалуйста, выберите повод для букета')
            return redirect('quiz')

        request.session['occasion_id'] = request.POST.get('occasion')
        return render(request, 'quiz-step.html')

    return redirect('quiz')


def result(request):
    if request.method == 'POST':
        occasion_id = request.session.get('occasion_id')
        price_range = request.POST.get('price_range', 'any')

        if not occasion_id:
            messages.error(request, 'Пожалуйста, сначала выберите повод для букета')
            return redirect('quiz')

        request.session['price_range'] = price_range

        bouquets = Bouquet.objects.filter(occasions__id=occasion_id) \
            .prefetch_related('bouquetflower_set__flower', 'occasions')

        if price_range != 'any':
            bouquets = bouquets.filter(budget_category=price_range)

        bouquet = bouquets.order_by('?').first()

        if not bouquet:
            messages.error(request, 'К сожалению, нет подходящих букетов. Попробуйте другие параметры')
            return redirect('quiz')

        request.session['selected_bouquet_id'] = bouquet.id

        flowers_info = [
            {'name': bf.flower.name, 'amount': bf.amount}
            for bf in bouquet.bouquetflower_set.all()
        ]

        shops = Shop.objects.all()
        shops_map = folium.Map(location=MOSCOW_CENTER, zoom_start=12)

        for shop in shops:
            add_shop(shops_map, shop.latitude, shop.longitude, shop.address)

        map_html = shops_map._repr_html_()
        map_html = map_html[:90] + '80' + map_html[92:]

        return render(request, 'result.html', {
            'bouquet': bouquet,
            'flowers': flowers_info,
            'shops': shops,
            'map': map_html
        })

    return redirect('quiz')


def order(request):
    bouquet_slug = request.GET.get('bouquet_slug')
    from_quiz = request.GET.get('from_quiz') == 'true'
    bouquet_id = request.GET.get('bouquet_id')

    if from_quiz and bouquet_id:
        try:
            bouquet = get_object_or_404(Bouquet, id=bouquet_id)
            request.session['selected_bouquet_id'] = bouquet.id
        except (ValueError, Bouquet.DoesNotExist):
            return redirect('catalog')
    elif bouquet_slug:
        try:
            bouquet = get_object_or_404(Bouquet, slug=bouquet_slug)
            request.session['selected_bouquet_id'] = bouquet.id
        except (ValueError, Bouquet.DoesNotExist):
            return redirect('catalog')
    else:
        bouquet_id = request.session.get('selected_bouquet_id')
        if not bouquet_id:
            return redirect('catalog')
        try:
            bouquet = get_object_or_404(Bouquet, id=bouquet_id)
        except (ValueError, Bouquet.DoesNotExist):
            return redirect('catalog')

    if request.method == 'POST':
        fname = request.POST.get('fname', '').strip()
        tel = request.POST.get('tel', '').strip()
        address = request.POST.get('adres', '').strip()

        if not fname or len(fname) < 2:
            messages.error(request, 'Введите корректное имя (минимум 2 символа)')
            return render(request, 'order.html', {
                'bouquet': bouquet,
                'delivery_times': DELIVERY_TIME_CHOICES,
                'form_data': request.POST
            })

        if not is_valid_phone(tel):
            messages.error(
                request,
                'Введите корректный номер телефона (11 цифр, начинается с 7 или 8)'
            )
            return render(request, 'order.html', {
                'bouquet': bouquet,
                'delivery_times': DELIVERY_TIME_CHOICES,
                'form_data': request.POST
            })

        if not address or len(address) < 10:
            messages.error(
                request,
                'Введите корректный адрес (минимум 10 символов)'
            )
            return render(request, 'order.html', {
                'bouquet': bouquet,
                'delivery_times': DELIVERY_TIME_CHOICES,
                'form_data': request.POST
            })

        try:
            client, created = Client.objects.get_or_create(
                phone=tel,
                defaults={'name': fname, 'is_consultation': False}
            )

            if not created:
                client.name = fname
                client.save()

            Order.objects.create(
                client=client,
                bouquet=bouquet,
                address=address,
                delivery_time=request.POST.get('orderTime', 'ASAP')
            )

            return redirect('order_step')

        except Exception as e:
            messages.error(
                request,
                f'Ошибка при оформлении заказа: {str(e)}'
            )
            return render(request, 'order.html', {
                'bouquet': bouquet,
                'delivery_times': DELIVERY_TIME_CHOICES,
                'form_data': request.POST
            })

    return render(request, 'order.html', {
        'bouquet': bouquet,
        'delivery_times': DELIVERY_TIME_CHOICES
    })


def order_step(request):
    if 'selected_bouquet_id' not in request.session:
        return redirect('order')

    if request.method == 'POST':
        card_number = request.POST.get('card_number', '').replace(' ', '')

        if not is_valid_card(card_number):
            messages.error(
                request,
                'Введите корректный номер карты (16 цифр)'
            )
            return render(request, 'order-step.html')

        if 'selected_bouquet_id' in request.session:
            del request.session['selected_bouquet_id']
        if 'occasion_id' in request.session:
            del request.session['occasion_id']

        return render(request, 'success_order.html')

    return render(request, 'order-step.html')



def consultation(request):
    if request.method == 'POST':
        fname = request.POST.get('fname', '').strip()
        tel = request.POST.get('tel', '').strip()

        if not fname or len(fname) < 2:
            messages.error(
                request,
                'Введите корректное имя (минимум 2 символа)'
            )
            return render(
                request,
                'consultation.html', {
                'form_data': {'fname': fname, 'tel': tel}
            })

        if not is_valid_phone(tel):
            messages.error(
                request,
                'Введите корректный номер телефона (11 цифр, начинается с 7 или 8)'
            )
            return render(
                request, 'consultation.html', {
                'form_data': {'fname': fname, 'tel': tel}
            })

        try:
            client, created = Client.objects.get_or_create(
                phone=tel,
                defaults={'name': fname, 'is_consultation': True}
            )

            if not created:
                client.name = fname
                client.is_consultation = True

            occasion_id = request.session.get('occasion_id')
            price_range = request.session.get('price_range')

            if occasion_id and price_range:
                try:
                    occasion = Occasion.objects.get(id=occasion_id)
                    client.quiz_occasion = occasion
                    client.quiz_price_range = price_range

                    if 'occasion_id' in request.session:
                        del request.session['occasion_id']
                    if 'price_range' in request.session:
                        del request.session['price_range']
                except Occasion.DoesNotExist:
                    pass

            client.save()

            try:
                from .telegram_bot import send_consultation_notification
                send_consultation_notification(client.id)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка отправки уведомления в Telegram: {str(e)}")

            return redirect('success_consult')

        except Exception as e:
            messages.error(request, f'Произошла ошибка: {str(e)}')
            return render(request, 'consultation.html', {
                'form_data': {'fname': fname, 'tel': tel}
            })

    from_quiz = request.GET.get('from_quiz') == 'true'
    if from_quiz:
        request.session['from_quiz'] = True

    return render(request, 'consultation.html')


def card(request, slug):
    bouquet = get_object_or_404(Bouquet, slug=slug)
    bouquet_flowers = BouquetFlower.objects.filter(bouquet=bouquet).select_related('flower')

    serialized_flowers = []
    for bouquet_flower in bouquet_flowers:
        serialized_flowers.append({
            'title': bouquet_flower.flower.name,
            'amount': bouquet_flower.amount,
        })

    context = {
        'bouquet': {
            'title': bouquet.name,
            'price': bouquet.price,
            'photo': bouquet.photo.url if bouquet.photo and hasattr(bouquet.photo, 'url') else None,
            'flowers': serialized_flowers,
            'description': bouquet.description,
            'slug': bouquet.slug
        }
    }
    return render(request, 'card.html', context)


def success_consult(request):
    return render(request, 'success_consult.html')


def success_order(request):
    return render(request, 'success_order.html')
