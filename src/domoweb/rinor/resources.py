#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Module purpose
==============

Implements
==========


@author: Cédric Trévisan <cedric@domogik.org>
@copyright: (C) 2007-2011 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from django.conf.urls.defaults import *
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from domoweb.rinor.rinorResource import RinorResource
from domoweb.rinor.pipes import *
from tastypie import fields
from tastypie.http import *
from tastypie.utils import trailing_slash

# Missing from tastypie 0.9.9
class HttpNotFound(HttpResponse):
    status_code = 404

class AssociationResource(RinorResource):
    # fields must map to the attributes in the Row class
    id = fields.IntegerField(attribute = 'id')
    place_id = fields.IntegerField(attribute = 'place_id')
    place_type = fields.CharField(attribute = 'place_type')
    place = fields.CharField(attribute = 'place')
    widget = fields.CharField(attribute = 'widget')
    device_feature_id = fields.IntegerField(attribute = 'device_feature_id')
    feature = fields.DictField(attribute = 'feature')

    class Meta:
        resource_name = 'association'
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['delete']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = AssociationExtendedPipe()

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<type>(house))%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), {'deep': False, 'pk': None}, name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<type>(house))/deep%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), {'deep': True, 'pk': None}, name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<type>(area|room))/(?P<pk>\d*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), {'deep': False}, name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<type>(area|room))/deep/(?P<pk>\d*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), {'deep': True}, name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\d*)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def obj_get_list(self, request, **kwargs):
        return self._meta.rinor_pipe.get_list(kwargs['type'], kwargs['pk'], kwargs['deep'])

    def obj_create(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.post_list(bundle["page_type"], bundle["feature_id"], bundle["page_id"], bundle["widget_id"], bundle["place_id"])

    def obj_delete(self, request=None, **kwargs):
        return self._meta.rinor_pipe.delete_detail(kwargs["pk"])

class FeatureResource(RinorResource):
    # fields must map to the attributes in the Row class
    id = fields.IntegerField(attribute = 'id')
    device_id = fields.IntegerField(attribute = 'device_id')
    device_feature_model_id = fields.CharField(attribute = 'device_feature_model_id')
    device = fields.DictField(attribute = 'device')
    device_feature_model = fields.DictField(attribute = 'device_feature_model')

    class Meta:
        resource_name = 'feature'
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = FeaturePipe()

class StateResource(RinorResource):
    
    class Meta:
        resource_name = 'state'
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = StatePipe()
        last_allowed_methods = ['get']
        fromto_allowed_methods = ['get']

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/last/(?P<last>\d+)/(?P<device>\d+)/(?P<key>[\w\d_-]+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_last'), name="api_dispatch_last"),
            url(r"^(?P<resource_name>%s)/from/(?P<from>\d+)/to/(?P<to>\d+)/interval/(?P<interval>(year|month|week|day|hour|minute|second))/selector/(?P<selector>(min|max|avg|first|last))/(?P<device>\d+)/(?P<key>[\w\d_-]+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_fromto'), name="api_dispatch_fromto"),
        ]
    
    def dispatch_last(self, request, **kwargs):
        return self.dispatch('last', request, **kwargs)

    def dispatch_fromto(self, request, **kwargs):
        return self.dispatch('fromto', request, **kwargs)
    
    def obj_get_last(self, request, **kwargs):
        _data = self._meta.rinor_pipe.get_last(kwargs['last'], kwargs['device'], kwargs['key'])
        if not(_data):
            raise ObjectDoesNotExist()
        return _data

    def obj_get_fromto(self, request, **kwargs):
        _data = self._meta.rinor_pipe.get_fromto(kwargs['from'], kwargs['to'], kwargs['interval'], kwargs['selector'], kwargs['device'], kwargs['key'])
        if not(_data):
            raise ObjectDoesNotExist()
        return _data
        
    def get_last(self, request, **kwargs):
        try:
            obj = self.obj_get_last(request=request, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpNotFound()
        return self.create_response(request, obj)

    def get_fromto(self, request, **kwargs):
        try:
            obj = self.obj_get_fromto(request=request, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpNotFound()
        return self.create_response(request, obj)

class UiConfigResource(RinorResource):
    # fields must map to the attributes in the Row class
    name = fields.CharField(attribute = 'name')
    reference = fields.CharField(attribute = 'reference')
    key = fields.CharField(attribute = 'key')
    value = fields.CharField(attribute = 'value')

    class Meta:
        resource_name = 'uiconfig'
        list_allowed_methods = ['get', 'post']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = UiConfigPipe()

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
        ]

    def obj_create(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.post_list(bundle["name"], bundle["reference"], bundle["key"], bundle["value"])

class PluginResource(RinorResource):
    # fields must map to the attributes in the Row class
    host = fields.CharField(attribute = 'host')
    list = fields.ListField(attribute = 'list')

    class Meta:
        resource_name = 'plugin'
        authentication = Authentication()
        authorization = Authorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['put']
        rinor_pipe = PluginPipe()
        include_resource_uri = False

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<hostname>[\w\d_-]+)/(?P<id>[\w\d_-]+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def obj_update(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.command_detail(kwargs['hostname'], kwargs["id"], bundle["command"])

class PluginDetailResource(RinorResource):
    # fields must map to the attributes in the Row class
    host = fields.CharField(attribute = 'host')
    status = fields.CharField(attribute = 'status')
    version = fields.CharField(attribute = 'version')
    id = fields.CharField(attribute = 'id')
    documentation = fields.CharField(attribute = 'documentation')
    technology = fields.CharField(attribute = 'technology')
    description = fields.CharField(attribute = 'description')
    configuration = fields.ListField(attribute = 'configuration')

    class Meta:
        resource_name = 'plugindetail'
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = PluginPipe()
        include_resource_uri = False

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<hostname>[\w\d_-]+)/(?P<id>[\w\d_-]+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def obj_get(self, request, **kwargs):
        return self._meta.rinor_pipe.get_detail(kwargs['hostname'], kwargs['id'])
        
class PluginConfigResource(RinorResource):
    # fields must map to the attributes in the Row class
    key = fields.CharField(attribute = 'key')
    value = fields.CharField(attribute = 'value')
    id = fields.CharField(attribute = 'id')
    hostname = fields.CharField(attribute = 'hostname')

    class Meta:
        resource_name = 'pluginconfig'
        list_allowed_methods = ['get', 'delete']
        detail_allowed_methods = ['get', 'delete', 'put']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = PluginConfigPipe()
        include_resource_uri = False

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<hostname>[\w\d_-]+)/(?P<id>[\w\d_-]+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<hostname>[\w\d_-]+)/(?P<id>[\w\d_-]+)/(?P<key>[\w\d_-]+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def obj_get_list(self, request, **kwargs):
        return self._meta.rinor_pipe.get_list(kwargs['hostname'], kwargs['id'])

    def obj_get(self, request, **kwargs):
        _data = self._meta.rinor_pipe.get_detail(kwargs['hostname'], kwargs['id'], kwargs['key'])
        if not(_data):
            raise ObjectDoesNotExist()
        return _data

    def obj_delete_list(self, request=None, **kwargs):
        return self._meta.rinor_pipe.delete_list(kwargs['hostname'], kwargs['id'])    
    
    def obj_delete(self, request=None, **kwargs):
        return self._meta.rinor_pipe.delete_detail(kwargs['hostname'], kwargs['id'], kwargs['key'])

    def obj_update(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.set_detail(kwargs['hostname'], kwargs['id'], kwargs['key'], bundle['value'])

class AreaResource(RinorResource):
    # fields must map to the attributes in the Row class
    id = fields.IntegerField(attribute = 'id')
    name = fields.CharField(attribute = 'name')
    description = fields.CharField(attribute = 'description')
    
    class Meta:
        resource_name = 'area'
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = AreaExtendedPipe()

    def obj_create(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.post_list(bundle["name"], bundle["description"])

    def obj_update(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.put_detail(kwargs['pk'], bundle["name"], bundle["description"])

    def obj_delete(self, request=None, **kwargs):
        return self._meta.rinor_pipe.delete_detail(kwargs["pk"])

class RoomResource(RinorResource):
    # fields must map to the attributes in the Row class
    id = fields.IntegerField(attribute = 'id')
    name = fields.CharField(attribute = 'name')
    description = fields.CharField(attribute = 'description')
    area_id = fields.IntegerField(attribute = 'area_id')
    
    class Meta:
        resource_name = 'room'
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = RoomExtendedPipe()

    def obj_create(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.post_list(bundle["name"], bundle["description"])

    def obj_update(self, bundle, request=None, **kwargs):
        if ('area_id' in bundle):
            return self._meta.rinor_pipe.put_detail(kwargs['pk'], None, None, bundle["area_id"])
        else:
            return self._meta.rinor_pipe.put_detail(kwargs['pk'], bundle["name"], bundle["description"], None)

    def obj_delete(self, request=None, **kwargs):
        return self._meta.rinor_pipe.delete_detail(kwargs["pk"])

class DeviceResource(RinorResource):
    # fields must map to the attributes in the Row class
#    id = fields.IntegerField(attribute = 'id')
#    name = fields.CharField(attribute = 'name')
#    description = fields.CharField(attribute = 'description')
#    area_id = fields.IntegerField(attribute = 'area_id')
    
    class Meta:
        resource_name = 'device'
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = DeviceExtendedPipe()

    def obj_create(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.post_list(bundle["name"], bundle["address"], bundle["type_id"], bundle["usage_id"], bundle["description"], bundle["reference"])

    def obj_update(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.put_detail(kwargs['pk'], bundle["name"], bundle["address"], bundle["usage_id"], bundle["description"], bundle["reference"])

    def obj_delete(self, request=None, **kwargs):
        return self._meta.rinor_pipe.delete_detail(kwargs["pk"])
        
class UserResource(RinorResource):
    # fields must map to the attributes in the Row class
    id = fields.IntegerField(attribute = 'id')
    person_id = fields.IntegerField(attribute = 'person_id')
    person = fields.DictField(attribute = 'person')
    login = fields.CharField(attribute = 'login')
    is_admin = fields.BooleanField(attribute = 'is_admin')

    class Meta:
        resource_name = 'user'
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = UserPipe()

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\d*)/password%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), {'password': True}, name="api_dispatch_detail"),
        ]

    def obj_create(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.post_list(bundle["login"], bundle["password"], bundle["is_admin"], bundle["first_name"], bundle["last_name"])

    def obj_update(self, bundle, request=None, **kwargs):
        if ('password' in kwargs):
            return self._meta.rinor_pipe.put_detail_password(kwargs['pk'], bundle["old"], bundle["new"])
        else:
            return self._meta.rinor_pipe.put_detail(kwargs['pk'], bundle["login"], bundle["is_admin"], bundle["first_name"], bundle["last_name"])

    def obj_delete(self, request=None, **kwargs):
        return self._meta.rinor_pipe.delete_detail(kwargs["pk"])

class PersonResource(RinorResource):
    # fields must map to the attributes in the Row class
    id = fields.IntegerField(attribute = 'id')
    first_name = fields.CharField(attribute = 'first_name')
    last_name = fields.CharField(attribute = 'last_name')

    class Meta:
        resource_name = 'person'
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = PersonPipe()

    def obj_create(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.post_list(bundle["first_name"], bundle["last_name"])

    def obj_update(self, bundle, request=None, **kwargs):
        return self._meta.rinor_pipe.put_detail(kwargs['pk'], bundle["first_name"], bundle["last_name"])

    def obj_delete(self, request=None, **kwargs):
        return self._meta.rinor_pipe.delete_detail(kwargs["pk"])

class InfoResource(RinorResource):
    # fields must map to the attributes in the Row class
    command = fields.DictField(attribute = 'command')
    event = fields.DictField(attribute = 'event')
    info = fields.DictField(attribute = 'info')
    queue = fields.DictField(attribute = 'queue')
    stats = fields.DictField(attribute = 'stats')

    class Meta:
        resource_name = 'info'
        info_allowed_methods = ['get']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = InfoPipe()

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_info'), name="api_dispatch_info"),
        ]

    def dispatch_info(self, request, **kwargs):
        return self.dispatch('info', request, **kwargs)
    
    def obj_get_info(self, request, **kwargs):
        _data = self._meta.rinor_pipe.get_info_extended()
        if not(_data):
            raise ObjectDoesNotExist()
        return _data
        
    def get_info(self, request, **kwargs):
        try:
            obj = self.obj_get_info(request=request, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpNotFound()
        return self.create_response(request, obj)

class HelperResource(RinorResource):
    # fields must map to the attributes in the Row class

    class Meta:
        resource_name = 'helper'
        detail_allowed_methods = ['put']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = HelperPipe()

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]
    
    def obj_update(self, bundle, request, **kwargs):
        _data = self._meta.rinor_pipe.get_info(bundle['command'])
        if not(_data):
            raise ObjectDoesNotExist()
        return _data
        
    def put_list(self, bundle, request, **kwargs):
        try:
            obj = self.obj_put_list(bundle, request=request, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpNotFound()
        return self.create_response(request, obj)

class PackageResource(RinorResource):
    # fields must map to the attributes in the Row class

    class Meta:
        resource_name = 'package'
        list_allowed_methods = ['get', 'put']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = PackagePipe()
   
    def obj_update_list(self, bundle, request=None, **kwargs):
        if (('action' in bundle) and (bundle['action'] == 'refresh')):
            return self._meta.rinor_pipe.refresh_list()
        else:
            return None

class CommandResource(RinorResource):
    # fields must map to the attributes in the Row class
#    name = fields.CharField(attribute = 'name')
#    reference = fields.CharField(attribute = 'reference')
#    key = fields.CharField(attribute = 'key')
#    value = fields.CharField(attribute = 'value')

    class Meta:
        resource_name = 'command'
        detail_allowed_methods = ['put']
        authentication = Authentication()
        authorization = Authorization()
        rinor_pipe = CommandPipe()

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<member>[\w\d_-]+)/(?P<address>.+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def obj_update(self, bundle, request=None, **kwargs):
        if ('value' in bundle):
            _data = self._meta.rinor_pipe.put_detail(kwargs['member'], kwargs['address'], bundle["command"], bundle["value"])
        else:
            _data = self._meta.rinor_pipe.put_detail(kwargs['member'], kwargs['address'], bundle["command"])
        return _data