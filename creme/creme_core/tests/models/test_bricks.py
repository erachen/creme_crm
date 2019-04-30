# -*- coding: utf-8 -*-

try:
    from functools import partial
    from json import loads as jsonloads

    from django.contrib.auth import get_user_model
    from django.contrib.contenttypes.models import ContentType
    from django.utils.translation import gettext as _

    from ..base import CremeTestCase
    from ..fake_models import FakeContact, FakeOrganisation, FakeImage
    from creme.creme_core.bricks import RelationsBrick, PropertiesBrick, CustomFieldsBrick, HistoryBrick
    from creme.creme_core.core.entity_cell import EntityCellRegularField, EntityCellFunctionField
    from creme.creme_core.gui.bricks import Brick
    from creme.creme_core.models import (BrickDetailviewLocation, UserRole,
            BrickHomeLocation, BrickMypageLocation,
            CremeEntity, InstanceBrickConfigItem,
            RelationBrickItem, RelationType, CustomBrickConfigItem)
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))


class BrickTestCase(CremeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls._bdl_backup = list(BrickDetailviewLocation.objects.all())
        cls._bpl_backup = list(BrickHomeLocation.objects.all())
        cls._bml_backup = list(BrickMypageLocation.objects.all())

        BrickDetailviewLocation.objects.all().delete()
        BrickHomeLocation.objects.all().delete()
        BrickMypageLocation.objects.all().delete()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        BrickDetailviewLocation.objects.all().delete()
        BrickHomeLocation.objects.all().delete()
        BrickMypageLocation.objects.all().delete()

        for model, backup in [(BrickDetailviewLocation, cls._bdl_backup),
                              (BrickHomeLocation, cls._bpl_backup),
                              (BrickMypageLocation, cls._bml_backup),
                             ]:
            try:
                model.objects.bulk_create(backup)
            except Exception as e:
                print('CremeBlockTagsTestCase: test-data backup problem with model={} ({})'.format(model, e))

    def test_populate(self):
        self.assertLessEqual({'modelblock', CustomFieldsBrick.id_, RelationsBrick.id_,
                              PropertiesBrick.id_, HistoryBrick.id_,
                              },
                             {loc.brick_id for loc in self._bdl_backup}
                            )
        brick_id = HistoryBrick.id_
        self.assertIn(brick_id, {bpl.brick_id for bpl in self._bpl_backup})
        self.assertIn(brick_id, {bml.brick_id for bml in self._bml_backup if bml.user is None})

    def test_create_detailview02(self):
        "For a ContentType"
        self.assertFalse(BrickDetailviewLocation.config_exists(FakeContact))

        order = 4
        zone = BrickDetailviewLocation.LEFT
        brick_id = PropertiesBrick.id_
        loc = BrickDetailviewLocation.create_if_needed(brick_id=brick_id, order=order, zone=zone, model=FakeContact)
        loc = self.get_object_or_fail(BrickDetailviewLocation, pk=loc.pk)
        self.assertEqual(FakeContact, loc.content_type.model_class())
        self.assertEqual(brick_id, loc.brick_id)
        self.assertEqual(order,    loc.order)
        self.assertEqual(zone,     loc.zone)

        self.assertTrue(BrickDetailviewLocation.config_exists(FakeContact))

    def test_create_detailview03(self):
        "Do not create if already exists (in any zone/order)"
        brick_id = PropertiesBrick.id_
        order = 5
        zone = BrickDetailviewLocation.RIGHT

        create_bdl = partial(BrickDetailviewLocation.create_if_needed, brick_id=brick_id, model=FakeContact)
        create_bdl(order=order, zone=zone)
        create_bdl(order=4, zone=BrickDetailviewLocation.LEFT)

        locs = BrickDetailviewLocation.objects.filter(
                brick_id=brick_id,
                content_type=ContentType.objects.get_for_model(FakeContact),
        )
        self.assertEqual(1, len(locs))

        loc = locs[0]
        self.assertEqual(order, loc.order)
        self.assertEqual(zone,  loc.zone)

    def test_create_detailview04(self):
        "For a Role"
        role = UserRole.objects.create(name='Viewer')

        brick_id = PropertiesBrick.id_
        order = 5
        zone = BrickDetailviewLocation.RIGHT

        create_bdl = partial(BrickDetailviewLocation.create_if_needed, brick_id=brick_id,
                             model=FakeContact, role=role,
                             )
        create_bdl(order=order, zone=zone)
        create_bdl(order=4, zone=BrickDetailviewLocation.LEFT)

        locs = BrickDetailviewLocation.objects.filter(
                brick_id=brick_id,
                content_type=ContentType.objects.get_for_model(FakeContact),
                role=role, superuser=False,
        )
        self.assertEqual(1, len(locs))

        loc = locs[0]
        self.assertEqual(order, loc.order)
        self.assertEqual(zone,  loc.zone)

        # Do not avoid default configuration creation
        count = BrickDetailviewLocation.objects.count()
        zone = BrickDetailviewLocation.BOTTOM
        loc = create_bdl(order=order, zone=zone, role=None)
        self.assertEqual(count + 1, BrickDetailviewLocation.objects.count())
        self.assertEqual(zone,  loc.zone)
        self.assertIsNone(loc.role)
        self.assertFalse(loc.superuser)

    def test_create_detailview05(self):
        "For super-users"
        brick_id = PropertiesBrick.id_
        order = 5
        zone = BrickDetailviewLocation.RIGHT

        create_bdl = partial(BrickDetailviewLocation.create_if_needed, brick_id=brick_id,
                             model=FakeContact, role='superuser',
                            )
        create_bdl(order=order, zone=zone)
        create_bdl(order=4, zone=BrickDetailviewLocation.LEFT)

        locs = BrickDetailviewLocation.objects.filter(
                brick_id=brick_id,
                content_type=ContentType.objects.get_for_model(FakeContact),
                role=None, superuser=True,
        )
        self.assertEqual(1, len(locs))

        loc = locs[0]
        self.assertEqual(order, loc.order)
        self.assertEqual(zone,  loc.zone)

        # Do not avoid default configuration creation
        count = BrickDetailviewLocation.objects.count()
        zone = BrickDetailviewLocation.BOTTOM
        loc = create_bdl(order=order, zone=zone, role=None)
        self.assertEqual(count + 1, BrickDetailviewLocation.objects.count())
        self.assertEqual(zone,  loc.zone)
        self.assertIsNone(loc.role)
        self.assertFalse(loc.superuser)

    def test_create_detailview06(self):
        "Default configuration cannot have a related role"
        with self.assertRaises(ValueError):
            BrickDetailviewLocation.create_if_needed(
                    brick_id=PropertiesBrick.id_,
                    order=5, zone=BrickDetailviewLocation.RIGHT,
                    model=None, role='superuser', # <==
            )

    def test_create_4_model_brick01(self):
        order = 5
        zone = BrickDetailviewLocation.RIGHT
        model = FakeContact
        loc = BrickDetailviewLocation.create_4_model_brick(order=order, zone=zone, model=model)

        self.assertEqual(1, BrickDetailviewLocation.objects.count())

        loc = self.get_object_or_fail(BrickDetailviewLocation, pk=loc.id)
        self.assertEqual('modelblock', loc.brick_id)
        self.assertEqual(model,        loc.content_type.model_class())
        self.assertEqual(order,        loc.order)
        self.assertEqual(zone,         loc.zone)

    def test_create_4_model_brick02(self):
        "model = None"
        loc = BrickDetailviewLocation.create_4_model_brick(
                order=8, zone=BrickDetailviewLocation.BOTTOM, model=None,
        )
        self.assertEqual(1, BrickDetailviewLocation.objects.count())
        self.assertEqual('modelblock', loc.brick_id)
        self.assertIsNone(loc.content_type)

    def test_create_4_model_brick03(self):
        "With a Role"
        role = UserRole.objects.create(name='Viewer')
        loc = BrickDetailviewLocation.create_4_model_brick(
                model=FakeContact, role=role,
                order=8, zone=BrickDetailviewLocation.BOTTOM,
        )
        self.assertEqual(1, BrickDetailviewLocation.objects.count())
        self.assertEqual('modelblock', loc.brick_id)
        self.assertEqual(role,         loc.role)

    def test_mypage_new_user(self):
        brick_id = HistoryBrick.id_
        order = 3
        BrickMypageLocation.objects.create(brick_id=brick_id, order=order)

        user = get_user_model().objects.create(username='Kirika')
        user.set_password('password')
        user.save()
        self.get_object_or_fail(BrickMypageLocation, user=user, brick_id=brick_id, order=order)

    def test_relation_block01(self):
        rtype = RelationType.create(('test-subject_loves', 'loves'),
                                    ('test-object_loved',  'is loved by')
                                   )[0]

        rbi = RelationBrickItem.create(rtype.id)

        get_ct = ContentType.objects.get_for_model
        ct_contact = get_ct(FakeContact)
        ct_orga = get_ct(FakeOrganisation)
        ct_img = get_ct(FakeImage)

        rbi = self.refresh(rbi)  # Test persistence
        self.assertIsNone(rbi.get_cells(ct_contact))
        self.assertIsNone(rbi.get_cells(ct_orga))
        self.assertIsNone(rbi.get_cells(ct_img))
        self.assertIs(rbi.all_ctypes_configured, False)

        rbi.set_cells(ct_contact,
                      [EntityCellRegularField.build(FakeContact, 'last_name'),
                       EntityCellFunctionField.build(FakeContact, 'get_pretty_properties'),
                      ],
                     )
        rbi.set_cells(ct_orga, [EntityCellRegularField.build(FakeOrganisation, 'name')])
        rbi.save()

        rbi = self.refresh(rbi)  # Test persistence
        self.assertIsNone(rbi.get_cells(ct_img))
        self.assertIs(rbi.all_ctypes_configured, False)

        cells_contact = rbi.get_cells(ct_contact)
        self.assertEqual(2, len(cells_contact))

        cell_contact = cells_contact[0]
        self.assertIsInstance(cell_contact, EntityCellRegularField)
        self.assertEqual('last_name', cell_contact.value)

        cell_contact = cells_contact[1]
        self.assertIsInstance(cell_contact, EntityCellFunctionField)
        self.assertEqual('get_pretty_properties', cell_contact.value)

        self.assertEqual(1, len(rbi.get_cells(ct_orga)))

    def test_relation_block02(self):
        "All ctypes configured"
        rtype = RelationType.create(('test-subject_rented', 'is rented by'),
                                    ('test-object_rented',  'rents', [FakeContact, FakeOrganisation]),
                                   )[0]

        rbi = RelationBrickItem.create(rtype.id)
        get_ct = ContentType.objects.get_for_model

        rbi.set_cells(get_ct(FakeContact), [EntityCellRegularField.build(FakeContact, 'last_name')])
        rbi.save()
        self.assertFalse(self.refresh(rbi).all_ctypes_configured)

        rbi.set_cells(get_ct(FakeOrganisation), [EntityCellRegularField.build(FakeOrganisation, 'name')])
        rbi.save()
        self.assertTrue(self.refresh(rbi).all_ctypes_configured)

    def test_relation_block_errors(self):
        rtype = RelationType.create(('test-subject_rented', 'is rented by'),
                                    ('test-object_rented',  'rents'),
                                   )[0]
        ct_contact = ContentType.objects.get_for_model(FakeContact)
        rbi = RelationBrickItem.create(rtype.id)

        build = partial(EntityCellRegularField.build, model=FakeContact)
        rbi.set_cells(ct_contact,
                      [build(name='last_name'), build(name='description')]
                     )
        rbi.save()

        # Inject error by bypassing checkings
        RelationBrickItem.objects.filter(id=rbi.id) \
            .update(json_cells_map=rbi.json_cells_map.replace('description', 'invalid'))

        rbi = self.refresh(rbi)
        cells_contact = rbi.get_cells(ct_contact)
        self.assertEqual(1, len(cells_contact))
        self.assertEqual('last_name', cells_contact[0].value)

        with self.assertNoException():
            deserialized = jsonloads(rbi.json_cells_map)

        self.assertEqual({str(ct_contact.id): [{'type': 'regular_field', 'value': 'last_name'}]},
                         deserialized
                        )

    def test_custom_block(self):
        cbci = CustomBrickConfigItem.objects.create(
                id='tests-organisations01', name='General',
                content_type=ContentType.objects.get_for_model(FakeOrganisation),
                cells=[EntityCellRegularField.build(FakeOrganisation, 'name')],
        )

        cells = self.refresh(cbci).cells
        self.assertEqual(1, len(cells))

        cell = cells[0]
        self.assertIsInstance(cell, EntityCellRegularField)
        self.assertEqual('name', cell.value)

    def test_custom_block_errors01(self):
        cbci = CustomBrickConfigItem.objects.create(
                id='tests-organisations01', name='General',
                content_type=ContentType.objects.get_for_model(FakeOrganisation),
                cells=[EntityCellRegularField.build(FakeOrganisation, 'name'),
                       EntityCellRegularField.build(FakeOrganisation, 'description'),
                      ],
        )

        # Inject error by bypassing checkings
        CustomBrickConfigItem.objects.filter(id=cbci.id) \
            .update(json_cells=cbci.json_cells.replace('description', 'invalid'))

        cbci = self.refresh(cbci)
        self.assertEqual(1, len(cbci.cells))

        with self.assertNoException():
            deserialized = jsonloads(cbci.json_cells)

        self.assertEqual([{'type': 'regular_field', 'value': 'name'}],
                         deserialized
                        )

    def test_custom_block_errors02(self):
        cbci = CustomBrickConfigItem.objects.create(
                id='tests-organisations01', name='General',
                content_type=ContentType.objects.get_for_model(FakeOrganisation),
                cells=[EntityCellRegularField.build(FakeOrganisation, 'name'),
                       EntityCellRegularField.build(FakeOrganisation, 'invalid'),
                      ],
        )

        cbci = self.refresh(cbci)
        self.assertEqual(1, len(cbci.cells))

    # See reports for InstanceBlockConfigItem with a working classes; here are the error cases
    def test_instance_block(self):
        self.login()

        class TestInstanceBlock(Brick):
            id_ = InstanceBrickConfigItem.generate_base_id('creme_core', 'invalid_id')

        brick_entity = CremeEntity.objects.create(user=self.user)

        generate_id = InstanceBrickConfigItem.generate_id
        self.assertRaises(ValueError, generate_id, TestInstanceBlock, brick_entity, 'foo#bar')

        ibi = InstanceBrickConfigItem(
                brick_id=generate_id(TestInstanceBlock, brick_entity, ''),
                entity=brick_entity,
        )

        id_is_specific = InstanceBrickConfigItem.id_is_specific
        self.assertFalse(id_is_specific(Brick.generate_id('creme_core', 'foobar')))
        self.assertTrue(id_is_specific(ibi.brick_id))

        brick = ibi.brick
        self.assertIsInstance(brick, Brick)
        self.assertFalse(isinstance(brick, TestInstanceBlock))  # Because the class is not registered
        self.assertEqual('??', brick.verbose_name)

        errors = [_('Unknown type of block (bad uninstall ?)')]
        self.assertEqual(errors, getattr(brick, 'errors', None))
        self.assertEqual(errors, ibi.errors)

# TODO: test BlockState
