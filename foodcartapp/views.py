import json
from json import JSONDecodeError

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


# Забираем данные заказа/проверяем валидность
@api_view(['POST'])
def register_order(request):
    try:
        order_details = json.loads(request.body)

        if not isinstance(order_details.get('firstname'), str):
            return Response({'error': 'Ошибка в поле "firstname"'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(order_details.get('lastname'), str):
            return Response({'error': 'Ошибка в поле "lastname"'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(order_details.get('phonenumber'), str):
            return Response({'error': 'Ошибка в поле "phonenumber"'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(order_details.get('address'), str):
            return Response({'error': 'Ошибка в поле "address"'}, status=status.HTTP_400_BAD_REQUEST)

        products = order_details.get('products')
        if products is None:
            return Response({'error': 'Поле "products" не может быть пустым'}, status=status.HTTP_400_BAD_REQUEST)
        elif not isinstance(products, list):
            return Response({'products: Ожидался list со значениями, но был получен "str".'}, status=status.HTTP_400_BAD_REQUEST)
        elif len(products) == 0:
            return Response({'error': 'Список продуктов не может быть пустым'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            for product in products:
                if not (product, dict):
                    return Response({'error': 'Ошибка в списке продуктов'}, status=status.HTTP_400_BAD_REQUEST)

        create_order(order_details)
        return Response(order_details)
    except JSONDecodeError:
        return Response({'error': 'Ошибка при декодировании JSON'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

