# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2011  Hybird
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

from django.utils.translation import ugettext_lazy as _

from creme_core.registry import creme_registry
from creme_core.gui.menu import creme_menu
from creme_core.gui.block import block_registry
from creme_core.gui.bulk_update import bulk_update_registry

from media_managers.models import Image
from media_managers.blocks import ImageBlock


creme_registry.register_app('media_managers', _(u'Media managers'), '/media')
creme_registry.register_entity_models(Image)

reg_item = creme_menu.register_app('media_managers', '/media_managers/').register_item
reg_item('/media_managers/',          _(u'Portal'),       'media_managers')
reg_item('/media_managers/image/add', _(u'Add an image'), 'media_managers.add_image')
reg_item('/media_managers/images',    _(u'All images'),   'media_managers')

block_registry.register_4_model(Image, ImageBlock())

bulk_update_registry.register(
    (Image, ['height', 'width', 'image']),
)