# -*- coding: utf-8 -*-

try:
    from copy import deepcopy
    from functools import partial

    from django.conf import settings
    from django.contrib.contenttypes.models import ContentType
    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext as _

    from creme.creme_core.tests.base import CremeTestCase, skipIfNotInstalled
    from creme.creme_core.tests.fake_models import (FakeContact, FakeOrganisation, FakeAddress,
            FakeImage, FakeActivity, FakeEmailCampaign, FakeInvoiceLine)
    from creme.creme_core.bricks import (RelationsBrick, PropertiesBrick,
                                         HistoryBrick, CustomFieldsBrick)
    # from creme.creme_core.constants import MODELBLOCK_ID
    from creme.creme_core.core.entity_cell import (EntityCellRegularField,
            EntityCellCustomField, EntityCellFunctionField, EntityCellRelation)
    from creme.creme_core.gui import bricks as gui_bricks
    from creme.creme_core.gui.bricks import Brick, SpecificRelationsBrick  # block_registry
    from creme.creme_core.models import (RelationType, CustomField, FieldsConfig, UserRole,
            BlockDetailviewLocation, InstanceBlockConfigItem,
            BlockPortalLocation, BlockMypageLocation, RelationBlockItem, CustomBlockConfigItem)
    from creme.creme_core.registry import creme_registry

    from creme.creme_config import bricks
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


# Test Bricks ------------------------------------------------------------------
class _BaseCompleteBrick(Brick):
    verbose_name = u'Testing purpose'

    def detailview_display(self, context):
        # return self._render(self.get_block_template_context(context))
        return '<table id="%s"></table>' % self.id_

    def home_display(self, context):
        return '<table id="%s"></table>' % self.id_

    def portal_display(self, context, ct_ids):
        return '<table id="%s"></table>' % self.id_


class CompleteBrick1(_BaseCompleteBrick):
    id_ = Brick.generate_id('creme_config', 'testbrickconfig_complete_1')


class CompleteBrick2(_BaseCompleteBrick):
    id_ = Brick.generate_id('creme_config', 'testbrickconfig_complete_2')


class CompleteBrick3(_BaseCompleteBrick):
    id_ = Brick.generate_id('creme_config', 'testbrickconfig_complete_3')


class CompleteBrick4(_BaseCompleteBrick):
    id_ = Brick.generate_id('creme_config', 'testbrickconfig_complete_4')


class HomePortalBrick(Brick):
    id_          = Brick.generate_id('creme_config', 'testbrickconfig_home_portal')
    verbose_name = u'Testing purpose'

    # def detailview_display(self, context): NO

    def home_display(self, context):
        return '<table id="%s"></table>' % self.id_

    def portal_display(self, context, ct_ids):
        return '<table id="%s"></table>' % self.id_


class PortalOnlyBrick1(Brick):
    id_          = Brick.generate_id('creme_config', 'testbrickconfig_portal_only_1')
    verbose_name = u'Testing purpose'

    def portal_display(self, context, ct_ids):
        return '<table id="%s"></table>' % self.id_


class PortalOnlyBrick2(Brick):
    id_          = Brick.generate_id('creme_config', 'testbrickconfig_portal_only_2')
    verbose_name = u'Testing purpose'
    configurable = False  # <----

    def portal_display(self, context, ct_ids):
        return '<table id="%s"></table>' % self.id_


class PortalOnlyBrick3(Brick):
    id_          = Brick.generate_id('creme_config', 'testbrickconfig_portal_only_3')
    verbose_name = u'Testing purpose'
    target_apps  = ('persons', 'billing')

    def portal_display(self, context, ct_ids):
        return '<table id="%s"></table>' % self.id_


class PortalOnlyBrick4(Brick):
    id_          = Brick.generate_id('creme_config', 'testbrickconfig_portal_only_4')
    verbose_name = u'Testing purpose'
    target_apps  = ('billing', 'documents')

    def portal_display(self, context, ct_ids):
        return '<table id="%s"></table>' % self.id_


class HomeOnlyBrick(Brick):
    id_          = Brick.generate_id('creme_config', 'testbrickconfig_home_only')
    verbose_name = u'Testing purpose'

    # def detailview_display(self, context): return self._render(self.get_block_template_context(context))
    # def portal_display(self, context, ct_ids): return '<table id="%s"></table>' % self.id_

    def home_display(self, context):
        return '<table id="%s"></table>' % self.id_


class DetailviewInstanceBrick(Brick):
    id_ = InstanceBlockConfigItem.generate_base_id('creme_config', 'test_detail_instance')

    def __init__(self, instance_block_config_item):
        super(DetailviewInstanceBrick, self).__init__()
        self.ibci = instance_block_config_item

    def detailview_display(self, context):
        return '<table id="%s"><thead><tr>%s</tr></thead></table>' % (self.id_, self.ibci.entity)


class PortalInstanceBrick(Brick):
    id_          = InstanceBlockConfigItem.generate_base_id('creme_config', 'test_portal_instance')
    verbose_name = u'Testing purpose'

    def __init__(self, instance_block_config_item):
        super(PortalInstanceBrick, self).__init__()
        self.ibci = instance_block_config_item

    def portal_display(self, context, ct_ids):
        return '<table id="%s"><thead><tr>%s</tr></thead></table>' % (self.id_, self.ibci.entity)


class FakeContactHatBrick(Brick):
    id_ = Brick._generate_hat_id('creme_core', 'test_hat_brick')
    verbose_name = u'Fake contact header brick'

    def detailview_display(self, context):
        return '<table id="%s"></table>' % self.id_


