from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=400,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    CASH = 'Наличный'
    CASHLESS = 'Безналичный'
    NEW = 'new'
    COOKING = 'cooking'
    DELIVERY = 'delivery'
    READY = 'ready'
    ORDER_STATUS = [
        (NEW, 'Необработанный'),
        (COOKING, 'Готовится'),
        (DELIVERY, 'Доставка'),
        (READY, 'Доставлен'),
    ]
    PAYMENT_METHOD = [
        (CASH, 'Наличный'),
        (CASHLESS, 'Безналичный')
    ]
    status = models.CharField('Статус заказа', choices=ORDER_STATUS, default=NEW, max_length=20, db_index=True)
    payment = models.CharField('Способ оплаты', choices=PAYMENT_METHOD, default=CASHLESS, max_length=20, db_index=True)
    firstname = models.CharField('Имя', max_length=50)
    lastname = models.CharField('Фамилия', max_length=50, db_index=True)
    phonenumber = PhoneNumberField(verbose_name='Телефон', db_index=True, region='RU')
    address = models.CharField('Адрес доставки', max_length=120)
    totalprice = models.DecimalField('Сумма заказа', max_digits=10, decimal_places=2,
                                     validators=[MinValueValidator(limit_value=0)])
    comment = models.TextField('Комментарии', max_length=128, blank=True)
    registration_date = models.DateTimeField('Дата регистрации', blank=True, db_index=True, auto_now=True)
    call_date = models.DateTimeField('Дата звонка', blank=True, db_index=True, null=True)
    delivery_date = models.DateTimeField('Дата доставки', blank=True, null=True, db_index=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname} {self.phonenumber}'

    def get_total_coast(self):
        if not self.totalprice:
            return sum(item.get_cost() for item in self.items.all())
        else:
            return self.totalprice


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', verbose_name='Заказы', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_products', verbose_name='Продукты', on_delete=models.CASCADE)
    quantity = models.IntegerField('Количество')
    price = models.DecimalField('Сумма', max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(limit_value=0)], null=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        unique_together = ('order', 'product')

    def __str__(self):
        return f'{self.order.phonenumber} - {self.product.name}'

    def get_coast(self):
        if not self.price:
            return self.product.price * self.quantity
        else:
            return self.price
