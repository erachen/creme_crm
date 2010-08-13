# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2010  Hybird
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

#from logging import debug

from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext

from creme_core.forms.header_filter import HeaderFilterForm
from creme_core.views.generic import add_entity
from creme_core.models.header_filter import HeaderFilter, HeaderFilterList
from creme_core.entities_access.functions_for_permissions import delete_object_or_die
from creme_core.utils import get_ct_or_404


@login_required
def add(request, content_type_id, extra_template_dict=None):
    """
        @Permissions : to be set
    """
    ct_entity = get_ct_or_404(content_type_id)

    try:
        callback_url = ct_entity.model_class().get_lv_absolute_url()
    except AttributeError:
        callback_url = '/'

    return add_entity(request, HeaderFilterForm, callback_url,
                      template='creme_core/header_filters.html',
                      extra_initial={'content_type': ct_entity},
                      extra_template_dict=extra_template_dict or {})

@login_required
def edit(request, header_filter_id):
    hf = get_object_or_404(HeaderFilter, pk=header_filter_id)

    if not hf.is_custom:
        raise Http404("Non editable HeaderFilter")  #TODO: 403 instead

    if request.POST:
        hf_form = HeaderFilterForm(request.POST, instance=hf)

        if hf_form.is_valid():
            hf_form.save()

            return HttpResponseRedirect(hf.entity_type.model_class().get_lv_absolute_url())
    else:
        hf_form = HeaderFilterForm(instance=hf)

    return render_to_response('creme_core/header_filters.html',
                              {'form': hf_form},
                              context_instance=RequestContext(request))

@login_required
def delete(request, header_filter_id, js=0):
    hf           = get_object_or_404(HeaderFilter, pk=header_filter_id)
    callback_url = hf.entity_type.model_class().get_lv_absolute_url()
    return_msg   = u'Vue supprimée avec succès'
    status       = 200

    if hf.is_custom:
        die_status = delete_object_or_die(request, hf)
        if die_status:
            if not js:
                return die_status
            else:
                return_msg = u'Permission refusée'
                status = 400
        else:
            hf.delete()
    else:
        return_msg = u'Cette vue ne peut être effacée'
        status = 400

    if js:
        return HttpResponse(return_msg, mimetype="text/javascript", status=status)

    return HttpResponseRedirect(callback_url)

@login_required
def get_hfs_4_ct(request, content_type_id):
    """
        @Returns header filters' json list
    """
    ct = get_ct_or_404(content_type_id)
    hfl = HeaderFilterList(ct)
    fields = request.GET.getlist('fields') or ('name', )
    
    data = serializers.serialize('json', hfl, fields=fields)
    return HttpResponse(data, mimetype="text/javascript")
    

    