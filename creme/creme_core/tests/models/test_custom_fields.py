# -*- coding: utf-8 -*-

try:
    from collections import defaultdict
    from decimal import Decimal
    from functools import partial

    from django import forms
    from django.contrib.contenttypes.models import ContentType
    from django.utils.translation import gettext as _

    from ..base import CremeTestCase

    from creme.creme_core.models import (
        CustomField,
        CustomFieldInteger, CustomFieldFloat, CustomFieldBoolean,
        CustomFieldString,
        CustomFieldDateTime,
        CustomFieldEnumValue, CustomFieldEnum, CustomFieldMultiEnum,
        FakeOrganisation,
    )

    from creme.creme_config.forms.fields import (
        CustomEnumChoiceField,
        CustomMultiEnumChoiceField,
    )
except Exception as e:
    print(f'Error in <{__name__}>: {e}')


class CustomFieldsTestCase(CremeTestCase):
    def assertValueEqual(self, *, cfield, entity, value):
        cf_value = self.get_object_or_fail(
            cfield.get_value_class(),
            custom_field=cfield,
            entity=entity,
        )
        self.assertEqual(value, cf_value.value)

    def _create_orga(self):
        return FakeOrganisation.objects.create(
            user=self.create_user(),
            name='Arcadia',
        )

    def test_int01(self):
        name = 'Length of ship'
        cfield: CustomField = CustomField.objects.create(
            name=name,
            field_type=CustomField.INT,
            content_type=FakeOrganisation,
        )
        self.assertEqual(
            ContentType.objects.get_for_model(FakeOrganisation),
            cfield.content_type,
        )
        self.assertTrue(cfield.uuid)
        self.assertIs(cfield.is_required, False)
        self.assertEqual(name, str(cfield))
        self.assertEqual(CustomFieldInteger, cfield.get_value_class())
        self.assertEqual(_('Integer'), cfield.type_verbose_name())

        self.assertEqual(
            'customfieldinteger',
            CustomFieldInteger.get_related_name()
        )

        orga = self._create_orga()
        value = 1562
        cf_value = CustomFieldInteger.objects.create(
            custom_field=cfield,
            entity=orga,
            value=value,
        )
        self.assertValueEqual(cfield=cfield, entity=orga, value=value)
        self.assertEqual(str(value), cfield.get_pretty_value(orga.id))

        formfield1 = cfield.get_formfield(custom_value=cf_value, user=orga.user)
        self.assertIsInstance(formfield1, forms.IntegerField)
        self.assertFalse(formfield1.required)
        self.assertEqual(value, formfield1.initial)

        formfield2 = cfield.get_formfield(custom_value=None, user=orga.user)
        self.assertIsInstance(formfield2, forms.IntegerField)
        self.assertIsNone(formfield2.initial)

    def test_int02(self):
        "value_n_save()."
        cfield = CustomField.objects.create(
            name='Length of ship',
            field_type=CustomField.INT,
            content_type=FakeOrganisation,
        )
        orga = self._create_orga()

        cf_value: CustomFieldInteger = CustomFieldInteger.objects.create(
            custom_field=cfield,
            entity=orga,
            value=456,
        )

        value = cf_value.value + 1

        with self.assertNumQueries(1):
            cf_value.set_value_n_save(value)

        self.assertEqual(value, self.refresh(cf_value).value)

        # ---
        with self.assertNumQueries(0):
            cf_value.set_value_n_save(value)

    def test_str(self):
        cfield = CustomField.objects.create(
            name='Length of ship',
            field_type=CustomField.STR,
            content_type=FakeOrganisation,
            is_required=True,
        )
        self.assertEqual(CustomFieldString, cfield.get_value_class())
        self.assertEqual(_('String'), cfield.type_verbose_name())

        self.assertEqual(
            'customfieldstring',
            CustomFieldString.get_related_name()
        )

        orga = self._create_orga()
        value = '1562 m'
        cf_value = CustomFieldString.objects.create(
            custom_field=cfield,
            entity=orga,
            value=value,
        )
        self.assertValueEqual(cfield=cfield, entity=orga, value=value)

        formfield = cfield.get_formfield(custom_value=cf_value, user=orga.user)
        self.assertIsInstance(formfield, forms.CharField)
        self.assertTrue(formfield.required)
        self.assertEqual(value, formfield.initial)

    def test_decimal(self):
        cfield = CustomField.objects.create(
            name='Length of ship',
            field_type=CustomField.FLOAT,
            content_type=FakeOrganisation,
        )
        self.assertEqual(CustomFieldFloat, cfield.get_value_class())
        self.assertEqual(_('Decimal'), cfield.type_verbose_name())

        orga = self._create_orga()
        value1 = '1562.50'
        cf_value = CustomFieldFloat.objects.create(
            custom_field=cfield,
            entity=orga,
            value=value1,
        )
        self.assertValueEqual(cfield=cfield, entity=orga, value=Decimal(value1))

        cf_value.value = value2 = Decimal('1562.60')
        cf_value.save()
        self.assertValueEqual(cfield=cfield, entity=orga, value=value2)

        formfield = cfield.get_formfield(custom_value=cf_value, user=orga.user)
        self.assertIsInstance(formfield, forms.DecimalField)

    def test_datetime(self):
        user = self.create_user()
        cfield = CustomField.objects.create(
            name='Last battle',
            field_type=CustomField.DATETIME,
            content_type=FakeOrganisation,
        )
        self.assertEqual(CustomFieldDateTime, cfield.get_value_class())
        self.assertEqual(_('Date and time'), cfield.type_verbose_name())

        orga = FakeOrganisation.objects.create(user=user, name='Arcadia')
        value = self.create_datetime(year=2058, month=2, day=15, hour=18, minute=32)
        CustomFieldDateTime.objects.create(
            custom_field=cfield,
            entity=orga,
            value=value,
        )
        self.assertValueEqual(cfield=cfield, entity=orga, value=value)

        formfield = cfield.get_formfield(custom_value=None, user=orga.user)
        self.assertIsInstance(formfield, forms.DateTimeField)

    def test_bool01(self):
        create_cfield = partial(
            CustomField.objects.create,
            field_type=CustomField.BOOL,
            content_type=ContentType.objects.get_for_model(FakeOrganisation),
        )
        cfield1 = create_cfield(name='Ship is armed?')
        self.assertEqual(CustomFieldBoolean, cfield1.get_value_class())
        self.assertEqual(_('Boolean (2 values: Yes/No)'), cfield1.type_verbose_name())

        orga = self._create_orga()
        value = True
        cf_value = CustomFieldBoolean.objects.create(
            custom_field=cfield1,
            entity=orga,
            value=value,
        )
        self.assertValueEqual(cfield=cfield1, entity=orga, value=value)

        formfield = cfield1.get_formfield(custom_value=cf_value, user=orga.user)
        self.assertIsInstance(formfield, forms.NullBooleanField)
        self.assertFalse(formfield.required)
        self.assertEqual(value, formfield.initial)

        # ---
        cfield2 = create_cfield(name='Pirates?', is_required=True)
        formfield = cfield2.get_formfield(custom_value=None, user=orga.user)
        self.assertIsInstance(formfield, forms.BooleanField)
        self.assertFalse(formfield.required)

    def test_bool02(self):
        "set_value_n_save()."
        cfield = CustomField.objects.create(
            name='Ship is armed?',
            field_type=CustomField.BOOL,
            content_type=FakeOrganisation,
        )
        orga = self._create_orga()

        cf_value: CustomFieldBoolean = CustomFieldBoolean.objects.create(
            custom_field=cfield,
            entity=orga,
            value=False,
        )

        with self.assertNumQueries(1):
            cf_value.set_value_n_save(True)

        self.assertIs(self.refresh(cf_value).value, True)

        # ---
        with self.assertNumQueries(1):
        # with self.assertNumQueries(0):  # TODO: beware to False case
            cf_value.set_value_n_save(True)

        # ---
        with self.assertNumQueries(1):
            cf_value.set_value_n_save(False)

        self.assertIs(self.refresh(cf_value).value, False)

        # ---
        with self.assertNumQueries(0):
            cf_value.set_value_n_save(None)

    def test_enum01(self):
        cfield = CustomField.objects.create(
            name='Type of ship',
            field_type=CustomField.ENUM,
            content_type=FakeOrganisation,
        )
        self.assertEqual(CustomFieldEnum, cfield.get_value_class())
        self.assertEqual(_('Choice list'), cfield.type_verbose_name())

        enum_value = CustomFieldEnumValue.objects.create(
            custom_field=cfield,
            value='BattleShip',
        )
        orga = self._create_orga()
        cf_value = CustomFieldEnum.objects.create(
            custom_field=cfield,
            entity=orga,
            value=enum_value,
        )
        self.assertValueEqual(cfield=cfield, entity=orga, value=enum_value)
        self.assertEqual(enum_value.value, cfield.get_pretty_value(orga.id))

        formfield = cfield.get_formfield(custom_value=cf_value, user=orga.user)
        self.assertIsInstance(formfield, CustomEnumChoiceField)
        self.assertEqual(orga.user, formfield.user)
        self.assertEqual(cfield,    formfield.custom_field)
        self.assertFalse(formfield.required)

    def test_enum02(self):
        "set_value_n_save()."
        cfield = CustomField.objects.create(
            name='Type of ship',
            field_type=CustomField.ENUM,
            content_type=FakeOrganisation,
        )

        create_enum_value = partial(
            CustomFieldEnumValue.objects.create,
            custom_field=cfield,
        )
        enum_value1 = create_enum_value(value='BattleShip')
        enum_value2 = create_enum_value(value='Transporter')

        orga = self._create_orga()
        cf_value = CustomFieldEnum.objects.create(
            custom_field=cfield,
            entity=orga,
            value=enum_value1,
        )

        with self.assertNumQueries(1):
            cf_value.set_value_n_save(str(enum_value2.id))

        self.assertEqual(enum_value2, self.refresh(cf_value).value)

        # ---
        with self.assertNumQueries(0):
            cf_value.set_value_n_save(enum_value2.id)

    def test_multi_enum01(self):
        cfield = CustomField.objects.create(
            name='Weapons',
            field_type=CustomField.MULTI_ENUM,
            content_type=FakeOrganisation,
        )
        self.assertEqual(CustomFieldMultiEnum, cfield.get_value_class())
        self.assertEqual(_('Multiple choice list'), cfield.type_verbose_name())

        create_enum_value = partial(
            CustomFieldEnumValue.objects.create,
            custom_field=cfield,
        )
        enum_value1 = create_enum_value(value='Lasers')
        enum_value2 = create_enum_value(value='Missiles')
        orga = self._create_orga()
        cf_value = CustomFieldMultiEnum.objects.create(
            custom_field=cfield,
            entity=orga,
        )
        cf_value.value.set([enum_value1, enum_value2])

        self.assertSetEqual(
            {enum_value1, enum_value2},
            {*self.refresh(cf_value).value.all()}
        )
        self.assertEqual('Lasers / Missiles', cfield.get_pretty_value(orga.id))

        formfield = cfield.get_formfield(custom_value=cf_value, user=orga.user)
        self.assertIsInstance(formfield, CustomMultiEnumChoiceField)
        self.assertEqual(orga.user, formfield.user)
        self.assertEqual(cfield,    formfield.custom_field)
        self.assertFalse(formfield.required)
        self.assertListEqual(
            [
                (enum_value1.id, enum_value1.value),
                (enum_value2.id, enum_value2.value),
            ],
            formfield.choices
        )

    def test_multi_enum02(self):
        "set_value_n_save()."
        cfield = CustomField.objects.create(
            name='Weapons',
            field_type=CustomField.MULTI_ENUM,
            content_type=FakeOrganisation,
        )

        create_enum_value = partial(
            CustomFieldEnumValue.objects.create,
            custom_field=cfield,
        )
        enum_value1 = create_enum_value(value='Lasers')
        enum_value2 = create_enum_value(value='Missiles')
        orga = self._create_orga()

        cf_value = CustomFieldMultiEnum.objects.create(
            custom_field=cfield,
            entity=orga,
        )

        with self.assertNumQueries(3):
            cf_value.set_value_n_save([enum_value1, enum_value2])

        self.assertSetEqual(
            {enum_value1, enum_value2},
            {*self.refresh(cf_value).value.all()}
        )

    def test_delete(self):
        create_cfield = partial(
            CustomField.objects.create,
            field_type=CustomField.STR,
            content_type=FakeOrganisation,
        )
        cfield1 = create_cfield(name='Length of ship')
        cfield2 = create_cfield(name='Width of ship')

        def create_value(cfield, value):
            return CustomFieldString.objects.create(
                custom_field=cfield,
                entity=orga,
                value=value,
            )

        orga = self._create_orga()
        cf_value1 = create_value(cfield1, '1562 m')
        cf_value2 = create_value(cfield2, '845 m')

        cfield1.delete()
        self.assertDoesNotExist(cfield1)
        self.assertDoesNotExist(cf_value1)
        self.assertStillExists(cfield2)
        self.assertStillExists(cf_value2)

    def test_delete_entity(self):
        create_orga = partial(
            FakeOrganisation.objects.create,
            user=self.create_user(),
        )
        orga1 = create_orga(name='Arcadia')
        orga2 = create_orga(name='Queen Emeraldas')

        cfield: CustomField = CustomField.objects.create(
            name='Length',
            field_type=CustomField.INT,
            content_type=FakeOrganisation,
        )

        def create_value(entity, value):
            return CustomFieldInteger.objects.create(
                custom_field=cfield,
                entity=entity,
                value=value,
            )

        cf_value1 = create_value(orga1, 1562)
        cf_value2 = create_value(orga2, 1236)

        orga1.delete()
        self.assertDoesNotExist(orga1)
        self.assertStillExists(cfield)
        self.assertDoesNotExist(cf_value1)
        self.assertStillExists(orga2)
        self.assertStillExists(cf_value2)

    def test_save_values_for_entities(self):
        cfield = CustomField.objects.create(
            name='Length of ship',
            field_type=CustomField.INT,
            content_type=FakeOrganisation,
        )
        create_orga = partial(
            FakeOrganisation.objects.create,
            user=self.create_user(),
        )
        orga1 = create_orga(name='Arcadia')
        orga2 = create_orga(name='Queen Emeraldas')

        value = 456
        with self.assertNumQueries(3):
            CustomFieldInteger.save_values_for_entities(
                custom_field=cfield,
                entities=[orga1, orga2],
                value=value,
            )

        cf_value1 = self.get_object_or_fail(CustomFieldInteger, custom_field=cfield, entity=orga1)
        self.assertEqual(value, cf_value1.value)

        cf_value2 = self.get_object_or_fail(CustomFieldInteger, custom_field=cfield, entity=orga1)
        self.assertEqual(value, cf_value2.value)

        # Do not save entities with existing same value ---
        orga3 = create_orga(name='Yamato')

        with self.assertNumQueries(2):
            CustomFieldInteger.save_values_for_entities(
                custom_field=cfield,
                entities=[orga1, orga3],
                value=value,
            )

        cf_value3 = self.get_object_or_fail(CustomFieldInteger, custom_field=cfield, entity=orga3)
        self.assertEqual(value, cf_value3.value)

        # Empty value => deletion ---
        with self.assertNumQueries(2):
            # NB: Django makes a query to retrieve the IDs, then performs a
            #     second query...
            CustomFieldInteger.save_values_for_entities(
                custom_field=cfield,
                entities=[orga1, orga2],
                value=None,
            )

        self.assertDoesNotExist(cf_value1)
        self.assertDoesNotExist(cf_value2)
        self.assertStillExists(cf_value3)

    def test_get_custom_values_map01(self):
        create_cfield = partial(
            CustomField.objects.create,
            field_type=CustomField.INT,
            content_type=ContentType.objects.get_for_model(FakeOrganisation),
        )
        cfield1 = create_cfield(name='Length of ship')
        cfield2 = create_cfield(name='Width of ship')

        create_orga = partial(
            FakeOrganisation.objects.create,
            user=self.create_user(),
        )
        orga1 = create_orga(name='Arcadia')
        orga2 = create_orga(name='Queen Emeraldas')
        orga3 = create_orga(name='Yamato')

        create_cf_value = CustomFieldInteger.objects.create
        cf_value11 = create_cf_value(custom_field=cfield1, entity=orga1, value=1200)
        cf_value12 = create_cf_value(custom_field=cfield2, entity=orga1, value=450)
        cf_value21 = create_cf_value(custom_field=cfield1, entity=orga2, value=860)

        with self.assertNumQueries(1):
            values_map = CustomField.get_custom_values_map(
                entities=[orga1, orga2, orga3],
                custom_fields=[cfield1, cfield2],
            )

        self.assertIsInstance(values_map, defaultdict)
        self.assertIsInstance(values_map.default_factory(), dict)
        self.assertDictEqual(
            {
                orga1.id: {
                    cfield1.id: cf_value11,
                    cfield2.id: cf_value12,
                },
                orga2.id: {
                    cfield1.id: cf_value21,
                },
                # orga3.id: {}, NOPE
            },
            values_map
        )

    def test_get_custom_values_map02(self):
        "Several types of fields."
        create_cfield = partial(
            CustomField.objects.create,
            content_type=ContentType.objects.get_for_model(FakeOrganisation),
        )
        cfield1 = create_cfield(name='Length of ship', field_type=CustomField.INT)
        cfield2 = create_cfield(name='Width of ship',  field_type=CustomField.STR)

        create_orga = partial(
            FakeOrganisation.objects.create,
            user=self.create_user(),
        )
        orga1 = create_orga(name='Arcadia')
        orga2 = create_orga(name='Queen Emeraldas')

        create_cf_value1 = partial(CustomFieldInteger.objects.create, custom_field=cfield1)
        create_cf_value2 = partial(CustomFieldString.objects.create,  custom_field=cfield2)
        cf_value11 = create_cf_value1(custom_field=cfield1, entity=orga1, value=1200)
        cf_value12 = create_cf_value2(custom_field=cfield2, entity=orga1, value='450 m')
        cf_value21 = create_cf_value1(custom_field=cfield1, entity=orga2, value=860)

        with self.assertNumQueries(2):
            values_map = CustomField.get_custom_values_map(
                entities=[orga1, orga2],
                custom_fields=[cfield1, cfield2],
            )

        self.assertDictEqual(
            {
                orga1.id: {
                    cfield1.id: cf_value11,
                    cfield2.id: cf_value12,
                },
                orga2.id: {
                    cfield1.id: cf_value21,
                },
                # orga3.id: {}, NOPE
            },
            values_map
        )