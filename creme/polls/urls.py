# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import pollcampaign_model_is_custom, pollform_model_is_custom, pollreply_model_is_custom
from .views import portal, poll_form, poll_reply


urlpatterns = [
    url(r'^$', portal.portal),

    url(r'^poll_form/stats/(?P<pform_id>\d+)$', poll_form.stats),

    # Form lines
    url(r'^poll_form/(?P<pform_id>\d+)/add/line$',        poll_form.add_line),
    url(r'^pform_line/(?P<line_id>\d+)/edit$',            poll_form.edit_line),
    url(r'^pform_line/(?P<line_id>\d+)/disable$',         poll_form.disable_line),
    url(r'^pform_line/(?P<line_id>\d+)/conditions/edit$', poll_form.edit_line_conditions),
    url(r'^pform_line/(?P<line_id>\d+)/choices$',         poll_form.get_choices),

    # Form section
    url(r'^poll_form/(?P<pform_id>\d+)/add/section$',     poll_form.add_section),
    url(r'^pform_section/(?P<section_id>\d+)/edit$',      poll_form.edit_section),
    url(r'^pform_section/(?P<section_id>\d+)/add/child$', poll_form.add_section_child),
    url(r'^pform_section/(?P<section_id>\d+)/add/line$',  poll_form.add_line_to_section),

    # Replies
    url(r'^poll_reply/fill/(?P<preply_id>\d+)$',           poll_reply.fill),
    url(r'^poll_reply/clean$',                             poll_reply.clean),
    url(r'^poll_reply/link_to_person/(?P<person_id>\d+)$', poll_reply.link_to_person),

    url(r'^poll_reply/(?P<preply_id>\d+)/line/(?P<line_id>\d+)/edit$',        poll_reply.edit_line),
    url(r'^poll_reply/(?P<preply_id>\d+)/line/(?P<line_id>\d+)/edit_wizard$', poll_reply.edit_line_wizard),
]

if not pollcampaign_model_is_custom():
    from .views import campaign

    urlpatterns += [
        url(r'^campaigns',                           campaign.listview,   name='polls__list_campaigns'),
        url(r'^campaign/add$',                       campaign.add,        name='polls__create_campaign'),
        url(r'^campaign/edit/(?P<campaign_id>\d+)$', campaign.edit,       name='polls__edit_campaign'),
        url(r'^campaign/(?P<campaign_id>\d+)$',      campaign.detailview, name='polls__view_campaign'),
    ]

if not pollform_model_is_custom():
    urlpatterns += [
        url(r'^poll_forms',                        poll_form.listview,   name='polls__list_forms'),
        url(r'^poll_form/add$',                    poll_form.add,        name='polls__create_form'),
        url(r'^poll_form/edit/(?P<pform_id>\d+)$', poll_form.edit,       name='polls__edit_form'),
        url(r'^poll_form/(?P<pform_id>\d+)$',      poll_form.detailview, name='polls__view_form'),
    ]

if not pollreply_model_is_custom():
    urlpatterns += [
        url(r'^poll_replies$',                                      poll_reply.listview,          name='polls__list_replies'),
        url(r'^poll_reply/add$',                                    poll_reply.add,               name='polls__create_reply'),
        url(r'^poll_reply/add_from_pform/(?P<pform_id>\d+)$',       poll_reply.add_from_pform,    name='polls__create_reply_from_pform'),
        url(r'^poll_reply/add_from_campaign/(?P<campaign_id>\d+)$', poll_reply.add_from_campaign, name='polls__create_reply_from_campaign'),
        url(r'^poll_reply/add_from_person/(?P<person_id>\d+)$',     poll_reply.add_from_person,   name='polls__create_reply_from_person'),
        url(r'^poll_reply/edit/(?P<preply_id>\d+)$',                poll_reply.edit,              name='polls__edit_reply'),
        url(r'^poll_reply/(?P<preply_id>\d+)$',                     poll_reply.detailview,        name='polls__view_reply'),
    ]
