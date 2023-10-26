from django.db import transaction
from foodcartapp.models import Order, OrderItem
from rest_framework import serializers


class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    products = OrderProductSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ['products', 'phonenumber', 'firstname', 'lastname', 'address']

    @transaction.atomic
    def create(self, validated_data):
        order = Order.objects.create(
            phonenumber=validated_data['phonenumber'],
            firstname=validated_data['firstname'],
            lastname=validated_data['lastname'],
            address=validated_data['address'],
            status=Order.NEW,
            totalprice=0
        )
        products = validated_data['products']

        items = [OrderItem(
            order=order,
            price=fields['product'].price * fields['quantity'], **fields) for fields in products]
        OrderItem.objects.bulk_create(items)

        order.totalprice = order.get_total_coast()
        order.save()
        return order

