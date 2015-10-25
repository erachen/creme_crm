# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2015  Hybird
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

from django.db.models import DecimalField

# NB: useful to have a specific printer + a specifi form field
class BillingDiscountField(DecimalField):
    def formfield(self, **kwargs):
        from ..forms.fields import BillingDiscountField as FormBillingDiscountField

        defaults = {'form_class': FormBillingDiscountField}
        defaults.update(kwargs)

        return super(BillingDiscountField, self).formfield(**defaults)