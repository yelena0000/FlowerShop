from django.shortcuts import render, redirect
from flowers.models import Buyer, Consult
from django.contrib import messages


def index(request):
    return render(request, 'index.html')

def catalog(request):
    return render(request, 'catalog.html')


def flower_detail(request):
    return render(request, 'card.html')


def quiz(request):
    return render(request, 'quiz.html')


def quiz_step(request):
    return render(request, 'quiz-step.html')


def result(request):
    return render(request, 'result.html')


def order(request, pk=None):
    return render(request, 'order.html')


def order_step(request):
    return render(request, 'order-step.html')


def consultation(request):
    if request.method == 'POST':
        buyer_name = request.POST.get('fname')
        buyer_phone = request.POST.get('tel')

        if not buyer_name or not buyer_phone:
            messages.error(request, 'Пожалуйста, заполните все поля.')
            return render(request, 'consultation.html')

        buyer = Buyer.objects.create(
            buyer_name=buyer_name,
            buyer_phone=buyer_phone
        )
        Consult.objects.create(buyer_name=buyer)
        return redirect('consultation')

    return render(request, 'consultation.html')


def card(request):
    return render(request, 'card.html')
