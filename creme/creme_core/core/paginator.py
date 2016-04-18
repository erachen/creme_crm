# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2016  Hybird
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

import collections
from datetime import date, datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.paginator import InvalidPage
from django.db.models import Q
from django.utils.lru_cache import lru_cache

from creme.creme_core.utils.dates import DATE_ISO8601_FMT, DATETIME_ISO8601_FMT
from creme.creme_core.utils.meta import FieldInfo


_FORWARD = 'forward'
_BACKWARD = 'backward'


class FirstPage(InvalidPage):
    pass


class LastPage(InvalidPage):
    pass


class FlowPaginator(object):
    """Paginates a Queryset on CremeEntities.

    It should be fast on big data bases, because it avoids SQL's OFFSET most of the time,
    because we use a KEYSET way (ex: the page is the X first items with name >= "foobar").
    Disadvantage is that you can only go to the next & previous pages.

    Beware: if you use a nullable key, NULL values must be ordered as the lowest values
            (ie: first in ASC order, last in DESC order).
            Tip: you can use creme.models.manager.LowNullsQuerySet.
    """
    def __init__(self, queryset, key, per_page, count):
        """Constructor.
        @param queryset: QuerySet instance. Beware: lines must have always the same order when
                         sub-set queries are performed, or the paginated content won't be consistent.
                         Tip: use the 'PK' as the (last) ordering field.
        @param key: Name of the field used as key (ie: first ordering field). It can be a composed
                    field name like 'user__username'. ManyToManyFields are not managed ; ForeignKeys
                    must reference models with a Meta option 'ordering'.
        @param per_page: Number of entities.
        @param count: Total number of entities (ie should be equal to object_list.count())
                      (so no additional query is performed to get it).
        @raise ValueError: If key is invalid.
        """
        assert per_page > 1

        self.queryset = queryset
        self.per_page = per_page
        self.count = count

        self._attr_name = ''
        self._reverse_order = False
        self._key_field_info = None
        self.key = key

    @property
    def attr_name(self):
        return self._attr_name

    @property
    def reverse_order(self):
        return self._reverse_order

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value):
        self._count = int(value)

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

        if value.startswith('-'):
            attr_name = value[1:]
            self._reverse_order = True
        else:
            attr_name = value
            self._reverse_order = False

        field_info = FieldInfo(self.queryset.model, attr_name)

        if any(f.many_to_many for f in field_info):
            raise ValueError('Invalid key: ManyToManyFields cannot be used as key.')

        # TODO: if related_model is not None ?
        last_field = field_info[-1]

        if last_field.is_relation:
            subfield_model = last_field.rel.to
            subfield_ordering = subfield_model._meta.ordering

            if not subfield_ordering:
                raise ValueError('Invalid key: related field model "%s" should '
                                 'have Meta.ordering' % subfield_model
                                )

            attr_name += '__' + subfield_ordering[0]
            field_info = FieldInfo(self.queryset.model, attr_name)

        self._attr_name = attr_name
        self._key_field_info = field_info

    def last_page(self):
        return self.page({'type': 'last', 'key': self.key})

    @property
    def per_page(self):
        return self._per_page

    @per_page.setter
    def per_page(self, value):
        self._per_page = int(value)

    def _check_key_info(self, page_info):
        try:
            info_key = page_info['key']
        except KeyError:
            raise InvalidPage('Missing "key".')
        else:
            if info_key != self.key:
                raise InvalidPage('Invalid "key" (different from paginator key).')

    @staticmethod
    def _offset_from_info(page_info):
        try:
            offset = int(page_info.get('offset', 0))
        except ValueError:
            raise InvalidPage('Invalid "offset" (not integer).')

        if offset < 0:
            raise InvalidPage('Invalid "offset" (negative) .')

        return offset

    def _get_qs(self, page_info, reverse):
        value = page_info['value']
        attr_name = self._attr_name

        if value is None:
            q = Q(**{attr_name + '__isnull': True}) if reverse else Q()
        else:
            op = '__lte' if reverse else '__gte'
            q = Q(**{attr_name + op: value})

            if reverse and any(f.null for f in self._key_field_info):
                q |= Q(**{attr_name + '__isnull': True})

        try:
            qs = self.queryset.filter(q)
        except (ValueError, ValidationError) as e:
            raise InvalidPage('Invalid "value" [%s].' % e)

        return qs

    def page(self, page_info=None):
        """Get the wanted page.
        @param page_info: A dictionary returned by the methods
                          info()/next_page_info()/previous_page_info() of a page,
                          or None (which means 'first page').
        @return An instance of FlowPage.

        @raise FirstPage: the first page has been reached when going backward (the page could be not complete).
        @raise LastPage: it seems that the last page has been exceeded (this page is empty).
        @raise InvalidPage: page_info is invalid.

        @see FlowPage.info()
        """
        if page_info is None:
            page_info = {'type': 'first'}

        per_page = self._per_page
        offset = 0
        forward = True
        first_page = False
        move_type = page_info.get('type')

        if move_type == 'first' or self.count <= per_page:
            entities = list(self.queryset[:per_page + 1])
            next_item = None if len(entities) <= per_page else entities.pop()
            first_page = True
        elif move_type == 'last':
            self._check_key_info(page_info)

            entities = reversed(self.queryset.reverse()[:per_page])
            next_item = None
            forward = False
        else:
            self._check_key_info(page_info)

            offset = self._offset_from_info(page_info)

            if move_type == _FORWARD:
                qs = self._get_qs(page_info, reverse=self._reverse_order)
                entities = list(qs[offset:offset + per_page + 1])
                next_item = None if len(entities) <= per_page else entities.pop()

                if not entities:
                    raise LastPage()
            elif move_type == _BACKWARD:
                qs = self._get_qs(page_info, reverse=not self._reverse_order)

                # NB: we get 2 additional items:
                #  - 1 will be the next_item of the page.
                #  - if the second one exists, it indicates that there is at least one item before the page.
                #    (so it is not the first one).
                size = per_page + 2
                entities = list(qs.reverse()[offset:offset + size])

                if len(entities) != size:
                    raise FirstPage()

                entities.pop()
                entities.reverse()
                next_item = entities.pop()

                if self._key_field_info.value_from(entities[-1]) != page_info['value']:
                    offset = 0

                forward = False
            else:
                raise InvalidPage('Invalid or missing "type".')

        return FlowPage(object_list=entities, paginator=self, forward=forward,
                        key=self._key, key_field_info=self._key_field_info, attr_name=self._attr_name,
                        offset=offset, max_size=per_page,
                        next_item=next_item, first_page=first_page,
                       )

    def pages(self):
        page = self.page()

        while True:
            yield page

            if not page.has_next():
                break

            try:
                page = self.page(page.next_page_info())
            except LastPage:
                break