# Test case --------------------------------------------------------------------
# class BlocksConfigTestCase(CremeTestCase):
class BricksConfigTestCase(CremeTestCase):
    # DEL_DETAIL_URL = '/creme_config/blocks/detailview/delete'
    DEL_DETAIL_URL = reverse('creme_config__delete_detailview_bricks')
    # PORTAL_WIZARD_URL = '/creme_config/blocks/portal/wizard'
    PORTAL_WIZARD_URL = reverse('creme_config__create_portal_bricks')
    # CUSTOM_WIZARD_URL = '/creme_config/blocks/custom/wizard'
    CUSTOM_WIZARD_URL = reverse('creme_config__create_custom_brick')

    @classmethod
    def setUpClass(cls):
        # CremeTestCase.setUpClass()
        # super(BlocksConfigTestCase, cls).setUpClass()
        super(BricksConfigTestCase, cls).setUpClass()

        cls._bdl_backup = list(BlockDetailviewLocation.objects.all())
        cls._bpl_backup = list(BlockPortalLocation.objects.all())
        cls._bml_backup = list(BlockMypageLocation.objects.all())
        cls._rbi_backup = list(RelationBlockItem.objects.all())

        BlockDetailviewLocation.objects.all().delete()
        BlockPortalLocation.objects.all().delete()
        BlockMypageLocation.objects.all().delete()
        RelationBlockItem.objects.all().delete()

        # cls.populate('creme_core')

        # cls.complete_block     = b1 = CompleteBlock()
        # cls.home_portal_block  = b2 = HomePortalBlock()
        # 
        # cls.portal_only_block1 = b3 = PortalOnlyBlock1()
        # cls.portal_only_block2 = b4 = PortalOnlyBlock2()
        # cls.portal_only_block3 = b5 = PortalOnlyBlock3()
        # cls.portal_only_block4 = b6 = PortalOnlyBlock4()

        # cls.home_only_block = b7 = HomeOnlyBlock()

        # block_registry.register(b1, b2, b3, b4, b5, b6, b7)
        cls._original_block_registry = gui_bricks.brick_registry

        # gui_bricks.block_registry = cls.block_registry = block_registry = deepcopy(gui_bricks.block_registry)
        cls.brick_registry = block_registry = deepcopy(gui_bricks.brick_registry)
        block_registry.register(CompleteBrick1, CompleteBrick2, CompleteBrick3, CompleteBrick4,
                                HomePortalBrick,
                                PortalOnlyBrick1,
                                PortalOnlyBrick2,
                                PortalOnlyBrick3,
                                PortalOnlyBrick4,
                                HomeOnlyBrick
                               )

        block_registry.register_4_instance(DetailviewInstanceBrick)
        block_registry.register_4_instance(PortalInstanceBrick)

    @classmethod
    def tearDownClass(cls):
        # CremeTestCase.tearDownClass()
        # super(BlocksConfigTestCase, cls).tearDownClass()
        super(BricksConfigTestCase, cls).tearDownClass()

        BlockDetailviewLocation.objects.all().delete()
        BlockPortalLocation.objects.all().delete()
        BlockMypageLocation.objects.all().delete()
        RelationBlockItem.objects.all().delete()

        for model, backup in [(BlockDetailviewLocation, cls._bdl_backup),
                              (BlockPortalLocation,     cls._bpl_backup),
                              (BlockMypageLocation,     cls._bml_backup),
                              (RelationBlockItem,       cls._rbi_backup),
                             ]:
            try:
                model.objects.bulk_create(backup)
            except Exception:
                print('CremeBlockTagsTestCase: test-data backup problem with model=%s' % model)

        gui_bricks.brick_registry = cls._original_block_registry

    def setUp(self):
        gui_bricks.brick_registry = self.brick_registry = deepcopy(self.brick_registry)

        self.login()

    def _build_adddetail_url(self, ct):
        # return '/creme_config/blocks/detailview/add/%s' % ct.id
        return reverse('creme_config__create_detailviews_bricks', args=(ct.id,))

    def _build_editdetail_url(self, ct=None, role=None, superuser=False):
        # return '/creme_config/blocks/detailview/edit/%(ctype)s/%(role)s' % {
        #             'ctype': ct.id if ct else 0,
        #             'role':  'superuser' if superuser else
        #                      role.id if role
        #                      else 'default',
        #         }
        return reverse('creme_config__edit_detailview_bricks', args=(
            ct.id if ct else 0,
            'superuser' if superuser else role.id if role else 'default',
        ))

    # def _build_rblock_addctypes_url(self, rbi):
    def _build_rbrick_addctypes_url(self, rbi):
        # return '/creme_config/blocks/relation_block/add_ctypes/%s' % rbi.id
        return reverse('creme_config__add_ctype_config_to_rtype_brick', args=(rbi.id,))

    def _build_rbrick_addctypes_wizard_url(self, rbi):
        # return '/creme_config/blocks/relation_block/%s/wizard' % rbi.id
        return reverse('creme_config__add_cells_to_rtype_brick', args=(rbi.id,))

    # def _build_rblock_editctype_url(self, rbi, model):
    def _build_rbrick_editctype_url(self, rbi, model):
        # return '/creme_config/blocks/relation_block/%s/edit_ctype/%s' % (
        #             rbi.id, ContentType.objects.get_for_model(model).id,
        #         )
        return reverse('creme_config__edit_cells_of_rtype_brick', args=(
                    rbi.id, ContentType.objects.get_for_model(model).id,
                ))

    # def _build_customblock_edit_url(self, cbc_item):
    def _build_custombrick_edit_url(self, cbc_item):
        # return '/creme_config/blocks/custom/edit/%s' % cbc_item.id
        return reverse('creme_config__edit_custom_brick', args=(cbc_item.id,))

    def _find_field_index(self, formfield, name):
        for i, (fname, fvname) in enumerate(formfield.choices):
            if fname == name:
                return i

        self.fail('No "%s" field' % name)

    def _assertNotInChoices(self, formfield, id_, error_msg):
        for fid, fvname in formfield.choices:
            if fid == id_:
                self.fail(error_msg + ' -> should not be in choices.')

    def _find_location(self, block_id, locations):
        for location in locations:
            if location.block_id == block_id:
                return location

        self.fail('No "%s" in locations' % block_id)

    def test_portal(self):
        # response = self.assertGET200('/creme_config/blocks/portal/')
        response = self.assertGET200(reverse('creme_config__bricks'))

        fmt = 'id="%s"'
        self.assertContains(response, fmt % bricks.BlockDetailviewLocationsBrick.id_)
        if settings.OLD_MENU:
            self.assertContains(response, fmt % bricks.BlockPortalLocationsBrick.id_)
        else:
            self.assertContains(response, fmt % bricks.BlockHomeLocationsBrick.id_)
        self.assertContains(response, fmt % bricks.BlockDefaultMypageLocationsBrick.id_)
        self.assertContains(response, fmt % bricks.RelationBlocksConfigBrick.id_)
        self.assertContains(response, fmt % bricks.InstanceBlocksConfigBrick.id_)
        self.assertContains(response, fmt % bricks.CustomBlocksConfigBrick.id_)

    def _aux_test_add_detailview(self, role=None, superuser=False):
        model = FakeContact
        ct = ContentType.objects.get_for_model(model)

        url = self._build_adddetail_url(ct)
        response = self.assertGET200(url)

        with self.assertNoException():
            fields = response.context['form'].fields
            top_field    = fields['top']
            left_field   = fields['left']
            right_field  = fields['right']
            bottom_field = fields['bottom']

        self.assertNotIn('hat', fields)

        bricks = list(self.brick_registry.get_compatible_bricks(model))
        self.assertGreaterEqual(len(bricks), 5)
        self._find_field_index(top_field, CompleteBrick1.id_)

        brick_top_id1   = bricks[0].id_
        brick_top_id2   = bricks[1].id_
        brick_left_id1  = bricks[2].id_
        # brick_left_id2  = MODELBLOCK_ID
        brick_left_id2  = self.brick_registry.get_brick_4_object(model).id_
        brick_right_id  = bricks[3].id_
        brick_bottom_id = bricks[4].id_

        brick_top_index1   = self._find_field_index(top_field, brick_top_id1)
        brick_top_index2   = self._find_field_index(top_field, brick_top_id2)
        brick_left_index1  = self._find_field_index(left_field, brick_left_id1)
        brick_left_index2  = self._find_field_index(left_field, brick_left_id2)
        brick_right_index  = self._find_field_index(right_field, brick_right_id)
        brick_bottom_index = self._find_field_index(bottom_field, brick_bottom_id)

        response = self.client.post(url,
                                    data={'role': role.id if role else '',

                                          'top_check_%s' % brick_top_index1: 'on',
                                          'top_value_%s' % brick_top_index1: brick_top_id1,
                                          'top_order_%s' % brick_top_index1: 1,

                                          'top_check_%s' % brick_top_index2: 'on',
                                          'top_value_%s' % brick_top_index2: brick_top_id2,
                                          'top_order_%s' % brick_top_index2: 2,

                                          'left_check_%s' % brick_left_index1: 'on',
                                          'left_value_%s' % brick_left_index1: brick_left_id1,
                                          'left_order_%s' % brick_left_index1: 1,

                                          'left_check_%s' % brick_left_index2: 'on',
                                          'left_value_%s' % brick_left_index2: brick_left_id2,
                                          'left_order_%s' % brick_left_index2: 2,

                                          'right_check_%s' % brick_right_index: 'on',
                                          'right_value_%s' % brick_right_index: brick_right_id,
                                          'right_order_%s' % brick_right_index: 1,

                                          'bottom_check_%s' % brick_bottom_index: 'on',
                                          'bottom_value_%s' % brick_bottom_index: brick_bottom_id,
                                          'bottom_order_%s' % brick_bottom_index: 1,
                                         }
                                   )
        self.assertNoFormError(response)

        b_locs = BlockDetailviewLocation.objects.filter(content_type=ct, role=role, superuser=superuser)
        filter_locs = lambda zone: [bl for bl in b_locs if bl.zone == zone]

        locations = filter_locs(BlockDetailviewLocation.TOP)
        self.assertEqual(2, len(locations))
        self.assertEqual(1, self._find_location(brick_top_id1, locations).order)
        self.assertEqual(2, self._find_location(brick_top_id2, locations).order)

        locations = filter_locs(BlockDetailviewLocation.LEFT)
        self.assertEqual(2, len(locations))
        self.assertEqual(1, self._find_location(brick_left_id1, locations).order)
        self.assertEqual(2, self._find_location(brick_left_id2, locations).order)

        locations = filter_locs(BlockDetailviewLocation.RIGHT)
        self.assertEqual(1, len(locations))
        self.assertEqual(1, self._find_location(brick_right_id, locations).order)

        locations = filter_locs(BlockDetailviewLocation.BOTTOM)
        self.assertEqual(1, len(locations))
        self.assertEqual(1, self._find_location(brick_bottom_id, locations).order)

        self.assertEqual([''], [loc.block_id for loc in filter_locs(BlockDetailviewLocation.HAT)])

    def test_add_detailview01(self):
        self._aux_test_add_detailview(role=self.role, superuser=False)

    def test_add_detailview02(self):
        self._aux_test_add_detailview(role=None, superuser=True)

    def test_add_detailview03(self):
        "Used roles are not proposed anymore"
        model = FakeContact
        ct = ContentType.objects.get_for_model(model)
        url = self._build_adddetail_url(ct)

        role1 = self.role
        role2 = UserRole.objects.create(name='Viewer')

        def get_choices():
            response = self.assertGET200(url)

            with self.assertNoException():
                return list(response.context['form'].fields['role'].choices)

        choices = get_choices()
        self.assertIn(('', u'*%s*' % _(u'Superuser')), choices)
        self.assertIn((role1.id, role1.name), choices)
        self.assertIn((role2.id, role2.name), choices)

        # Role ------------
        bricks = list(self.brick_registry.get_compatible_bricks(model))
        self.assertGreaterEqual(len(bricks), 5, bricks)

        create_loc = partial(BlockDetailviewLocation.objects.create, content_type=ct, order=1)
        create_loc(role=role1, block_id=bricks[0].id_, zone=BlockDetailviewLocation.TOP)
        create_loc(role=role1, block_id=bricks[1].id_, zone=BlockDetailviewLocation.LEFT)
        create_loc(role=role1, block_id=bricks[2].id_, zone=BlockDetailviewLocation.RIGHT)
        create_loc(role=role1, block_id=bricks[3].id_, zone=BlockDetailviewLocation.BOTTOM)

        choices = get_choices()
        self.assertIn(('', u'*%s*' % _(u'Superuser')), choices)
        self.assertIn((role2.id, role2.name), choices)
        self.assertNotIn((role1.id, role1.name), choices)

        # Superuser ------------
        create_loc(superuser=True, block_id=bricks[0].id_, zone=BlockDetailviewLocation.TOP)
        create_loc(superuser=True, block_id=bricks[1].id_, zone=BlockDetailviewLocation.LEFT)
        create_loc(superuser=True, block_id=bricks[2].id_, zone=BlockDetailviewLocation.RIGHT)
        create_loc(superuser=True, block_id=bricks[3].id_, zone=BlockDetailviewLocation.BOTTOM)

        choices = get_choices()
        self.assertIn((role2.id, role2.name), choices)
        self.assertNotIn((role1.id, role1.name), choices)
        self.assertNotIn(('', u'*%s*' % _(u'Superuser')), choices)

    def test_add_detailview04(self):
        "Un-configurable models"
        get_ct = ContentType.objects.get_for_model

        build_url = self._build_adddetail_url
        self.assertGET404(build_url(get_ct(FakeAddress)))  # Not a CremeEntity

        model = FakeInvoiceLine
        self.assertIn(model, creme_registry.iter_entity_models())
        self.assertGET404(build_url(get_ct(model)))

    def test_add_detailview05(self):
        "Extra HatBrick"
        model = FakeContact
        ct = ContentType.objects.get_for_model(model)

        self.brick_registry.register_hat(model, secondary_brick_classes=[FakeContactHatBrick])

        url = self._build_adddetail_url(ct)
        response = self.assertGET200(url)

        with self.assertNoException():
            fields = response.context['form'].fields
            top_field = fields['top']
            hat_f = fields['hat']
            hat_choices = hat_f.choices

        self.assertEqual(2, len(hat_choices))

        generic_id = Brick.GENERIC_HAT_BRICK_ID
        self.assertEqual((generic_id, _(u'Title bar')), hat_choices[0])
        self.assertEqual((FakeContactHatBrick.id_, FakeContactHatBrick.verbose_name),
                         hat_choices[1]
                        )
        self.assertEqual(generic_id, hat_f.initial)

        brick_top_id = CompleteBrick1.id_
        brick_top_index = self._find_field_index(top_field, brick_top_id)
        response = self.client.post(url,
                                    data={'hat':                            FakeContactHatBrick.id_,

                                          'top_check_%s' % brick_top_index: 'on',
                                          'top_value_%s' % brick_top_index: brick_top_id,
                                          'top_order_%s' % brick_top_index: 1,
                                         },
                                   )
        self.assertNoFormError(response)

        b_locs = BlockDetailviewLocation.objects.filter(content_type=ct, role=None, superuser=True)
        filter_locs = lambda zone: [bl for bl in b_locs if bl.zone == zone]

        top_locations = filter_locs(BlockDetailviewLocation.TOP)
        self.assertEqual(1, len(top_locations))
        self.assertEqual(brick_top_id, top_locations[0].block_id)

        self.assertEqual([''], [loc.block_id for loc in filter_locs(BlockDetailviewLocation.LEFT)])
        self.assertEqual([''], [loc.block_id for loc in filter_locs(BlockDetailviewLocation.RIGHT)])
        self.assertEqual([''], [loc.block_id for loc in filter_locs(BlockDetailviewLocation.BOTTOM)])

        hat_locations = filter_locs(BlockDetailviewLocation.HAT)
        self.assertEqual(1, len(hat_locations))
        self.assertEqual(FakeContactHatBrick.id_, hat_locations[0].block_id)

    def _aux_test_edit_detailview(self, role=None, superuser=False):
        model = FakeContact
        ct = ContentType.objects.get_for_model(model)

        url = self._build_editdetail_url(ct, role, superuser)
        response = self.assertGET200(url)

        with self.assertNoException():
            fields = response.context['form'].fields
            top_field    = fields['top']
            left_field   = fields['left']
            right_field  = fields['right']
            bottom_field = fields['bottom']

        bricks = list(self.brick_registry.get_compatible_bricks(model))
        self.assertGreaterEqual(len(bricks), 5)
        self._find_field_index(top_field, CompleteBrick1.id_)
        self._assertNotInChoices(top_field, HomePortalBrick.id_,
                                 'Block has no detailview_display() method'
                                )

        brick_top_id1   = bricks[0].id_
        brick_top_id2   = bricks[1].id_
        # brick_left_id1  = MODELBLOCK_ID
        brick_left_id1  = self.brick_registry.get_brick_4_object(model).id_
        brick_left_id2  = bricks[2].id_
        brick_right_id  = bricks[3].id_
        brick_bottom_id = bricks[4].id_

        brick_top_index1   = self._find_field_index(top_field, brick_top_id1)
        brick_top_index2   = self._find_field_index(top_field, brick_top_id2)
        brick_left_index1  = self._find_field_index(left_field, brick_left_id1)
        brick_left_index2  = self._find_field_index(left_field, brick_left_id2)
        brick_right_index  = self._find_field_index(right_field, brick_right_id)
        brick_bottom_index = self._find_field_index(bottom_field, brick_bottom_id)

        response = self.client.post(url,
                                    data={'top_check_%s' % brick_top_index1: 'on',
                                          'top_value_%s' % brick_top_index1: brick_top_id1,
                                          'top_order_%s' % brick_top_index1: 1,

                                          'top_check_%s' % brick_top_index2: 'on',
                                          'top_value_%s' % brick_top_index2: brick_top_id2,
                                          'top_order_%s' % brick_top_index2: 2,

                                          'left_check_%s' % brick_left_index1: 'on',
                                          'left_value_%s' % brick_left_index1: brick_left_id1,
                                          'left_order_%s' % brick_left_index1: 1,

                                          'left_check_%s' % brick_left_index2: 'on',
                                          'left_value_%s' % brick_left_index2: brick_left_id2,
                                          'left_order_%s' % brick_left_index2: 2,

                                          'right_check_%s' % brick_right_index: 'on',
                                          'right_value_%s' % brick_right_index: brick_right_id,
                                          'right_order_%s' % brick_right_index: 1,

                                          'bottom_check_%s' % brick_bottom_index: 'on',
                                          'bottom_value_%s' % brick_bottom_index: brick_bottom_id,
                                          'bottom_order_%s' % brick_bottom_index: 1,
                                         }
                                   )
        self.assertNoFormError(response)

        b_locs = BlockDetailviewLocation.objects.filter(content_type=ct, role=role,
                                                        superuser=superuser,
                                                       )
        filter_locs = lambda zone: [bl for bl in b_locs if bl.zone == zone]

        locations = filter_locs(BlockDetailviewLocation.TOP)
        self.assertEqual(2, len(locations))
        self.assertEqual(1, self._find_location(brick_top_id1, locations).order)
        self.assertEqual(2, self._find_location(brick_top_id2, locations).order)

        locations = filter_locs(BlockDetailviewLocation.LEFT)
        self.assertEqual(2, len(locations))
        self.assertEqual(1, self._find_location(brick_left_id1, locations).order)
        self.assertEqual(2, self._find_location(brick_left_id2, locations).order)

        locations = filter_locs(BlockDetailviewLocation.RIGHT)
        self.assertEqual(1, len(locations))
        self.assertEqual(1, self._find_location(brick_right_id, locations).order)

        locations = filter_locs(BlockDetailviewLocation.BOTTOM)
        self.assertEqual(1, len(locations))
        self.assertEqual(1, self._find_location(brick_bottom_id, locations).order)

        self.assertEqual([''], [loc.block_id for loc in filter_locs(BlockDetailviewLocation.HAT)])

    def test_edit_detailview01(self):
        "Default configuration of a ContentType"
        model = FakeContact
        ct = ContentType.objects.get_for_model(model)
        brick_id = list(self.brick_registry.get_compatible_bricks(model))[0].id_

        # These bricks should not be modified
        create_loc = partial(BlockDetailviewLocation.objects.create,
                             content_type=ct, order=1, block_id=brick_id,
                             zone=BlockDetailviewLocation.TOP,
                            )
        b_loc1 = create_loc(role=self.role)
        b_loc2 = create_loc(superuser=True)

        self._aux_test_edit_detailview(role=None, superuser=False)

        b_loc1 = self.refresh(b_loc1)
        self.assertEqual(self.role, b_loc1.role)
        self.assertEqual(brick_id, b_loc1.block_id)

        b_loc2 = self.refresh(b_loc2)
        self.assertTrue(b_loc2.superuser)
        self.assertEqual(brick_id, b_loc2.block_id)

    def test_edit_detailview02(self):
        "Configuration for a role"
        self._aux_test_edit_detailview(role=self.role, superuser=False)

    def test_edit_detailview03(self):
        "Configuration for superusers"
        self._aux_test_edit_detailview(role=None, superuser=True)

    def test_edit_detailview04(self):
        "When no block -> fake block"
        model = FakeContact
        ct = ContentType.objects.get_for_model(model)

        bricks = list(self.brick_registry.get_compatible_bricks(model))
        self.assertGreaterEqual(len(bricks), 5, bricks)

        create_loc = partial(BlockDetailviewLocation.objects.create, content_type=ct, order=1)
        create_loc(block_id=bricks[0].id_, zone=BlockDetailviewLocation.TOP)
        create_loc(block_id=bricks[1].id_, zone=BlockDetailviewLocation.LEFT)
        create_loc(block_id=bricks[2].id_, zone=BlockDetailviewLocation.RIGHT)
        create_loc(block_id=bricks[3].id_, zone=BlockDetailviewLocation.BOTTOM)

        url = self._build_editdetail_url(ct)
        response = self.assertGET200(url)

        with self.assertNoException():
            fields = response.context['form'].fields
            top_field    = fields['top']
            left_field   = fields['left']
            right_field  = fields['right']
            bottom_field = fields['bottom']

        brick_top_id1 = bricks[0].id_
        brick_top_id2 = bricks[1].id_

        self.assertEqual([brick_top_id1], top_field.initial)
        self.assertEqual([brick_top_id2], left_field.initial)
        self.assertEqual([bricks[2].id_], right_field.initial)
        self.assertEqual([bricks[3].id_], bottom_field.initial)

        brick_top_index1 = self._find_field_index(top_field, brick_top_id1)
        brick_top_index2 = self._find_field_index(top_field, brick_top_id2)

        response = self.client.post(url,
                                    data={'top_check_%s' % brick_top_index1: 'on',
                                          'top_value_%s' % brick_top_index1: brick_top_id1,
                                          'top_order_%s' % brick_top_index1: 1,

                                          'top_check_%s' % brick_top_index2: 'on',
                                          'top_value_%s' % brick_top_index2: brick_top_id2,
                                          'top_order_%s' % brick_top_index2: 2,
                                         }
                                   )
        self.assertNoFormError(response)

        b_locs = BlockDetailviewLocation.objects.filter(content_type=ct)
        locations = [b_loc for b_loc in b_locs if b_loc.zone == BlockDetailviewLocation.TOP]
        self.assertEqual(2, len(locations))
        self.assertEqual(1, self._find_location(brick_top_id1, locations).order)
        self.assertEqual(2, self._find_location(brick_top_id2, locations).order)

        bricks_info = lambda zone: [(bl.block_id, bl.order) for bl in b_locs if bl.zone == zone]

        self.assertEqual([('', 1)], bricks_info(BlockDetailviewLocation.LEFT))
        self.assertEqual([('', 1)], bricks_info(BlockDetailviewLocation.RIGHT))
        self.assertEqual([('', 1)], bricks_info(BlockDetailviewLocation.BOTTOM))

    def test_edit_detailview05(self):
        "Default conf + no empty configuration"
