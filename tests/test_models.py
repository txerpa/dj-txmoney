# coding=utf-8

import pytest
from django import VERSION
from django.core.exceptions import ValidationError
from django.db.models import Case, F, Func, Model, Q, Value, When

from tests.testapp.models import (
    AbstractMoneyModel, InheritedMoneyModel, InheritorMoneyModel,
    ModelRelatedToModelWithMoney, ModelWithCustomManager,
    ModelWithDefaultAsDecimal, ModelWithDefaultAsFloat, ModelWithDefaultAsInt,
    ModelWithDefaultAsMoney, ModelWithDefaultAsString,
    ModelWithDefaultAsStringWithCurrency, ModelWithTwoMoneyFields,
    NullMoneyFieldModel, ProxyMoneyModel, SimpleMoneyModel
)
from txmoney.money.exceptions import NotSupportedLookup
from txmoney.money.models.fields import MoneyField
from txmoney.money.models.money import Money

pytestmark = pytest.mark.django_db


class TestMoneyField(object):
    @pytest.mark.parametrize(
        'value',
        (
            (1, 'USD', 'extra_string'),
            (1, None),
            (1,),
        )
    )
    def test_create_with_invalid_values(self, value):
        with pytest.raises(ValidationError):
            SimpleMoneyModel.objects.create(amount=value)

    @pytest.mark.parametrize(
        'model_class, kwargs, expected',
        (
            (NullMoneyFieldModel, {}, None),
            (SimpleMoneyModel, {'amount': Money('100.0')}, Money('100.0')),
            (SimpleMoneyModel, {}, Money(0, 'EUR')),
            (SimpleMoneyModel, {'amount': '111.2'}, Money('111.2', 'EUR')),
            (SimpleMoneyModel, {'amount': Money('123', 'PLN')}, Money('123', 'PLN')),
            (SimpleMoneyModel, {'amount': ('123', 'PLN')}, Money('123', 'PLN')),
            (SimpleMoneyModel, {'amount': (123.0, 'PLN')}, Money('123', 'PLN')),
            (ModelWithDefaultAsMoney, {}, Money('0.01', 'RUB')),
            (ModelWithDefaultAsFloat, {}, Money('12.05', 'PLN')),
            (ModelWithDefaultAsStringWithCurrency, {}, Money('123', 'EUR')),
            (ModelWithDefaultAsString, {}, Money('123', 'PLN')),
            (ModelWithDefaultAsInt, {}, Money('123', 'GHS')),
            (ModelWithDefaultAsDecimal, {}, Money('0.01', 'CHF')),
        )
    )
    def test_create_defaults(self, model_class, kwargs, expected):
        instance = model_class.objects.create(**kwargs)
        assert instance.amount == expected

        retrieved = model_class.objects.get(pk=instance.pk)
        assert retrieved.amount == expected

    def test_save_new_value(self):
        instance = SimpleMoneyModel.objects.create(amount=Money('100.0'))

        # Try setting the value directly
        setattr(instance, 'amount', Money(1, 'GBP'))
        instance.save()
        instance.refresh_from_db()

        assert getattr(instance, 'amount') == Money(1, 'GBP')

    def test_not_supported_lookup(self):
        with pytest.raises(NotSupportedLookup) as exc:
            SimpleMoneyModel.objects.filter(amount__regex='\d+').count()
        assert str(exc.value) == 'Lookup "regex" is not supported for MoneyField'

    @pytest.fixture
    def objects_setup(self):
        ModelWithTwoMoneyFields.objects.bulk_create((
            ModelWithTwoMoneyFields(amount1=Money(1, 'EUR'), amount2=Money(2, 'EUR')),
            ModelWithTwoMoneyFields(amount1=Money(2, 'EUR'), amount2=Money(0, 'EUR')),
            ModelWithTwoMoneyFields(amount1=Money(3, 'EUR'), amount2=Money(0, 'EUR')),
            ModelWithTwoMoneyFields(amount1=Money(4, 'EUR'), amount2=Money(0, 'GHS')),
            ModelWithTwoMoneyFields(amount1=Money(5, 'EUR'), amount2=Money(5, 'EUR')),
            ModelWithTwoMoneyFields(amount1=Money(5, 'USD'), amount2=Money(5, 'EUR')),
        ))

    @pytest.mark.parametrize(
        'filters, expected_count',
        (
            (Q(amount1=F('amount2')), 1),
            (Q(amount1__gt=F('amount2')), 2),
            (Q(amount1__in=(Money(1, 'EUR'), Money(5, 'USD'))), 2),
            (Q(id__in=(-1, -2)), 0),
            (Q(amount1=Money(1, 'EUR')) | Q(amount2=Money(0, 'EUR')), 3),
            (Q(amount1=Money(1, 'EUR')) | Q(amount1=Money(4, 'EUR')) | Q(amount2=Money(0, 'GHS')), 2),
            (Q(amount1=Money(1, 'EUR')) | Q(amount1=Money(5, 'EUR')) | Q(amount2=Money(0, 'GHS')), 3),
            (Q(amount1=Money(1, 'EUR')) | Q(amount1=Money(4, 'EUR'), amount2=Money(0, 'GHS')), 2),
            (Q(amount1=Money(1, 'EUR')) | Q(amount1__gt=Money(4, 'EUR'), amount2=Money(0, 'GHS')), 1),
            (Q(amount1=Money(1, 'EUR')) | Q(amount1__gte=Money(4, 'EUR'), amount2=Money(0, 'GHS')), 2),
        )
    )
    @pytest.mark.usefixtures('objects_setup')
    def test_comparison_lookup(self, filters, expected_count):
        assert ModelWithTwoMoneyFields.objects.filter(filters).count() == expected_count

    @pytest.mark.usefixtures('objects_setup')
    def test_in_lookup(self):
        assert ModelWithTwoMoneyFields.objects.filter(amount1__in=(Money(1, 'EUR'), Money(5, 'USD'))).count() == 2
        assert ModelWithTwoMoneyFields.objects.filter(
            Q(amount1__lte=Money(2, 'EUR')), amount1__in=(Money(1, 'EUR'), Money(3, 'EUR'))
        ).count() == 1
        assert ModelWithTwoMoneyFields.objects.exclude(amount1__in=(Money(1, 'EUR'), Money(5, 'USD'))).count() == 4

    def test_isnull_lookup(self):
        NullMoneyFieldModel.objects.create(amount=None)
        NullMoneyFieldModel.objects.create(amount=Money(100, 'USD'))

        queryset = NullMoneyFieldModel.objects.filter(amount=None)

        assert queryset.count() == 1

    def test_rounding(self):
        instance = SimpleMoneyModel.objects.create(amount=Money('100.0623456781123219'))
        instance.refresh_from_db()
        assert instance.amount == Money('100.06')

    def test_exact_match(self):
        money = Money('100.0')

        instance = SimpleMoneyModel.objects.create(amount=money)
        retrieved = SimpleMoneyModel.objects.get(amount=money)

        assert instance.pk == retrieved.pk

    def test_range_search(self):
        money = Money('3')

        instance = SimpleMoneyModel.objects.create(amount=Money('100.0'))
        retrieved = SimpleMoneyModel.objects.get(amount__gt=money)

        assert instance.pk == retrieved.pk
        assert SimpleMoneyModel.objects.filter(amount__lt=money).count() == 0

    # @pytest.mark.parametrize('model_class', (SimpleMoneyModel, ModelWithChoicesMoneyField))
    @pytest.mark.parametrize('model_class', (SimpleMoneyModel,))
    def test_currency_querying(self, model_class):
        model_class.objects.create(amount=Money('100.0', 'GBP'))

        assert model_class.objects.filter(amount__lt=Money('1000', 'USD')).count() == 0
        assert model_class.objects.filter(amount__lt=Money('1000', 'GBP')).count() == 1


