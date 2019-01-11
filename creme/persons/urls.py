# -*- coding: utf-8 -*-

from django.conf.urls import url, include

from creme.creme_core.conf.urls import Swappable, swap_manager

from creme import persons
from .views import address, contact, crud_relations, organisation


urlpatterns = [
    url(r'^organisation/managed[/]?$',
        organisation.ManagedOrganisationsAdding.as_view(),
        name='persons__orga_set_managed',
    ),
    url(r'^organisation/not_managed[/]?$', organisation.unset_managed, name='persons__orga_unset_managed'),

    url(r'^(?P<entity_id>\d+)/become_', include([
        url(r'^customer[/]?$',          crud_relations.become_customer, name='persons__become_customer'),
        url(r'^prospect[/]?$',          crud_relations.become_prospect, name='persons__become_prospect'),
        url(r'^suspect[/]?$',           crud_relations.become_suspect,  name='persons__become_suspect'),
        url(r'^inactive_customer[/]?$', crud_relations.become_inactive, name='persons__become_inactive_customer'),
        url(r'^supplier[/]?$',          crud_relations.become_supplier, name='persons__become_supplier'),
    ])),
]

urlpatterns += swap_manager.add_group(
    persons.contact_model_is_custom,
    Swappable(url(r'^contacts[/]?$',                                                  contact.listview,                         name='persons__list_contacts')),
    Swappable(url(r'^contact/add[/]?$',                                               contact.ContactCreation.as_view(),        name='persons__create_contact')),
    Swappable(url(r'^contact/add_related/(?P<orga_id>\d+)[/]?$',                      contact.RelatedContactCreation.as_view(), name='persons__create_related_contact'), check_args=Swappable.INT_ID),
    Swappable(url(r'^contact/add_related/(?P<orga_id>\d+)/(?P<rtype_id>[\w-]+)[/]?$', contact.RelatedContactCreation.as_view(), name='persons__create_related_contact'), check_args=(1, 'idxxx')),
    Swappable(url(r'^contact/edit/(?P<contact_id>\d+)[/]?$',                          contact.ContactEdition.as_view(),         name='persons__edit_contact'),           check_args=Swappable.INT_ID),
    Swappable(url(r'^contact/(?P<contact_id>\d+)[/]?$',                               contact.ContactDetail.as_view(),          name='persons__view_contact'),           check_args=Swappable.INT_ID),
    app_name='persons',
).kept_patterns()

urlpatterns += swap_manager.add_group(
    persons.organisation_model_is_custom,
    Swappable(url(r'^organisations[/]?$',                      organisation.listview,                       name='persons__list_organisations')),
    Swappable(url(r'^organisation/add[/]?$',                   organisation.OrganisationCreation.as_view(), name='persons__create_organisation')),
    Swappable(url(r'^organisation/edit/(?P<orga_id>\d+)[/]?$', organisation.OrganisationEdition.as_view(),  name='persons__edit_organisation'), check_args=Swappable.INT_ID),
    Swappable(url(r'^organisation/(?P<orga_id>\d+)[/]?$',      organisation.OrganisationDetail.as_view(),   name='persons__view_organisation'), check_args=Swappable.INT_ID),
    Swappable(url(r'^leads_customers[/]?$',                    organisation.list_my_leads_my_customers,     name='persons__leads_customers')),
    app_name='persons',
).kept_patterns()

urlpatterns += swap_manager.add_group(
    persons.address_model_is_custom,
    Swappable(url(r'^address/add/(?P<entity_id>\d+)[/]?$',          address.AddressCreation.as_view(),         name='persons__create_address'),          check_args=Swappable.INT_ID),
    Swappable(url(r'^address/add/billing/(?P<entity_id>\d+)[/]?$',  address.BillingAddressCreation.as_view(),  name='persons__create_billing_address'),  check_args=Swappable.INT_ID),
    Swappable(url(r'^address/add/shipping/(?P<entity_id>\d+)[/]?$', address.ShippingAddressCreation.as_view(), name='persons__create_shipping_address'), check_args=Swappable.INT_ID),
    Swappable(url(r'^address/edit/(?P<address_id>\d+)[/]?$',        address.AddressEdition.as_view(),          name='persons__edit_address'),            check_args=Swappable.INT_ID),
    app_name='persons',
).kept_patterns()