#        BlockDetailviewLocation.objects.filter(content_type=None).delete()

        self.assertGET404(self._build_editdetail_url(ct=None, role=self.role))

        url = self._build_editdetail_url(ct=None)
        self.assertGET200(url)

        response = self.assertPOST200(url, data={})
        self.assertFormError(response, 'form', None,
                             _(u'Your configuration is empty !')
                            )

        bricks = list(self.brick_registry.get_compatible_bricks(None))
        self.assertGreaterEqual(len(bricks), 1, bricks)
        brick_id = bricks[0].id_

        with self.assertNoException():
            top_field = response.context['form'].fields['top']

        index = self._find_field_index(top_field, brick_id)
        response = self.client.post(url,
                                    data={'top_check_%s' % index: 'on',
                                          'top_value_%s' % index: brick_id,
                                          'top_order_%s' % index: 1,
                                         }
                                   )
        self.assertNoFormError(response)

        b_locs = BlockDetailviewLocation.objects.filter(content_type=None)
        bricks_info = lambda zone: [(bl.block_id, bl.order) for bl in b_locs if bl.zone == zone]

        self.assertEqual([(brick_id, 1)], bricks_info(BlockDetailviewLocation.TOP))
        self.assertEqual([('', 1)], bricks_info(BlockDetailviewLocation.LEFT))
        self.assertEqual([('', 1)], bricks_info(BlockDetailviewLocation.RIGHT))
        self.assertEqual([('', 1)], bricks_info(BlockDetailviewLocation.BOTTOM))

    def test_edit_detailview06(self):
        "Post one block several times -> validation error"
        model = FakeContact
        ct = ContentType.objects.get_for_model(model)

        url = self._build_editdetail_url(ct)
        response = self.assertGET200(url)

        with self.assertNoException():
            fields = response.context['form'].fields
            left_field  = fields['left']
            right_field = fields['right']

        bricks = list(self.brick_registry.get_compatible_bricks(model))
        self.assertTrue(bricks)

        def post(brick_id, brick_vname):
            brick_left_id = block_right_id = brick_id  # <= same block !!
            brick_left_index  = self._find_field_index(left_field,  brick_left_id)
            brick_right_index = self._find_field_index(right_field, block_right_id)

            response = self.client.post(url,
                                        data={'right_check_%s' % brick_right_index: 'on',
                                              'right_value_%s' % brick_right_index: block_right_id,
                                              'right_order_%s' % brick_right_index: 1,

                                              'left_check_%s' % brick_left_index: 'on',
                                              'left_value_%s' % brick_left_index: brick_left_id,
                                              'left_order_%s' % brick_left_index: 1,
                                             }
                                       )
            self.assertFormError(response, 'form', field=None,
                                 errors=_(u'The following block should be displayed only once: «%(block)s»') % {
                                                'block': brick_vname,
                                            }
                                )

        modelbrick_id = self.brick_registry.get_brick_4_object(model).id_

        with self.assertNoException():
            # evil_brick = (b for b in bricks if b.id_ != MODELBLOCK_ID).next()
            evil_brick = (b for b in bricks if not b.id_ != modelbrick_id).next()

        post(evil_brick.id_, evil_brick.verbose_name)
        # post(MODELBLOCK_ID, _(u'Information on the entity'))
        post(modelbrick_id, _(u'Information on the entity (generic)'))

    def test_edit_detailview07(self):
        "Instance block, RelationType brick"
        model = FakeContact
        ct = ContentType.objects.get_for_model(model)

        rtype = RelationType.objects.all()[0]
        rtype_brick_id = SpecificRelationsBrick.generate_id('test', 'foobar')
        RelationBlockItem.objects.create(block_id=rtype_brick_id, relation_type=rtype)

        naru = FakeContact.objects.create(user=self.user, first_name='Naru', last_name='Narusegawa')

        instance_brick_id = InstanceBlockConfigItem.generate_id(DetailviewInstanceBrick, naru, '')
        InstanceBlockConfigItem.objects.create(block_id=instance_brick_id,
                                               entity=naru, verbose='All stuffes',
                                              )

        response = self.assertGET200(self._build_editdetail_url(ct))

        with self.assertNoException():
            top_field = response.context['form'].fields['top']

        choices = [brick_id for brick_id, block_name in top_field.choices]
        self.assertIn(rtype_brick_id,    choices)
        self.assertIn(instance_brick_id, choices)

    def test_edit_detailview08(self):
        "Invalid models"
        build_url = self._build_editdetail_url
        get_ct = ContentType.objects.get_for_model
        self.assertGET404(build_url(get_ct(FakeAddress)))
        self.assertGET404(build_url(get_ct(FakeInvoiceLine)))

    def test_edit_detailview09(self):
        "Extra HatBrick"
        model = FakeContact
        ct = ContentType.objects.get_for_model(model)

        self.brick_registry.register_hat(model, secondary_brick_classes=[FakeContactHatBrick])

        url = self._build_editdetail_url(ct)
        response = self.assertGET200(url)

        with self.assertNoException():
            fields = response.context['form'].fields
            top_field = fields['top']
            hat_f = fields['hat']
            hat_choices = hat_f.choices

        generic_id = Brick.GENERIC_HAT_BRICK_ID
        self.assertEqual(2, len(hat_choices))
        self.assertEqual((generic_id, _(u'Title bar')), hat_choices[0])
        self.assertEqual((FakeContactHatBrick.id_, FakeContactHatBrick.verbose_name),
                         hat_choices[1]
                        )
        self.assertEqual(generic_id, hat_f.initial)

        brick_top_id = CompleteBrick1.id_
        brick_top_index = self._find_field_index(top_field, brick_top_id)
        response = self.client.post(url,
                                    data={'hat':                            FakeContactHatBrick.id_,

                                          'top_check_%s' % brick_top_index: 'on',
                                          'top_value_%s' % brick_top_index: brick_top_id,
                                          'top_order_%s' % brick_top_index: 1,
                                         },
                                   )
        self.assertNoFormError(response)

        b_locs = BlockDetailviewLocation.objects.filter(content_type=ct)
        filter_locs = lambda zone: [bl for bl in b_locs if bl.zone == zone]

        top_locations = filter_locs(BlockDetailviewLocation.TOP)
        self.assertEqual(1, len(top_locations))
        self.assertEqual(brick_top_id, top_locations[0].block_id)

        self.assertEqual([''], [loc.block_id for loc in filter_locs(BlockDetailviewLocation.LEFT)])
        self.assertEqual([''], [loc.block_id for loc in filter_locs(BlockDetailviewLocation.RIGHT)])
        self.assertEqual([''], [loc.block_id for loc in filter_locs(BlockDetailviewLocation.BOTTOM)])

        hat_locations = filter_locs(BlockDetailviewLocation.HAT)
        self.assertEqual(1, len(hat_locations))
        self.assertEqual(FakeContactHatBrick.id_, hat_locations[0].block_id)

        # -----------
        response = self.assertGET200(url)

        with self.assertNoException():
            hat_f = response.context['form'].fields['hat']

        self.assertEqual(FakeContactHatBrick.id_, hat_f.initial)

    def test_delete_detailview01(self):
        "Can not delete default conf"
        self.assertPOST404(self.DEL_DETAIL_URL, data={'id': 0})

    def test_delete_detailview02(self):
        "Default ContentType configuration"
        get_ct = ContentType.objects.get_for_model
        ct = get_ct(FakeContact)

        create_bdl = partial(BlockDetailviewLocation.objects.create, order=1,
                             content_type=ct, zone=BlockDetailviewLocation.TOP,
                            )
        locs = [create_bdl(block_id=RelationsBrick.id_),
                create_bdl(zone=BlockDetailviewLocation.LEFT, block_id=PropertiesBrick.id_),
                create_bdl(zone=BlockDetailviewLocation.RIGHT, block_id=CustomFieldsBrick.id_),
                create_bdl(zone=BlockDetailviewLocation.BOTTOM, block_id=HistoryBrick.id_),
               ]

        locs_2 = [create_bdl(block_id=RelationsBrick.id_, role=self.role),
                  create_bdl(block_id=RelationsBrick.id_, superuser=True),
                  create_bdl(block_id=RelationsBrick.id_, content_type=get_ct(FakeOrganisation)),
                 ]

        self.assertPOST200(self.DEL_DETAIL_URL, data={'id': ct.id})
        self.assertFalse(BlockDetailviewLocation.objects.filter(id__in=[l.id for l in locs]))
        self.assertEqual(len(locs_2),
                         BlockDetailviewLocation.objects.filter(id__in=[l.id for l in locs_2])
                                                        .count()
                        )

    def test_delete_detailview03(self):
        "Role configuration"
        get_ct = ContentType.objects.get_for_model
        ct = get_ct(FakeContact)
        role = self.role

        create_bdl = partial(BlockDetailviewLocation.objects.create, order=1,
                             content_type=ct, zone=BlockDetailviewLocation.TOP,
                             role=role,
                            )
        locs = [create_bdl(block_id=RelationsBrick.id_),
                create_bdl(zone=BlockDetailviewLocation.LEFT, block_id=PropertiesBrick.id_),
                create_bdl(zone=BlockDetailviewLocation.RIGHT, block_id=CustomFieldsBrick.id_),
                create_bdl(zone=BlockDetailviewLocation.BOTTOM, block_id=HistoryBrick.id_),
               ]

        locs_2 = [create_bdl(block_id=RelationsBrick.id_, role=None),
                  create_bdl(block_id=RelationsBrick.id_, superuser=True),
                  create_bdl(block_id=RelationsBrick.id_, content_type=get_ct(FakeOrganisation)),
                 ]

        self.assertPOST200(self.DEL_DETAIL_URL, data={'id': ct.id, 'role': role.id})
        self.assertFalse(BlockDetailviewLocation.objects.filter(id__in=[l.id for l in locs]))
        self.assertEqual(len(locs_2),
                         BlockDetailviewLocation.objects.filter(id__in=[l.id for l in locs_2])
                                                        .count()
                        )

    def test_delete_detailview04(self):
        "Superuser configuration"
        get_ct = ContentType.objects.get_for_model
        ct = get_ct(FakeOrganisation)

        create_bdl = partial(BlockDetailviewLocation.objects.create, order=1,
                             content_type=ct, zone=BlockDetailviewLocation.TOP,
                             superuser=True,
                            )
        locs = [create_bdl(block_id=RelationsBrick.id_),
                create_bdl(zone=BlockDetailviewLocation.LEFT, block_id=PropertiesBrick.id_),
                create_bdl(zone=BlockDetailviewLocation.RIGHT, block_id=CustomFieldsBrick.id_),
                create_bdl(zone=BlockDetailviewLocation.BOTTOM, block_id=HistoryBrick.id_),
               ]

        locs_2 = [create_bdl(block_id=RelationsBrick.id_, role=self.role),
                  create_bdl(block_id=RelationsBrick.id_, superuser=False),
                  create_bdl(block_id=RelationsBrick.id_, content_type=get_ct(FakeContact)),
                 ]

        self.assertPOST200(self.DEL_DETAIL_URL, data={'id': ct.id, 'role': 'superuser'})
        self.assertFalse(BlockDetailviewLocation.objects.filter(id__in=[l.id for l in locs]))
        self.assertEqual(len(locs_2),
                         BlockDetailviewLocation.objects.filter(id__in=[l.id for l in locs_2])
                                                        .count()
                        )

    def test_add_portal(self):
        # url = '/creme_config/blocks/portal/add/'
        url = reverse('creme_config__create_portal_bricks_legacy')
        self.assertGET200(url)

        app_name = 'persons'
        self.assertFalse(BlockPortalLocation.objects.filter(app_name=app_name))

        self.assertNoFormError(self.client.post(url, data={'app_name': app_name}))

        b_locs = list(BlockPortalLocation.objects.filter(app_name=app_name))
        self.assertEqual(1, len(b_locs))

        bpl = b_locs[-1]
        self.assertEqual(1,  bpl.order)
        self.assertEqual('', bpl.block_id)

        response = self.client.get(url)

        with self.assertNoException():
            choices = response.context['form'].fields['app_name'].choices

        names = {name for name, vname in choices}
        self.assertNotIn(app_name,       names)
        self.assertNotIn('creme_core',   names)
        self.assertNotIn('creme_config', names)

    def test_edit_portal01(self):
        # self.assertGET404('/creme_config/blocks/portal/edit/persons')
        self.assertGET404(reverse('creme_config__edit_portal_bricks', args=('persons',)))

    def test_edit_portal02(self):
        app_name = 'persons'

        naru = FakeContact.objects.create(user=self.user, first_name='Naru', last_name='Narusegawa')

        instance_brick_id = InstanceBlockConfigItem.generate_id(PortalInstanceBrick, naru, '')
        InstanceBlockConfigItem.objects.create(block_id=instance_brick_id, entity=naru, verbose='All stuffes')

        brick1 = PortalOnlyBrick1
        brick2 = PortalOnlyBrick2; assert not brick2.configurable
        brick3 = PortalOnlyBrick3; assert app_name in brick3.target_apps
        brick4 = PortalOnlyBrick4; assert app_name not in brick4.target_apps

        # self.client.post('/creme_config/blocks/portal/add/', data={'app_name': app_name})
        self.client.post(reverse('creme_config__create_portal_bricks_legacy'), data={'app_name': app_name})
        self.assertEqual(1, BlockPortalLocation.objects.filter(app_name=app_name).count())

        # url = '/creme_config/blocks/portal/edit/%s' % app_name
        url = reverse('creme_config__edit_portal_bricks', args=(app_name,))
        response = self.assertGET200(url)

        with self.assertNoException():
            blocks_field = response.context['form'].fields['blocks']

        choices = blocks_field.choices
        self.assertGreaterEqual(len(choices), 2)
        self._find_field_index(blocks_field, brick1.id_)
        self._assertNotInChoices(blocks_field, brick2.id_, 'Block is not configurable')
        self._find_field_index(blocks_field, brick3.id_)
        self._assertNotInChoices(blocks_field, brick4.id_, 'Block is not compatible with this app')
        self._find_field_index(blocks_field, instance_brick_id)

        brick_id1 = choices[0][0]
        brick_id2 = choices[1][0]

        index1 = self._find_field_index(blocks_field, brick_id1)
        index2 = self._find_field_index(blocks_field, brick_id2)

        response = self.client.post(url, data={'blocks_check_%s' % index1: 'on',
                                               'blocks_value_%s' % index1: brick_id1,
                                               'blocks_order_%s' % index1: 1,

                                               'blocks_check_%s' % index2: 'on',
                                               'blocks_value_%s' % index2: brick_id2,
                                               'blocks_order_%s' % index2: 2,
                                              }
                                   )
        self.assertNoFormError(response)

        b_locs = list(BlockPortalLocation.objects.filter(app_name=app_name))
        self.assertEqual(2, len(b_locs))
        self.assertEqual(1, self._find_location(brick_id1, b_locs).order)
        self.assertEqual(2, self._find_location(brick_id2, b_locs).order)

    def _get_blocks_4_portal(self):
        bricks = [block for block_id, block in self.brick_registry
                            if hasattr(block, 'portal_display')
                 ]
        self.assertGreaterEqual(len(bricks), 2, bricks)

        return bricks

    def test_edit_portal03(self):
        "Set no block -> fake blocks"
        app_name = 'persons'
        blocks = self._get_blocks_4_portal()

        create_loc = partial(BlockPortalLocation.objects.create, app_name=app_name)
        create_loc(block_id=blocks[0].id_, order=1)
        create_loc(block_id=blocks[1].id_, order=2)

        # url = '/creme_config/blocks/portal/edit/%s' % app_name
        url = reverse('creme_config__edit_portal_bricks', args=(app_name,))
        response = self.assertGET200(url)

        with self.assertNoException():
            blocks_field = response.context['form'].fields['blocks']

        self.assertEqual([blocks[0].id_, blocks[1].id_], blocks_field.initial)

        self.assertNoFormError(self.client.post(url, data={}))

        b_locs = list(BlockPortalLocation.objects.filter(app_name=app_name))
        self.assertEqual(1, len(b_locs))

        bpl = b_locs[0]
        self.assertEqual(1,  bpl.order)
        self.assertEqual('', bpl.block_id)

    def test_edit_portal04(self):
        "Default conf"
        BlockPortalLocation.objects.filter(app_name='').delete()
        # url = '/creme_config/blocks/portal/edit/default'
        url = reverse('creme_config__edit_portal_bricks', args=('default',))
        self.assertGET404(url)

        bricks = self._get_blocks_4_portal()
        create_loc = partial(BlockPortalLocation.objects.create, app_name='')
        create_loc(block_id=bricks[0].id_, order=1)
        create_loc(block_id=bricks[1].id_, order=2)

        self.assertGET200(url)

        self.assertNoFormError(self.client.post(url, data={}))

        b_locs = list(BlockPortalLocation.objects.filter(app_name=''))
        self.assertEqual(1, len(b_locs))

        bpl = b_locs[0]
        self.assertEqual(1,  bpl.order)
        self.assertEqual('', bpl.block_id)

    def test_edit_portal05(self):
        "Home -> use 'home_display' method"
        app_name = 'creme_core'

        BlockPortalLocation.create(block_id=HistoryBrick.id_, order=8, app_name=app_name)

        brick = HomeOnlyBrick

        # response = self.assertGET200('/creme_config/blocks/portal/edit/%s' % app_name)
        response = self.assertGET200(reverse('creme_config__edit_portal_bricks', args=(app_name,)))

        with self.assertNoException():
            blocks_field = response.context['form'].fields['blocks']

        self._find_field_index(blocks_field, brick.id_)

    def test_edit_portal06(self):
        "Edit portal of unknown app"
        app_name = 'unknown'
        self.assertFalse(BlockPortalLocation.objects.filter(app_name=app_name).exists())
        # self.assertGET404('/creme_config/blocks/portal/edit/%s' % app_name)
        self.assertGET404(reverse('creme_config__edit_portal_bricks', args=(app_name,)))

    def test_delete_portal(self):
        app_name = 'persons'
        # self.client.post('/creme_config/blocks/portal/add/', data={'app_name': app_name})
        self.client.post(reverse('creme_config__create_portal_bricks_legacy'), data={'app_name': app_name})

        # self.assertPOST200('/creme_config/blocks/portal/delete', data={'id': app_name})
        self.assertPOST200(reverse('creme_config__delete_portal_bricks'), data={'id': app_name})
        self.assertFalse(BlockPortalLocation.objects.filter(app_name=app_name))

    @skipIfNotInstalled('creme.persons')
    def test_portal_wizard_appname_step(self):
        app_name = 'persons'
        self.assertFalse(BlockPortalLocation.objects.filter(app_name=app_name))

        response = self.assertGET200(self.PORTAL_WIZARD_URL)
        self.assertIn(app_name, [e[0] for e in response.context['form'].fields['app_name'].choices])

        response = self.assertPOST200(self.PORTAL_WIZARD_URL,
                                      {'portal_bricks_wizard-current_step': '0',
                                       '0-app_name': app_name,
                                      }
                                     )

        brick_ids = [e[0] for e in response.context['form'].fields['blocks'].choices]
        self.assertIn('block_creme_core-history', brick_ids)

        # last step is not submitted so nothing yet in database
        self.assertFalse(BlockPortalLocation.objects.filter(app_name=app_name))

    def test_portal_wizard_appname_step_invalid(self):
        response = self.assertPOST200(self.PORTAL_WIZARD_URL,
                                      {'portal_bricks_wizard-current_step': '0',
                                       '0-app_name': 'unregistered_app',
                                      }
                                     )

        self.assertFormError(response, 'form', 'app_name',
                             _(u'Select a valid choice. %(value)s is not one of the available choices.') % {
                                    'value': 'unregistered_app',
                                }
                            )

    @skipIfNotInstalled('creme.persons')
    def test_portal_wizard_config_step(self):
        app_name = 'persons'
        self.assertFalse(BlockPortalLocation.objects.filter(app_name=app_name))

        response = self.assertGET200(self.PORTAL_WIZARD_URL)
        self.assertIn(app_name, [e[0] for e in response.context['form'].fields['app_name'].choices])

        response = self.assertPOST200(self.PORTAL_WIZARD_URL,
                                      {'portal_bricks_wizard-current_step': '0',
                                       '0-app_name': app_name,
                                      }
                                     )

        brick_field = response.context['form'].fields['blocks']
        brick_ids = [e[0] for e in brick_field.choices]
        self.assertIn('block_creme_core-history', brick_ids)

        history_brick_index = self._find_field_index(brick_field, 'block_creme_core-history')

        response = self.assertPOST200(self.PORTAL_WIZARD_URL,
                                      {'portal_bricks_wizard-current_step': '1',
                                       '1-blocks_check_%s' % history_brick_index: 'on',
                                       '1-blocks_value_%s' % history_brick_index: 'block_creme_core-history',
                                       '1-blocks_order_%s' % history_brick_index: 1,
                                      }
                                     )
        self.assertNoFormError(response)

        blocks = list(BlockPortalLocation.objects.filter(app_name=app_name)
                                                 .order_by('order')
                                                 .values_list('block_id', 'order')
                     )
        self.assertEqual([('block_creme_core-history', 1)], blocks)

    @skipIfNotInstalled('creme.assistants')
    def test_portal_wizard_config_step_assistants(self):
        app_name = 'assistants'
        self.assertFalse(BlockPortalLocation.objects.filter(app_name=app_name))

        response = self.assertGET200(self.PORTAL_WIZARD_URL)
        self.assertIn(app_name, [e[0] for e in response.context['form'].fields['app_name'].choices])

        response = self.assertPOST200(self.PORTAL_WIZARD_URL,
                                      {'portal_bricks_wizard-current_step': '0',
                                       '0-app_name': app_name,
                                      }
                                     )

        brick_field = response.context['form'].fields['blocks']
        brick_ids = [e[0] for e in brick_field.choices]

        self.assertIn('block_assistants-memos', brick_ids)
        self.assertIn('block_assistants-messages', brick_ids)
        self.assertIn('block_creme_core-history', brick_ids)

        history_brick_index = self._find_field_index(brick_field, 'block_creme_core-history')
        memos_brick_index = self._find_field_index(brick_field, 'block_assistants-memos')
        messages_brick_index = self._find_field_index(brick_field, 'block_assistants-messages')

        response = self.assertPOST200(self.PORTAL_WIZARD_URL,
                                      {'portal_bricks_wizard-current_step': '1',
                                       '1-blocks_check_%s' % history_brick_index: 'on',
                                       '1-blocks_value_%s' % history_brick_index: 'block_creme_core-history',
                                       '1-blocks_order_%s' % history_brick_index: 1,
                                       '1-blocks_check_%s' % memos_brick_index: 'on',
                                       '1-blocks_value_%s' % memos_brick_index: 'block_assistants-memos',
                                       '1-blocks_order_%s' % memos_brick_index: 2,
                                       '1-blocks_check_%s' % messages_brick_index: 'on',
                                       '1-blocks_value_%s' % messages_brick_index: 'block_assistants-messages',
                                       '1-blocks_order_%s' % messages_brick_index: 3,
                                      }
                                     )
        self.assertNoFormError(response)

        self.assertListEqual([('block_creme_core-history', 1),
                              ('block_assistants-memos', 2),
                              ('block_assistants-messages', 3),
                             ],
                             list(BlockPortalLocation.objects.filter(app_name=app_name)
                                                             .order_by('order')
                                                             .values_list('block_id', 'order')
                                 )
                            )

    @skipIfNotInstalled('creme.persons')
    def test_portal_wizard_go_back(self):
        app_name = 'persons'
        self.assertFalse(BlockPortalLocation.objects.filter(app_name=app_name))

        response = self.assertGET200(self.PORTAL_WIZARD_URL)
        self.assertIn(app_name, [e[0] for e in response.context['form'].fields['app_name'].choices])

        response = self.assertPOST200(self.PORTAL_WIZARD_URL,
                                      {'portal_bricks_wizard-current_step': '0',
                                       '0-app_name': app_name,
                                      }
                                     )

        brick_ids = [e[0] for e in response.context['form'].fields['blocks'].choices]
        self.assertIn('block_creme_core-history', brick_ids)

        # Return to first step
        response = self.assertPOST200(self.PORTAL_WIZARD_URL,
                                      {'portal_bricks_wizard-current_step': '1',
                                       'wizard_goto_step': '0',
                                      }
                                     )
        self.assertIn(app_name, [e[0] for e in response.context['form'].fields['app_name'].choices])

    def test_delete_home(self):
        "Can not delete home conf"
        # TODO: use a helper method ??
        app_name = 'creme_core'
        bricks = [block for block_id, block in self.brick_registry
                            if hasattr(block, 'home_display')
                 ]
        self.assertGreaterEqual(len(bricks), 1)

        BlockPortalLocation.objects.create(app_name=app_name, block_id=bricks[0].id_, order=1)
        # self.assertPOST404('/creme_config/blocks/portal/delete', data={'id': app_name})
        self.assertPOST404(reverse('creme_config__delete_portal_bricks'), data={'id': app_name})

    def test_delete_home_location_item(self):
        app_name = 'creme_core'
        blocks = [block for block_id, block in self.brick_registry
                            if hasattr(block, 'home_display')
                 ]
        self.assertGreaterEqual(len(blocks), 1)

        bpl = BlockPortalLocation.objects.create(app_name=app_name, block_id=blocks[0].id_, order=1)
        # self.assertPOST200('/creme_config/blocks/home/delete', data={'id': bpl.id})
        self.assertPOST200(reverse('creme_config__delete_home_brick'), data={'id': bpl.id})
        self.assertDoesNotExist(bpl)

    def test_edit_default_mypage(self):
        # url = '/creme_config/blocks/mypage/edit/default'
        url = reverse('creme_config__edit_default_mypage_bricks')
        response = self.assertGET200(url)

        with self.assertNoException():
            bricks_field = response.context['form'].fields['blocks']

        choices = bricks_field.choices
        self.assertGreaterEqual(len(choices), 2)
        self.assertEqual(list(BlockMypageLocation.objects.filter(user=None).values_list('block_id', flat=True)),
                         bricks_field.initial
                        )

        block_id1 = choices[0][0]
        block_id2 = choices[1][0]

        index1 = self._find_field_index(bricks_field, block_id1)
        index2 = self._find_field_index(bricks_field, block_id2)

        response = self.client.post(url,
                                    data={'blocks_check_%s' % index1: 'on',
                                          'blocks_value_%s' % index1: block_id1,
                                          'blocks_order_%s' % index1: 1,

                                          'blocks_check_%s' % index2: 'on',
                                          'blocks_value_%s' % index2: block_id2,
                                          'blocks_order_%s' % index2: 2,
                                         }
                                   )
        self.assertNoFormError(response)

        b_locs = list(BlockMypageLocation.objects.filter(user=None))
        self.assertEqual(2, len(b_locs))
        self.assertEqual(1, self._find_location(block_id1, b_locs).order)
        self.assertEqual(2, self._find_location(block_id2, b_locs).order)

    def test_edit_mypage(self):
        user = self.user
        # url = '/creme_config/blocks/mypage/edit'
        url = reverse('creme_config__edit_mypage_bricks')
        response = self.assertGET200(url)

        with self.assertNoException():
            blocks_field = response.context['form'].fields['blocks']

        choices = blocks_field.choices
        self.assertGreaterEqual(len(choices), 2)
        self.assertEqual(list(BlockMypageLocation.objects.filter(user=None).values_list('block_id', flat=True)),
                         blocks_field.initial
                        )

        brick_id1 = choices[0][0]
        brick_id2 = choices[1][0]

        index1 = self._find_field_index(blocks_field, brick_id1)
        index2 = self._find_field_index(blocks_field, brick_id2)

        response = self.client.post(url,
                                    data={'blocks_check_%s' % index1: 'on',
                                          'blocks_value_%s' % index1: brick_id1,
                                          'blocks_order_%s' % index1: 1,

                                          'blocks_check_%s' % index2: 'on',
                                          'blocks_value_%s' % index2: brick_id2,
                                          'blocks_order_%s' % index2: 2,
                                         }
                                   )
        self.assertNoFormError(response)

        b_locs = list(BlockMypageLocation.objects.filter(user=user))
        self.assertEqual(2, len(b_locs))
        self.assertEqual(1, self._find_location(brick_id1, b_locs).order)
        self.assertEqual(2, self._find_location(brick_id2, b_locs).order)

    def test_delete_default_mypage01(self):
        loc = BlockMypageLocation.objects.create(user=None, block_id=HistoryBrick.id_, order=1)
        # self.assertPOST200('/creme_config/blocks/mypage/default/delete', data={'id': loc.id})
        self.assertPOST200(reverse('creme_config__delete_default_mypage_bricks'), data={'id': loc.id})
        self.assertDoesNotExist(loc)

    def test_delete_default_mypage02(self):
        "'user' must be 'None'"
        loc = BlockMypageLocation.objects.create(user=self.user, block_id=HistoryBrick.id_, order=1)
        # self.assertPOST404('/creme_config/blocks/mypage/default/delete', data={'id': loc.id})
        self.assertPOST404(reverse('creme_config__delete_default_mypage_bricks'), data={'id': loc.id})
        self.assertStillExists(loc)

    def test_delete_mypage01(self):
        loc = BlockMypageLocation.objects.create(user=self.user, block_id=HistoryBrick.id_, order=1)
        # self.assertPOST200('/creme_config/blocks/mypage/delete', data={'id': loc.id})
        self.assertPOST200(reverse('creme_config__delete_mypage_bricks'), data={'id': loc.id})
        self.assertDoesNotExist(loc)

    def test_delete_mypage02(self):
        "BlockMypageLocation must belong to the user"
        loc = BlockMypageLocation.objects.create(user=self.other_user, block_id=HistoryBrick.id_, order=1)
        # self.assertPOST404('/creme_config/blocks/mypage/delete', data={'id': loc.id})
        self.assertPOST404(reverse('creme_config__delete_mypage_bricks'), data={'id': loc.id})
        self.assertStillExists(loc)

    def test_add_relationbrick(self):
        rt = RelationType.create(('test-subfoo', 'subject_predicate'),
                                 ('test-objfoo', 'object_predicate'),
                                )[0]
        self.assertFalse(RelationBlockItem.objects.filter(relation_type=rt).exists())

        # url = '/creme_config/blocks/relation_block/add/'
        url = reverse('creme_config__create_rtype_brick')
        self.assertGET200(url)

        self.assertNoFormError(self.client.post(url, data={'relation_type': rt.id}))

        rb_items = RelationBlockItem.objects.all()
        self.assertEqual(1, len(rb_items))

        rb_item = rb_items[0]
        self.assertEqual(rt.id, rb_item.relation_type.id)
        self.assertEqual('specificblock_creme_config-test-subfoo', rb_item.block_id)
        self.assertIsNone(rb_item.get_cells(ContentType.objects.get_for_model(FakeContact)))

    def test_add_relationbrick_ctypes01(self):
        rt = RelationType.create(('test-subfoo', 'subject_predicate'),
                                 ('test-objfoo', 'object_predicate', [FakeContact, FakeOrganisation, FakeActivity]),
                                )[0]

        rb_item = RelationBlockItem.objects.create(
                        block_id='specificblock_creme_config-test-subfoo',
                        relation_type=rt,
                    )

        url = self._build_rbrick_addctypes_url(rb_item)
        response = self.assertGET200(url)

        with self.assertNoException():
            choices = response.context['form'].fields['ctypes'].ctypes

        get_ct = ContentType.objects.get_for_model
        self.assertIn(get_ct(FakeContact), choices)
        self.assertIn(get_ct(FakeOrganisation), choices)
        self.assertIn(get_ct(FakeActivity), choices)
        self.assertNotIn(get_ct(FakeImage), choices)

        self.assertNoFormError(self.client.post(
            url,
            data={'ctypes': [get_ct(m).id for m in (FakeContact, FakeOrganisation)]},
        ))

        rb_item = self.refresh(rb_item)
        self.assertIsNone(rb_item.get_cells(get_ct(FakeActivity)))
        self.assertEqual([], rb_item.get_cells(get_ct(FakeContact)))
        self.assertEqual([], rb_item.get_cells(get_ct(FakeOrganisation)))

        # Used CTypes should not be proposed
        response = self.assertGET200(url)

        with self.assertNoException():
            choices = response.context['form'].fields['ctypes'].ctypes

        self.assertIn(get_ct(FakeActivity), choices)  # Compatible & not used
        self.assertNotIn(get_ct(FakeImage), choices)  # Still not compatible
        self.assertNotIn(get_ct(FakeContact), choices)  # Used
        self.assertNotIn(get_ct(FakeOrganisation), choices)  # Used

    def test_add_relationbrick_ctypes02(self):
        "All ContentTypes allowed"
        rt = RelationType.create(('test-subfoo', 'subject_predicate'),
                                 ('test-objfoo', 'object_predicate'),
                                )[0]

        rb_item = RelationBlockItem.objects.create(
                        block_id='specificblock_creme_config-test-subfoo',
                        relation_type=rt,
                    )

        url = self._build_rbrick_addctypes_url(rb_item)
        response = self.assertGET200(url)

        with self.assertNoException():
            choices = response.context['form'].fields['ctypes'].ctypes

        get_ct = ContentType.objects.get_for_model
        self.assertIn(get_ct(FakeContact), choices)
        self.assertIn(get_ct(FakeOrganisation), choices)
        self.assertIn(get_ct(FakeActivity), choices)

        self.assertNoFormError(self.client.post(url, data={'ctypes': [get_ct(FakeContact).id]}))

        rb_item = self.refresh(rb_item)
        self.assertIsNone(rb_item.get_cells(get_ct(FakeOrganisation)))
        self.assertEqual([], rb_item.get_cells(get_ct(FakeContact)))

        # Used CTypes should not be proposed
        response = self.assertGET200(url)

        with self.assertNoException():
            choices = response.context['form'].fields['ctypes'].ctypes

        self.assertNotIn(get_ct(FakeContact), choices)  # Used
        self.assertIn(get_ct(FakeOrganisation), choices)  # Not used

    def test_add_relationbrick_ctypes_wizard01(self):
        rt = RelationType.create(('test-subfoo', 'subject_predicate'),
                                 ('test-objfoo', 'object_predicate', [FakeContact, FakeOrganisation, FakeActivity]),
                                 )[0]

        rb_item = RelationBlockItem.objects.create(
                        block_id='specificblock_creme_config-test-subfoo',
                        relation_type=rt,
                    )

        url = self._build_rbrick_addctypes_wizard_url(rb_item)
        response = self.assertGET200(url)

        with self.assertNoException():
            choices = response.context['form'].fields['ctype'].ctypes

        get_ct = ContentType.objects.get_for_model
        ct_contact  = get_ct(FakeContact)
        ct_activity = get_ct(FakeActivity)
        ct_image    = get_ct(FakeImage)
        self.assertIn(ct_contact,           choices)
        self.assertIn(get_ct(FakeOrganisation), choices)
        self.assertIn(ct_activity,          choices)
        self.assertNotIn(ct_image,          choices)

        response = self.assertPOST200(url,
                                      {'relation_c_type_brick_wizard-current_step': '0',
                                       '0-ctype': ct_contact.pk,
                                      }
                                     )

        # Last step is not submitted so nothing yet in database
        rb_item = self.refresh(rb_item)
        self.assertIsNone(rb_item.get_cells(ct_contact))

        with self.assertNoException():
            fields = response.context['form'].fields

        self.assertIn('cells', fields)

        funcfield = FakeContact.function_fields.get('get_pretty_properties')
        field_fname = 'first_name'
        field_lname = 'last_name'
        response = self.client.post(
                url,
                data={'relation_c_type_brick_wizard-current_step': '1',
                      '1-cells': 'regular_field-%(rfield1)s,regular_field-%(rfield2)s,function_field-%(ffield)s' % {
                                         'rfield1': field_fname,
                                         'rfield2': field_lname,
                                         'ffield':  funcfield.name,
                                    },
                     },
            )
        self.assertNoFormError(response)

        rb_item = self.refresh(rb_item)
        self.assertIsNone(rb_item.get_cells(ct_activity))

        cells = rb_item.get_cells(ct_contact)
        self.assertIsInstance(cells, list)
        self.assertEqual(3, len(cells))

        cell = cells[0]
        self.assertIsInstance(cell, EntityCellRegularField)
        self.assertEqual(field_fname, cell.value)

        self.assertEqual(field_lname, cells[1].value)

        cell = cells[2]
        self.assertIsInstance(cell, EntityCellFunctionField)
        self.assertEqual(funcfield.name, cell.value)

        # Used CTypes should not be proposed
        response = self.assertGET200(url)

        with self.assertNoException():
            choices = response.context['form'].fields['ctype'].ctypes

        self.assertIn(ct_activity,   choices)  # Compatible & not used
        self.assertNotIn(ct_image,   choices)  # Still not compatible
        self.assertNotIn(ct_contact, choices)  # Used

    def test_add_relationbrick_ctypes_wizard02(self):
        "ContentType constraint"
        rtype = RelationType.create(('test-subfoo', 'subject_predicate', [FakeContact]),
                                    ('test-objfoo', 'object_predicate',  [FakeOrganisation]),
                                    )[0]
        rb_item = RelationBlockItem.objects.create(
                        block_id='specificblock_creme_config-test-subfoo',
                        relation_type=rtype,
                    )

        url = self._build_rbrick_addctypes_wizard_url(rb_item)
        response = self.assertGET200(url)

        with self.assertNoException():
            choices = response.context['form'].fields['ctype'].ctypes

        get_ct = ContentType.objects.get_for_model
        ct_contact = get_ct(FakeContact)
        self.assertIn(get_ct(FakeOrganisation), choices)
        self.assertNotIn(ct_contact,        choices)
        self.assertNotIn(get_ct(FakeActivity), choices)

        response = self.client.post(url,
                                    {'relation_c_type_brick_wizard-current_step': '0',
                                     '0-ctype': ct_contact.pk,
                                    }
                                   )
        self.assertFormError(response, 'form', 'ctype',
                             _(u'Select a valid choice. That choice is not one of the available choices.')
                            )

    def test_add_relationbrick_ctypes_wizard03(self):
        "Go back"
        rtype = RelationType.create(('test-subfoo', 'subject_predicate', [FakeOrganisation]),
                                    ('test-objfoo', 'object_predicate',  [FakeContact]),
                                    )[0]
        rb_item = RelationBlockItem.objects.create(
                        block_id='specificblock_creme_config-test-subfoo',
                        relation_type=rtype,
                    )

        url = self._build_rbrick_addctypes_wizard_url(rb_item)

        ct_contact  = ContentType.objects.get_for_model(FakeContact)
        self.assertPOST200(url,
                           {'relation_c_type_brick_wizard-current_step': '0',
                            '0-ctype': ct_contact.pk,
                           }
                          )

        # Return to first step
        response = self.assertPOST200(url,
                                      {'relation_c_type_brick_wizard-current_step': '1',
                                       'wizard_goto_step': '0',
                                      }
                                     )

        with self.assertNoException():
            choices = response.context['form'].fields['ctype'].ctypes

        self.assertIn(ct_contact, choices)

    def test_edit_relationbrick_ctypes01(self):
        ct = ContentType.objects.get_for_model(FakeContact)
        rt = RelationType.create(('test-subfoo', 'subject_predicate'),
                                 ('test-objfoo', 'object_predicate'),
                                )[0]

        rb_item = RelationBlockItem(
                        block_id='specificblock_creme_config-test-subfoo',
                        relation_type=rt,
                    )
        rb_item.set_cells(ct, ())
        rb_item.save()

        self.assertGET404(self._build_rbrick_editctype_url(rb_item, FakeOrganisation))

        url = self._build_rbrick_editctype_url(rb_item, FakeContact)
        self.assertGET200(url)

        funcfield = FakeContact.function_fields.get('get_pretty_properties')
        field_fname = 'first_name'
        field_lname = 'last_name'
        self.assertNoFormError(self.client.post(
            url,
            data={'cells': 'regular_field-%(rfield1)s,regular_field-%(rfield2)s,function_field-%(ffield)s' % {
                                'rfield1': field_fname,
                                'rfield2': field_lname,
                                'ffield':  funcfield.name,
                            },
                 }
           )
        )

        rb_item = self.refresh(rb_item)
        cells = rb_item.get_cells(ct)
        self.assertIsInstance(cells, list)
        self.assertEqual(3, len(cells))

        cell = cells[0]
        self.assertIsInstance(cell, EntityCellRegularField)
        self.assertEqual(field_fname, cell.value)

        self.assertEqual(field_lname, cells[1].value)

        cell = cells[2]
        self.assertIsInstance(cell, EntityCellFunctionField)
        self.assertEqual(funcfield.name, cell.value)

    def test_edit_relationbrick_ctypes02(self):
        "Validation errors with URLField & ForeignKey"
        rb_item = RelationBlockItem(
                block_id='specificblock_creme_config-test-subfoo',
                relation_type=RelationType.create(('test-subfoo', 'subject_predicate'),
                                                  ('test-objfoo', 'object_predicate'),
                                                 )[0],
            )
        rb_item.set_cells(ContentType.objects.get_for_model(FakeContact), ())
        rb_item.save()

        url = self._build_rbrick_editctype_url(rb_item, FakeContact)

        def post(field_name, error=True):
            response = self.assertPOST200(
                url,
                data={'cells': 'regular_field-%(rfield1)s,regular_field-%(rfield2)s' % {
                                    'rfield1': field_name,
                                    'rfield2': 'last_name',
                                },
                     }
            )
            if error:
                self.assertFormError(response, 'form', 'cells',
                                     _(u'This type of field can not be the first column.')
                                    )
            else:
                self.assertNoFormError(response)

        post('url_site')
        post('email')
        post('image')
        post('image__name')
        post('civility', error=False)
        post('civility__shortcut', error=False)

    def test_edit_relationbrick_ctypes03(self):
        "Validation errors with M2M"
        rb_item = RelationBlockItem(
                block_id='specificblock_creme_config-test-subfoo',
                relation_type=RelationType.create(('test-subfoo', 'subject_predicate'),
                                                  ('test-objfoo', 'object_predicate'),
                                                 )[0],
            )
        rb_item.set_cells(ContentType.objects.get_for_model(FakeEmailCampaign), ())
        rb_item.save()

        url = self._build_rbrick_editctype_url(rb_item, FakeEmailCampaign)

        def post(field_name):
            response = self.assertPOST200(
                url,
                data={'cells': 'regular_field-%(rfield1)s,regular_field-%(rfield2)s' % {
                                    'rfield1': field_name,
                                    'rfield2': 'name',
                                },
                     }
            )
            self.assertFormError(response, 'form', 'cells',
                                 _('This type of field can not be the first column.')
                                )

        post('mailing_lists')
        post('mailing_lists__name')

    def test_edit_relationbrick_ctypes04(self):
        "Validation errors with Relation"
        create_rtype = RelationType.create
        rt1 = create_rtype(('test-subfoo', 'subject_predicate1'), ('test-objfoo', 'object_predicate2'))[0]
        rt2 = create_rtype(('test-subbar', 'subject_predicate2'), ('test-objbar', 'object_predicate2'))[0]

        rb_item = RelationBlockItem(
                block_id='specificblock_creme_config-test-subfoo',
                relation_type=rt1,
            )
        rb_item.set_cells(ContentType.objects.get_for_model(FakeOrganisation), ())
        rb_item.save()

        response = self.assertPOST200(
            self._build_rbrick_editctype_url(rb_item, FakeOrganisation),
            data={'cells': 'relation-%(rtype)s,regular_field-%(rfield)s' % {
                                'rtype':  rt2.id,
                                'rfield': 'name',
                            },
                 }
        )
        self.assertFormError(response, 'form', 'cells',
                             _('This type of field can not be the first column.')
                            )

    def test_edit_relationbrick_ctypes05(self):
        "With FieldsConfig"
        ct = ContentType.objects.get_for_model(FakeContact)
        rt = RelationType.create(('test-subfoo', 'subject_predicate'),
                                 ('test-objfoo', 'object_predicate'),
                                )[0]


        valid_fname = 'last_name'
        hidden_fname1 = 'phone'
        hidden_fname2 = 'birthday'
        FieldsConfig.create(FakeContact,
                            descriptions=[(hidden_fname1, {FieldsConfig.HIDDEN: True}),
                                          (hidden_fname2, {FieldsConfig.HIDDEN: True}),
                                         ],
                            )

        rb_item = RelationBlockItem(
                        block_id='specificblock_creme_config-test-subfoo',
                        relation_type=rt,
                    )
        build_cell = EntityCellRegularField.build
        rb_item.set_cells(ct, [build_cell(FakeContact, hidden_fname1)])
        rb_item.save()

        url = self._build_rbrick_editctype_url(rb_item, FakeContact)
        response = self.assertPOST200(
                        url,
                        data={'cells': 'regular_field-%(rfield1)s,regular_field-%(rfield2)s,regular_field-%(rfield3)s' % {
                                            'rfield1': valid_fname,
                                            'rfield2': hidden_fname1,
                                            'rfield3': hidden_fname2,
                                        },
                             }
                    )
        self.assertFormError(response, 'form', 'cells', _(u'Enter a valid value.'))

        self.assertNoFormError(self.client.post(
            url,
            data={'cells': 'regular_field-%(rfield1)s,regular_field-%(rfield2)s' % {
                                'rfield1': valid_fname,
                                'rfield2': hidden_fname1,
                            },
                 }
           ))

        rb_item = self.refresh(rb_item)
        self.assertEqual(2, len(rb_item.get_cells(ct)))

    def test_delete_relationbrick_ctypes(self):
        get_ct = ContentType.objects.get_for_model
        ct = get_ct(FakeContact)

        rb_item = RelationBlockItem(
                block_id='specificblock_creme_config-test-subfoo',
                relation_type=RelationType.create(('test-subfoo', 'subject_predicate'),
                                                  ('test-objfoo', 'object_predicate'),
                                                 )[0],
            )
        rb_item.set_cells(ct, [EntityCellRegularField.build(FakeContact, 'first_name')])
        rb_item.save()

        # url = '/creme_config/blocks/relation_block/%s/delete_ctype' % rb_item.id
        url = reverse('creme_config__delete_cells_of_rtype_brick', args=(rb_item.id,))
        self.assertPOST404(url, data={'id': get_ct(FakeOrganisation).id})

        data = {'id': ct.id}
        self.assertGET404(url, data=data)  # Only POST

        self.assertPOST200(url, data=data)
        self.assertIsNone(self.refresh(rb_item).get_cells(ct))

    def test_delete_relationbrick(self):
        rt = RelationType.create(('test-subfoo', 'subject_predicate'),
                                 ('test-objfoo', 'object_predicate'), is_custom=False
                                )[0]
        rbi = RelationBlockItem.objects.create(block_id='foobarid', relation_type=rt)
        loc = BlockDetailviewLocation.create(block_id=rbi.block_id, order=5,
                                             zone=BlockDetailviewLocation.RIGHT,
                                             model=FakeContact,
                                             )

        # self.assertPOST200('/creme_config/blocks/relation_block/delete', data={'id': rbi.id})
        self.assertPOST200(reverse('creme_config__delete_rtype_brick'), data={'id': rbi.id})
        self.assertDoesNotExist(rbi)
        self.assertDoesNotExist(loc)

    def test_delete_instancebrick(self):
        naru = FakeContact.objects.create(user=self.user, first_name='Naru', last_name='Narusegawa')

        ibi = InstanceBlockConfigItem.objects.create(
                    block_id=InstanceBlockConfigItem.generate_id(DetailviewInstanceBrick, naru, ''),
                    entity=naru, verbose='All stuffes',
                )
        loc = BlockDetailviewLocation.create(block_id=ibi.block_id, order=5,
                                             zone=BlockDetailviewLocation.RIGHT, model=FakeContact,
                                            )
        # self.assertPOST200('/creme_config/blocks/instance_block/delete', data={'id': ibi.id})
        self.assertPOST200(reverse('creme_config__delete_instance_brick'), data={'id': ibi.id})
        self.assertDoesNotExist(ibi)
        self.assertDoesNotExist(loc)

    def test_add_custombrick(self):
        get_ct = ContentType.objects.get_for_model
        ct = get_ct(FakeContact)
        self.assertFalse(CustomBlockConfigItem.objects.filter(content_type=ct))

        # url = '/creme_config/blocks/custom/add/'
        url = reverse('creme_config__create_custom_brick_legacy')
        response = self.assertGET200(url)

        with self.assertNoException():
            ctypes = response.context['form'].fields['ctype'].ctypes

        self.assertIn(ct, ctypes)
        self.assertNotIn(get_ct(FakeInvoiceLine), ctypes)

        name = 'Regular info'
        self.assertNoFormError(self.client.post(url,
                                                data={'ctype': ct.id,
                                                      'name':  name,
                                                     }
                                               )
                              )

        cbc_items = CustomBlockConfigItem.objects.filter(content_type=ct)
        self.assertEqual(1, len(cbc_items))

        cbc_item = cbc_items[0]
        self.assertEqual(name, cbc_item.name)
        self.assertEqual([], cbc_item.cells)

        self.assertNoFormError(self.client.post(url,
                                                data={'ctype': ct.id,
                                                      'name':  'Other info',
                                                     }
                                               )
                              )
        self.assertEqual(2, CustomBlockConfigItem.objects.filter(content_type=ct).count())

    def test_edit_custombrick01(self):
        ct = ContentType.objects.get_for_model(FakeContact)

        loves = RelationType.create(('test-subject_love', u'Is loving'),
                                    ('test-object_love',  u'Is loved by')
                                   )[0]
        customfield = CustomField.objects.create(name=u'Size (cm)',
                                                 field_type=CustomField.INT,
                                                 content_type=ct,
                                                )
        funcfield = FakeContact.function_fields.get('get_pretty_properties')

        name = 'info'
        cbc_item = CustomBlockConfigItem.objects.create(id='tests-contacts1',
                                                        content_type=ct, name=name,
                                                       )

        url = self._build_custombrick_edit_url(cbc_item)
        self.assertGET200(url)

        name = name.title()
        field_lname = 'last_name'
        field_subname = 'address__city'
        self.assertNoFormError(self.client.post(
            url, follow=True,
            data={'name':  name,
                  'cells': 'regular_field-%(rfield1)s,regular_field-%(rfield2)s,relation-%(rtype)s,function_field-%(ffield)s,custom_field-%(cfield)s' % {
                                'rfield1': field_lname,
                                'rfield2': field_subname,
                                'cfield':  customfield.id,
                                'rtype':   loves.id,
                                'ffield':  funcfield.name,
                            },
                 }
           )
        )

        cbc_item = self.refresh(cbc_item)
        self.assertEqual(name, cbc_item.name)

        cells = cbc_item.cells
        self.assertIsInstance(cells, list)
        self.assertEqual(5, len(cells))

        cell = cells[0]
        self.assertIsInstance(cell, EntityCellRegularField)
        self.assertEqual(field_lname, cell.value)

        self.assertEqual(field_subname, cells[1].value)

        cell = cells[2]
        self.assertIsInstance(cell, EntityCellRelation)
        self.assertEqual(loves.id, cell.value)

        cell = cells[3]
        self.assertIsInstance(cell, EntityCellFunctionField)
        self.assertEqual(funcfield.name, cell.value)

        cell = cells[4]
        self.assertIsInstance(cell, EntityCellCustomField)
        self.assertEqual(str(customfield.id), cell.value)

    def test_edit_custombrick02(self):
        "With FieldsConfig"
        ct = ContentType.objects.get_for_model(FakeContact)

        valid_fname = 'last_name'
        valid_subfname = 'city'
        hidden_fname = 'phone'
        hidden_fkname = 'image'
        hidden_subfname = 'zipcode'

        create_fconf = FieldsConfig.create
        create_fconf(FakeContact, descriptions=[(hidden_fname, {FieldsConfig.HIDDEN: True}),
                                                (hidden_fkname, {FieldsConfig.HIDDEN: True}),
                                                ]
                     )
        create_fconf(FakeAddress, descriptions=[(hidden_subfname, {FieldsConfig.HIDDEN: True})])

        cbc_item = CustomBlockConfigItem.objects.create(id='tests-contacts1',
                                                        name='Contact info',
                                                        content_type=ct,
                                                       )

        url = self._build_custombrick_edit_url(cbc_item)
        response = self.assertGET200(url)

        with self.assertNoException():
            widget = response.context['form'].fields['cells'].widget
            choices_keys = {c[0] for c in widget.model_fields}

        self.assertIn('regular_field-' + valid_fname,     choices_keys)
        self.assertIn('regular_field-address',            choices_keys)
        self.assertNotIn('regular_field-' + hidden_fname, choices_keys)

        response = self.assertPOST200(
                        url, follow=True,
                        data={'name':  cbc_item.name,
                              'cells': 'regular_field-%(rfield1)s,regular_field-%(rfield2)s' % {
                                            'rfield1': valid_fname,
                                            'rfield2': hidden_fname,
                                        },
                             },
                    )
        self.assertFormError(response, 'form', 'cells', _('Enter a valid value.'))

        # ---------------------------
        with self.assertNoException():
            address_choices_keys = {c[0] for c in widget.model_subfields['regular_field-address']}

        prefix = 'address__'
        self.assertIn('regular_field-' + prefix + valid_subfname, address_choices_keys)
        self.assertNotIn('regular_field-' + prefix + hidden_subfname, address_choices_keys)

        response = self.assertPOST200(
                        url, follow=True,
                        data={'name':  cbc_item.name,
                              'cells': 'regular_field-%(rfield1)s,regular_field-%(rfield2)s' % {
                                            'rfield1': valid_fname,
                                            'rfield2': prefix + hidden_subfname,
                                        },
                             },
                    )
        self.assertFormError(response, 'form', 'cells', _('Enter a valid value.'))

        # ----------------------------
        self.assertNotIn('regular_field-' + hidden_fkname, choices_keys)
        self.assertFalse(widget.model_subfields['regular_field-image'])

    def test_edit_custombrick03(self):
        "With FieldsConfig + field in the blocks becomes hidden => still proposed in the form"
        ct = ContentType.objects.get_for_model(FakeContact)

        valid_fname = 'last_name'
        hidden_fname1 = 'phone'
        hidden_fname2 = 'mobile'

        hidden_fkname = 'image__description'

        addr_prefix = 'address__'
        hidden_subfname1 = 'zipcode'
        hidden_subfname2 = 'country'

        create_fconf = FieldsConfig.create
        create_fconf(FakeContact, descriptions=[(hidden_fname1, {FieldsConfig.HIDDEN: True}),
                                                (hidden_fname2, {FieldsConfig.HIDDEN: True}),
                                                ('image',       {FieldsConfig.HIDDEN: True}),
                                               ],
                    )
        create_fconf(FakeAddress, descriptions=[(hidden_subfname1, {FieldsConfig.HIDDEN: True}),
                                                (hidden_subfname2, {FieldsConfig.HIDDEN: True}),
                                               ],
                    )

        build_cell = EntityCellRegularField.build
        cbc_item = CustomBlockConfigItem.objects.create(
                        id='tests-contacts1', name='Contact info', content_type=ct,
                        cells=[build_cell(FakeContact, valid_fname),
                               build_cell(FakeContact, hidden_fname1),
                               build_cell(FakeContact, addr_prefix + hidden_subfname1),
                               build_cell(FakeContact, hidden_fkname),
                              ],
                    )

        url = self._build_custombrick_edit_url(cbc_item)
        response = self.assertGET200(url)

        with self.assertNoException():
            widget = response.context['form'].fields['cells'].widget
            choices_keys = {c[0] for c in widget.model_fields}

            subfields = widget.model_subfields
            address_choices_keys = {c[0] for c in subfields['regular_field-address']}
            image_choices_keys   = {c[0] for c in subfields['regular_field-image']}

        rf_prefix = 'regular_field-'
        self.assertIn(rf_prefix + valid_fname,   choices_keys)
        self.assertIn(rf_prefix + hidden_fname1, choices_keys) # was already in the block => still proposed
        self.assertNotIn(rf_prefix + hidden_fname2, choices_keys)

        self.assertIn(rf_prefix + addr_prefix + hidden_subfname1, address_choices_keys) # idem
        self.assertNotIn(rf_prefix + addr_prefix + hidden_subfname2, address_choices_keys)

        self.assertIn(rf_prefix + hidden_fkname, image_choices_keys) # idem
        self.assertIn(rf_prefix + 'image',       choices_keys) # we need it because we have a subfield

        response = self.client.post(
                        url, follow=True,
                        data={'name':  cbc_item.name,
                              'cells': ','.join(rf_prefix + fname
                                                    for fname in (valid_fname,
                                                                  hidden_fname1,
                                                                  addr_prefix + hidden_subfname1,
                                                                  hidden_fkname,
                                                                 )
                                               ),
                             },
                    )
        self.assertNoFormError(response)
        self.assertEqual(4, len(self.refresh(cbc_item).cells))

    def test_delete_custombrick(self):
        ct = ContentType.objects.get_for_model(FakeContact)
        cbci = CustomBlockConfigItem.objects.create(content_type=ct, name='Info')
        loc = BlockDetailviewLocation.create(block_id=cbci.generate_id(), order=5,
                                             model=FakeContact,
                                             zone=BlockDetailviewLocation.RIGHT,
                                            )

        # self.assertPOST200('/creme_config/blocks/custom/delete', data={'id': cbci.id})
        self.assertPOST200(reverse('creme_config__delete_custom_brick'), data={'id': cbci.id})
        self.assertDoesNotExist(cbci)
        self.assertDoesNotExist(loc)

    def test_custombrick_wizard_model_step(self):
        contact_ct = ContentType.objects.get_for_model(FakeContact)
        contact_customfield = CustomField.objects.create(name=u'Size (cm)',
                                                         field_type=CustomField.INT,
                                                         content_type=contact_ct,
                                                        )

        self.assertFalse(CustomBlockConfigItem.objects.filter(content_type=contact_ct))

        response = self.assertGET200(self.CUSTOM_WIZARD_URL)
        self.assertIn(contact_ct, response.context['form'].fields['ctype'].ctypes)

        response = self.assertPOST200(self.CUSTOM_WIZARD_URL,
                                      {'custom_brick_wizard-current_step': '0',
                                       '0-ctype': contact_ct.pk,
                                       '0-name': 'foobar',
                                      }
                                     )

        cells_widget = response.context['form'].fields['cells'].widget
        customfield_ids = [e[0] for e in cells_widget.custom_fields]
        regularfield_ids = [e[0] for e in cells_widget.model_fields]

        self.assertIn('custom_field-%s' % contact_customfield.id, customfield_ids)
        self.assertIn('regular_field-first_name', regularfield_ids)
        self.assertIn('regular_field-birthday', regularfield_ids)

        # last step is not submitted so nothing yet in database
        self.assertFalse(CustomBlockConfigItem.objects.filter(content_type=contact_ct))

    def test_custombrick_wizard_model_step_invalid(self):
        contact_ct = ContentType.objects.get_for_model(FakeContact)
        self.assertFalse(CustomBlockConfigItem.objects.filter(content_type=contact_ct))

        response = self.assertGET200(self.CUSTOM_WIZARD_URL)
        self.assertIn(contact_ct, response.context['form'].fields['ctype'].ctypes)

        response = self.assertPOST200(self.CUSTOM_WIZARD_URL,
                                      {'custom_brick_wizard-current_step': '0',
                                       '0-ctype': 'unknown',
                                       '0-name': 'foobar',
                                      }
                                     )

        self.assertFormError(response, 'form', 'ctype',
                             _(u'Select a valid choice. That choice is not one of the available choices.')
                            )

        self.assertFalse(CustomBlockConfigItem.objects.filter(content_type=contact_ct))

    def test_custombrick_wizard_config_step(self):
        contact_ct = ContentType.objects.get_for_model(FakeContact)
        contact_customfield = CustomField.objects.create(name=u'Size (cm)',
                                                         field_type=CustomField.INT,
                                                         content_type=contact_ct,
                                                        )

        self.assertFalse(CustomBlockConfigItem.objects.filter(content_type=contact_ct))

        response = self.assertGET200(self.CUSTOM_WIZARD_URL)
        self.assertIn(contact_ct, response.context['form'].fields['ctype'].ctypes)

        response = self.assertPOST200(self.CUSTOM_WIZARD_URL,
                                      {'custom_brick_wizard-current_step': '0',
                                       '0-ctype': contact_ct.pk,
                                       '0-name': 'foobar',
                                      }
                                     )
        cells_widget = response.context['form'].fields['cells'].widget
        customfield_ids = [e[0] for e in cells_widget.custom_fields]
        regularfield_ids = [e[0] for e in cells_widget.model_fields]

        self.assertIn('custom_field-%s' % contact_customfield.id, customfield_ids)
        self.assertIn('regular_field-first_name', regularfield_ids)
        self.assertIn('regular_field-birthday', regularfield_ids)

        response = self.assertPOST200(self.CUSTOM_WIZARD_URL,
                                      {'custom_brick_wizard-current_step': '1',
                                       '1-cells': '%s,%s' % ('regular_field-first_name',
                                                             'custom_field-%s' % contact_customfield.id,
                                                            ),
                                      }
                                     )
        self.assertNoFormError(response)

        cbci = self.get_object_or_fail(CustomBlockConfigItem, content_type=contact_ct)
        cells = [(c.__class__, c.key, c.value) for c in cbci.cells]

        self.assertListEqual([(EntityCellRegularField, 'regular_field-first_name', 'first_name'),
                              (EntityCellCustomField,
                               'custom_field-%s' % contact_customfield.id,
                               unicode(contact_customfield.id)
                              ),
                             ], cells
                            )

    def test_custombrick_wizard_go_back(self):
        contact_ct = ContentType.objects.get_for_model(FakeContact)
        contact_customfield = CustomField.objects.create(name=u'Size (cm)',
                                                         field_type=CustomField.INT,
                                                         content_type=contact_ct,
                                                        )

        self.assertFalse(CustomBlockConfigItem.objects.filter(content_type=contact_ct))

        response = self.assertGET200(self.CUSTOM_WIZARD_URL)
        self.assertIn(contact_ct, response.context['form'].fields['ctype'].ctypes)

        response = self.assertPOST200(self.CUSTOM_WIZARD_URL,
                                      {'custom_brick_wizard-current_step': '0',
                                       '0-ctype': contact_ct.pk,
                                       '0-name': 'foobar',
                                      }
                                     )
        cells_widget = response.context['form'].fields['cells'].widget
        customfield_ids = [e[0] for e in cells_widget.custom_fields]
        regularfield_ids = [e[0] for e in cells_widget.model_fields]

        self.assertIn('custom_field-%s' % contact_customfield.id, customfield_ids)
        self.assertIn('regular_field-first_name', regularfield_ids)
        self.assertIn('regular_field-birthday', regularfield_ids)

        # Return to first step
        response = self.assertPOST200(self.CUSTOM_WIZARD_URL,
                                      {'custom_brick_wizard-current_step': '1',
                                       'wizard_goto_step': '0',
                                      }
                                     )
        self.assertIn(contact_ct, response.context['form'].fields['ctype'].ctypes)