class TestGetOrCreate(object):

    @pytest.mark.parametrize(
        'kwargs, currency',
        (
            ({'amount_currency': 'PLN'}, 'PLN'),
            ({'amount': Money(0, 'EUR')}, 'EUR')
        )
    )
    def test_get_or_create_respects_currency(self, kwargs, currency):
        instance, created = SimpleMoneyModel.objects.get_or_create(**kwargs)
        assert str(instance.amount.currency) == currency, 'currency should be taken into account in get_or_create'

    def test_defaults(self):
        money = Money(10, 'GBP')
        instance, _ = SimpleMoneyModel.objects.get_or_create(defaults={'amount': money})
        assert instance.amount == money


class TestFExpressions(object):
    parametrize_f_objects = pytest.mark.parametrize(
        'f_obj, expected',
        (
            (F('amount') + Money(100, 'USD'), Money(200, 'USD')),
            (F('amount') - Money(100, 'USD'), Money(0, 'USD')),
            (F('amount') * 2, Money(200, 'USD')),
            (F('amount') * 2, Money(200, 'USD')),
            (F('amount') / 2, Money(50, 'USD')),
            (F('amount') % 98, Money(2, 'USD')),
            (F('amount') / 2, Money(50, 'USD')),
            (F('amount') + F('amount'), Money(200, 'USD')),
            (F('amount') - F('amount'), Money(0, 'USD')),
        )
    )

    @parametrize_f_objects
    def test_save(self, f_obj, expected):
        instance = SimpleMoneyModel.objects.create(amount=Money(100, 'USD'))
        instance.amount = f_obj
        instance.save()
        instance.refresh_from_db()
        assert instance.amount == expected

    @parametrize_f_objects
    def test_f_update(self, f_obj, expected):
        instance = SimpleMoneyModel.objects.create(amount=Money(100, 'USD'))
        SimpleMoneyModel.objects.update(amount=f_obj)
        instance.refresh_from_db()
        assert instance.amount == expected

    @pytest.mark.parametrize(
        'create_kwargs, filter_value, in_result',
        (
            (
                {'amount1': Money(100, 'USD'), 'amount2': Money(100, 'USD')},
                {'amount1': F('amount1')},
                True
            ),
            (
                {'amount1': Money(100, 'USD'), 'amount2': Money(100, 'USD')},
                {'amount1': F('amount2')},
                True
            ),
            (
                {'amount1': Money(100, 'USD'), 'amount2': Money(100, 'EUR')},
                {'amount1': F('amount2')},
                False
            ),
            (
                {'amount1': Money(50, 'USD'), 'amount2': Money(100, 'USD')},
                {'amount2': F('amount1') * 2},
                True
            ),
            (
                {'amount1': Money(50, 'USD'), 'amount2': Money(100, 'USD')},
                {'amount2': F('amount1') + Money(50, 'USD')},
                True
            ),
            (
                {'amount1': Money(50, 'USD'), 'amount2': Money(100, 'EUR')},
                {'amount2': F('amount1') * 2},
                False
            ),
            (
                {'amount1': Money(50, 'USD'), 'amount2': Money(100, 'EUR')},
                {'amount2': F('amount1') + Money(50, 'USD')},
                False
            ),
        )
    )
    def test_filtration(self, create_kwargs, filter_value, in_result):
        instance = ModelWithTwoMoneyFields.objects.create(**create_kwargs)
        assert (instance in ModelWithTwoMoneyFields.objects.filter(**filter_value)) is in_result

    def test_update_fields_save(self):
        instance = SimpleMoneyModel.objects.create(amount=Money(100, 'USD'))
        instance.amount = F('amount') + Money(100, 'USD')
        instance.save(update_fields=['amount'])
        instance = SimpleMoneyModel.objects.get(pk=instance.pk)
        assert instance.amount == Money(200, 'USD')


