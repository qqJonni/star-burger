import json
from json import JSONDecodeError

import phonenumbers

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from .models import Product, Order, OrderItem


# Создаём заказ
def create_order(order_details):
    order = Order.objects.create(
        phone_number=order_details['phonenumber'],
        first_name=order_details['firstname'],
        last_name=order_details['lastname'],
        address=order_details['address'],
        total_price=0,
    )

    for product_item in order_details['products']:
        product = get_object_or_404(Product, pk=int(product_item['product']))
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=product_item['quantity'],
        )

    price = order.get_total_coast()
    order.total_price = price
    order.save()
    return order


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def check_phonenumber(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number, "RU")
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.NumberParseException:
        return False


def validate_fields(order_details):
    required_fields = ['firstname', 'lastname', 'phonenumber', 'address']
    for field in required_fields:
        if not order_details.get(field):
            return Response({'error': f'Отсутствует обязательное поле "{field}".'}, status=status.HTTP_400_BAD_REQUEST)
        elif not isinstance(order_details[field], str):
            return Response({'error': f'"{field}": Это поле не может быть пустым.'}, status=status.HTTP_400_BAD_REQUEST)

    products = order_details.get('products')
    if not products:
        return Response({'error': 'Поле "products" не может быть пустым'}, status=status.HTTP_400_BAD_REQUEST)
    elif not isinstance(products, list):
        return Response({'error': 'products: Ожидался list со значениями, но был получен "str".'}, status=status.HTTP_400_BAD_REQUEST)
    elif len(products) == 0:
        return Response({'error': 'Список продуктов не может быть пустым'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        for product in products:
            if not isinstance(product, dict):
                return Response({'error': 'Ошибка в списке продуктов'}, status=status.HTTP_400_BAD_REQUEST)
            elif 'product' not in product or 'quantity' not in product:
                return Response({'error': 'Недостаточно данных в списке продуктов.'}, status=status.HTTP_400_BAD_REQUEST)
            elif not Product.objects.filter(id=product['product']).exists():
                return Response({'error': f'products: Недопустимый первичный ключ "{product["product"]}"'}, status=status.HTTP_400_BAD_REQUEST)

    if not check_phonenumber(order_details.get('phonenumber')):
        return Response({'error': 'Введен некорректный номер телефона.'}, status=status.HTTP_400_BAD_REQUEST)

    return None


# Забираем данные заказа/проверяем валидность
@api_view(['POST'])
def register_order(request):
    validation_result = validate_fields(request.data)
    if validation_result:
        return validation_result

    create_order(request.data)
    return Response(request.data)