class FlowPage(collections.Sequence):
    def __init__(self, object_list, paginator, forward, key, key_field_info, attr_name,
                 offset, max_size, next_item, first_page):
        """Constructor.
        Do not use it directly ; use FlowPaginator.page().

        @param object_list: Iterable of model instances.
        @param paginator: A paginator with the following attribute: queryset.
        @param forward: Boolean ; True=>forward ; False=>backward.
        @param key: See FlowPaginator.
        @param key_field_info: Instance of FieldInfo corresponding to the key.
        @param attr_name: (Composite) attribute name corresponding to the key (ie: key without the '-' prefix).
        @param offset: Positive integer indicating the offset used with the key to get the object_list.
        @param max_size: Maximum size of pages with the paginator.
        @param next_item: First item of the next page ; 'None' if it's the last page.
        @param first_page: Indicates if its the first page (so there is no previous page).
        """
        # QuerySets do not manage negative indexing, so we build a list.
        self.object_list = list(object_list)
        self.paginator = paginator
        self._key = key
        self._key_field_info = key_field_info
        self._attr_name = attr_name
        self._offset = offset
        self._max_size = max_size
        self._forward = forward
        self._next_item = next_item
        self._first_page = bool(first_page)

    def __repr__(self):
        return '<Page key=%s offset=%s items[0]=%s>' % (
            self._key, self._offset, self[0]
        )

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        return self.object_list[index]

    # NB: 'maxsize=None' => avoid locking (will only be used with the same value)
    @lru_cache(maxsize=None)
    def _get_duplicates_count(self, value):
        return self.paginator.queryset.filter(**{self._attr_name: value}).count()

    def has_next(self):
        return self._next_item is not None

    def has_previous(self):
        return not self._first_page

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    @staticmethod
    def _serialize_value(value):
        if isinstance(value, date):
            return value.strftime(DATETIME_ISO8601_FMT
                                  if isinstance(value, datetime) else
                                  DATE_ISO8601_FMT
                                 )

        if isinstance(value, Decimal):
            return str(value)

        return value

    def info(self):
        """Returns a dictionary which can be given to FlowPaginator.page() to get this page again.
        This dictionary can be natively serialized to JSON.

        You do not have to understand the content on this dictionary ;
        you can just use it with FlowPaginator.page().

        Internal information:
        The dictionary contains the following items:
            'type': string in {'first', 'last', 'forward', 'backward'}.
            'key':  [not with 'first' type] field name used as key.
            'value': [not with 'first'/'last' types] value of the key.
            'offset': [optional & only with 'forward'/'backward' types] a positive integer.
                      When this item is missing, it is considered to be 0.

        Behavior of 'type' (X == max_size)
        (notice that objects order is the paginator.queryset's order):
            - 'first': first page, the content is the X first objects.
            - 'last': last page, the content is the X last objects.
            - 'forward': forward mode, the content is the X first objects where object.key >= value.
                         Offset behaviour: if offset==1, the first object will be the 2nd object with
                         object.key >= value ; if offset==2, it will be the 3rd. etc...
            - 'backward': backward mode, the content is the X last objects where object.key <= value.
                          Offset behaviour: with offset==0, the last item is ignored (because it is
                          the first item of the next page) ;
                          so with offset==1, we ignore the _2_ last items, etc...
        """
        if not self.has_previous():
            return {'type': 'first'}

        if not self.has_next():
            return {'type': 'last', 'key': self._key}

        if self._forward:
            move_type = _FORWARD
            value_item = self.object_list[0]
        else:
            move_type = _BACKWARD
            value_item = self._next_item

        return self._build_info(move_type, offset=self._offset,
                                value=self._key_field_info.value_from(value_item),
                               )

    def _build_info(self, move_type, value, offset):
        info = {'type': move_type, 'key': self._key, 'value': self._serialize_value(value)}

        if offset:
            info['offset'] = offset

        return info

    def _compute_offset(self, value, objects):
        """Count the number of key duplicates.
        @param value Value of the key for the reference object.
        @param objects Iterable ; instances to evaluate.
        """
        offset = 0
        value_from = self._key_field_info.value_from

        for elt in objects:
            if value != value_from(elt):
                break

            offset += 1

        return offset

    def next_page_info(self):
        """Returns a dictionary which can be given to FlowPaginator.page() to get the next page.

        @see info()
        Internal information ; notice that 'type' will always be 'forward'.
        """
        next_item = self._next_item

        # TODO: populate FK fields to avoid multiple query for the duplicates search
        #         => improved version of CremeEntity.populate_fk_fields
        if next_item is not None:
            value = self._key_field_info.value_from(next_item)
            offset = self._compute_offset(value, reversed(self.object_list))

            if offset == self._max_size:
                # The duplicates fill this page & there can be some duplicates on the previous page(s)
                if self._forward:
                    # Offsets are in the same direction (forward) => we cumulate them
                    offset += self._offset
                else:
                    # NB: it's easy to see (with a sketch) that
                    #     duplicates_count = forward_offset + backward_offset + 1
                    #     (with here forward_offset == offset & backward_offset == self._offset)
                    offset = self._get_duplicates_count(value) - self._offset - 1

            return self._build_info(_FORWARD, value, offset)

    def previous_page_info(self):
        """Returns a dictionary which can be given to FlowPaginator.page() to get the previous page.

        @see info()
        Internal information ; notice that 'type' will always be 'backward'.
        """
        if self.has_previous():
            object_iter = iter(self.object_list)
            value = self._key_field_info.value_from(next(object_iter))
            offset = self._compute_offset(value, object_iter)

            if offset == self._max_size - 1:  # NB: _max_size > 1
                # The duplicates fill this page & there can be some duplicates on the next page(s)
                if self._forward:
                    # NB: it's easy to see (with a sketch) that
                    #     duplicates_count = forward_offset + backward_offset + 1
                    #     (with here forward_offset == self._offset  & backward_offset == offset)
                    offset = self._get_duplicates_count(value) - self._offset - 1
                elif self._offset:
                    # Offsets are in the same direction (backward) => we cumulate them
                    offset += self._offset + 1

            return self._build_info(_BACKWARD, value, offset)