class TestExpressions(object):

    def test_conditional_update(self):
        SimpleMoneyModel.objects.bulk_create((
            SimpleMoneyModel(amount=Money(1)),
            SimpleMoneyModel(amount=Money(2)),
        ))
        SimpleMoneyModel.objects.update(amount=Case(
            When(amount=1, then=Value(10)),
            default=Value(0)
        ))
        assert SimpleMoneyModel.objects.all()[:1].get().amount == Money(10, 'EUR')
        assert SimpleMoneyModel.objects.all()[1:2].get().amount == Money(0, 'EUR')

    @pytest.mark.skipif(VERSION < (1, 9), reason='Only Django 1.9+ supports this')
    def test_create_func(self):
        instance = SimpleMoneyModel.objects.create(amount=Func(Value(-10), function='ABS'))
        instance.refresh_from_db()
        assert instance.amount.amount == 10

    @pytest.mark.parametrize(
        'value, expected', (
            (None, None),
            (10, Money(10, 'EUR')),
            (Money(10, 'USD'), Money(10, 'USD')),
        )
    )
    def test_value_create(self, value, expected):
        instance = NullMoneyFieldModel.objects.create(amount=Value(value))
        instance.refresh_from_db()
        assert instance.amount == expected

    def test_value_create_invalid(self):
        with pytest.raises(ValidationError):
            SimpleMoneyModel.objects.create(amount=Value('string'))


