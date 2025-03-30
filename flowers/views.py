from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
import folium
from django.core.paginator import Paginator
import random

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


def add_shop(map_obj, lat, lon, address):
    folium.Marker(
        location=[lat, lon],
        popup=address,
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(map_obj)


def serialize_bouquet(bouquet):
    photo_url = bouquet.photo.url if bouquet.photo and hasattr(bouquet.photo, 'url') else None
    return {
        "title": bouquet.name,
        "price": bouquet.price,
        "photo": photo_url,
        'slug': bouquet.slug
    }


def serialize_shop(shop):
    return {
        'title': shop.title,
        'address': shop.address,
        'phone_number': shop.phone_number
    }


def index(request):
    recommended_bouquets = Bouquet.objects.filter(is_recommended=True)[:3]
    shops = Shop.objects.all()
    context = {
        'recommended_bouquets': [serialize_bouquet(bouquet) for bouquet in recommended_bouquets],
        'shops': [serialize_shop(shop) for shop in shops]
    }
    return render(request, 'index.html', context)


def catalog(request):
    # Получаем все букеты с оптимизацией запросов
    bouquets = Bouquet.objects.all().prefetch_related(
        'occasions',
        'bouquetflower_set__flower'
    )

    # Сериализация букетов
    serialized_bouquets = []
    for bouquet in bouquets:
        # Получаем состав букета
        flowers_info = [
            {
                'title': bf.flower.name,
                'amount': bf.amount
            }
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

    # Разбиваем на группы по 3 букета
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
        request.session['occasion_id'] = request.POST.get('occasion')
        return render(request, 'quiz-step.html')

    return redirect('quiz')


def result(request):
    if request.method == 'POST':
        occasion_id = request.session.get('occasion_id')
        price_range = request.POST.get('price_range', 'any')

        bouquets = Bouquet.objects.filter(occasions__id=occasion_id) \
            .prefetch_related(
            'bouquetflower_set__flower',
            'occasions'
        )

        if price_range != 'any':
            bouquets = bouquets.filter(budget_category=price_range)

        bouquet = bouquets.order_by('?').first()

        if not bouquet:
            return redirect('quiz')

        request.session['selected_bouquet_id'] = bouquet.id

        flowers_info = [
            {
                'name': bf.flower.name,
                'amount': bf.amount
            }
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
        # Если после квиза
        try:
            bouquet = get_object_or_404(Bouquet, id=bouquet_id)
            request.session['selected_bouquet_id'] = bouquet.id
        except (ValueError, Bouquet.DoesNotExist):
            return redirect('catalog')
    elif bouquet_slug:
        # Если с карточки товара
        try:
            bouquet = get_object_or_404(Bouquet, slug=bouquet_slug)
            request.session['selected_bouquet_id'] = bouquet.id
        except (ValueError, Bouquet.DoesNotExist):
            return redirect('catalog')
    else:
        # Если нет параметров - проверяем сессию
        bouquet_id = request.session.get('selected_bouquet_id')
        if not bouquet_id:
            return redirect('catalog')
        try:
            bouquet = get_object_or_404(Bouquet, id=bouquet_id)
        except (ValueError, Bouquet.DoesNotExist):
            return redirect('catalog')

    if request.method == 'POST':
        try:
            required_fields = ['tel', 'fname', 'adres']
            if not all(request.POST.get(field) for field in required_fields):
                return render(request, 'order.html', {
                    'bouquet': bouquet,
                    'delivery_times': DELIVERY_TIME_CHOICES,
                    'form_data': request.POST
                })

            client, created = Client.objects.get_or_create(
                phone=request.POST['tel'],
                defaults={
                    'name': request.POST['fname'],
                    'is_consultation': False
                }
            )

            if not created:
                client.name = request.POST['fname']
                client.save()

            Order.objects.create(
                client=client,
                bouquet=bouquet,
                address=request.POST['adres'],
                delivery_time=request.POST.get('orderTime', 'ASAP')
            )

            return redirect('order_step')

        except Exception as e:
            messages.error(request, f'Ошибка при оформлении заказа: {str(e)}')
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
    if request.method == 'POST':
        try:
            card_number = request.POST.get('card_number', '').replace(' ', '')
            if len(card_number) != 16 or not card_number.isdigit():
                return redirect('order_step')

            if 'selected_bouquet_id' in request.session:
                del request.session['selected_bouquet_id']
            if 'occasion_id' in request.session:
                del request.session['occasion_id']

            return render(request, 'success_order.html')

        except Exception as e:
            return redirect('order_step')

    if 'selected_bouquet_id' not in request.session:
        return redirect('order')

    return render(request, 'order-step.html')


def consultation(request):
    if request.method == 'POST':
        if not all([request.POST.get('tel'), request.POST.get('fname')]):
            return render(request, 'consultation.html')

        try:
            Client.objects.create(
                name=request.POST['fname'],
                phone=request.POST['tel'],
                is_consultation=True
            )
            return redirect('success_consult')
        except Exception as e:
            return render(request, 'consultation.html')

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
    if request.method == 'POST':
        if not all([request.POST.get('tel'), request.POST.get('fname')]):
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
            return render(request, 'consultation.html')

        try:
            Client.objects.create(
                name=request.POST['fname'],
                phone=request.POST['tel'],
                is_consultation=True
            )
            return redirect('success_consult')
        except Exception as e:
            return render(request, 'consultation.html')

    return render(request, 'success_consult.html')

def success_order(request):
    return render(request, 'success_order.html')
