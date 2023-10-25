from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import transaction
from phonenumber_field.validators import validate_international_phonenumber
from rest_framework import serializers

from foodcartapp.models import Order, OrderItem


class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    products = OrderProductSerializer(many=True, allow_empty=False, write_only=True)
    phonenumber = serializers.CharField(validators=[RegexValidator(r'^\+\d{11}$')])

    class Meta:
        model = Order
        fields = ['products', 'phonenumber', 'firstname', 'lastname', 'address']

    def validate_phonenumber(self, phone_number):
        if not phone_number:
            raise ValidationError('Это поле обязательно')
        try:
            validate_international_phonenumber(phone_number)
        except ValidationError:
            raise serializers.ValidationError('Введен некорректный номер телефона.')
        return phone_number

    @transaction.atomic
    def create(self, validated_data):
        order = Order.objects.create(
            phone_number=validated_data['phonenumber'],
            firstname=validated_data['firstname'],
            lastname=validated_data['lastname'],
            address=validated_data['address'],
            comment=validated_data['comment'],
            total_price=0
        )
        products = validated_data['products']

        items = [OrderItem(
            order=order,
            price=fields['product'].price * fields['quantity'], **fields) for fields in products]
        OrderItem.objects.bulk_create(items)

        order.totalprice = order.get_total_coast()
        order.save()
        return order