def test_find_models_related_to_money_models():
    money_model = SimpleMoneyModel.objects.create(amount=Money('100.0', 'USD'))
    ModelRelatedToModelWithMoney.objects.create(money_model=money_model)

    ModelRelatedToModelWithMoney.objects.get(money_model__amount=Money('100.0', 'USD'))
    ModelRelatedToModelWithMoney.objects.get(money_model__amount__lt=Money('1000.0', 'USD'))


@pytest.mark.parametrize('model_class', (InheritedMoneyModel, InheritorMoneyModel))
class TestInheritance(object):
    """Test inheritance from a concrete and an abstract models"""

    def test_model(self, model_class):
        assert model_class.objects.model == model_class

    def test_fields(self, model_class):
        first_value = Money('100.0', 'GBP')
        second_value = Money('200.0', 'USD')
        instance = model_class.objects.create(amount=first_value, amount2=second_value)
        assert instance.amount == first_value
        assert instance.amount2 == second_value


class TestManager(object):
    def test_manager(self):
        assert hasattr(SimpleMoneyModel, 'objects')

    def test_objects_creation(self):
        SimpleMoneyModel.objects.create(amount=Money('100.0', 'USD'))
        assert SimpleMoneyModel.objects.count() == 1


class TestProxyModel(object):

    def test_instances(self):
        ProxyMoneyModel.objects.create(amount=Money('100.0', 'USD'))
        assert isinstance(ProxyMoneyModel.objects.all()[:1].get(), ProxyMoneyModel)

    def test_patching(self):
        ProxyMoneyModel.objects.create(amount=Money('100.0', 'USD'))
        # This will fail if ProxyMoneyModel.objects doesn't have the patched manager
        assert ProxyMoneyModel.objects.filter(amount__gt=Money('50.00', 'GBP')).count() == 0


INSTANCE_ACCESS_MODELS = [SimpleMoneyModel, InheritorMoneyModel, InheritedMoneyModel, ProxyMoneyModel]

if VERSION[:2] < (3, 2):
    # Django 3.2 and later does not support AbstractModel instancing
    INSTANCE_ACCESS_MODELS.append(AbstractMoneyModel)


@pytest.mark.parametrize('model_class', INSTANCE_ACCESS_MODELS)
def test_manager_instance_access(model_class):
    with pytest.raises(AttributeError):
        model_class().objects.all()


@pytest.mark.skipif(VERSION >= (1, 10), reason='Django >= 1.10 dropped `get_field_by_name` method of `Options`.')
def test_get_field_by_name():
    assert SimpleMoneyModel._meta.get_field_by_name('amount')[0].__class__.__name__ == 'MoneyField'
    assert SimpleMoneyModel._meta.get_field_by_name('amount_currency')[0].__class__.__name__ == 'CurrencyField'


def test_different_hashes():
    money = SimpleMoneyModel._meta.get_field('amount')
    money_currency = SimpleMoneyModel._meta.get_field('amount_currency')
    assert hash(money) != hash(money_currency)


class TestFieldAttributes(object):
    def create_class(self, **field_kwargs):
        class TestModel(Model):
            field = MoneyField(**field_kwargs)

            class Meta:
                app_label = 'test'

        return TestModel

    @pytest.mark.parametrize('field_kwargs, message', (
        ({'default': {}}, 'Default value must be an instance of Money, is: {}'),
    ))
    def test_missing_attributes(self, field_kwargs, message):
        with pytest.raises(ValueError) as exc:
            self.create_class(**field_kwargs)
        assert str(exc.value) == message

    def test_default_currency(self):
        klass = self.create_class(default_currency=None, default=Money(10, 'EUR'), max_digits=10, decimal_places=2)
        assert str(klass._meta.fields[2].default_currency) == 'EUR'
        instance = klass()
        assert instance.field == Money(10, 'EUR')


class TestCustomManager(object):
    def test_method(self):
        assert ModelWithCustomManager.manager.super_method().count() == 0
