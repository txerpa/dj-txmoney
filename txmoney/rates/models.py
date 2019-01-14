# coding=utf-8

from datetime import date

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ..settings import txmoney_settings as settings


class RateSource(models.Model):
    name = models.CharField(max_length=100)
    base_currency = models.CharField(max_length=3, default=settings.DEFAULT_CURRENCY, blank=True)
    last_update = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        unique_together = ('name', 'base_currency')

    def __str__(self):
        return _(f'{self.name} rates in {self.base_currency} update {self.last_update}')

    @cached_property
    def is_updated(self):
        return True if self.last_update.date() == date.today() else False


class RateQuerySet(models.QuerySet):

    def get_for_date(self, currency, currency_date=None):
        """
        Return currency rate for a date or first oldest.

        If not `currency_date` is given today is used.
        """
        currency_date = currency_date or date.today()
        try:
            return self.filter(currency=currency, date__lte=currency_date).order_by('-date')[:1].get()
        except Rate.DoesNotExist:
            raise Rate.DoesNotExist(f'No {currency} rate for {currency_date} or older date')


class Rate(models.Model):
    source = models.ForeignKey(RateSource, on_delete=models.PROTECT, related_name='rates', related_query_name='rate')
    currency = models.CharField(max_length=3)
    value = models.DecimalField(max_digits=14, decimal_places=6)
    date = models.DateField(auto_now_add=True, blank=True, db_index=True)

    objects = RateQuerySet.as_manager()

    class Meta:
        unique_together = ('source', 'currency', 'date')

    def __str__(self):
        return _("%s at %.6f") % (self.currency, self.value)
