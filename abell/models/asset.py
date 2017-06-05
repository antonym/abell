# from repoze.lru import lru_cache
from abell.models import model_tools
from abell.database import AbellDb
from abell.models import asset_type as AT


ABELLDB = AbellDb()


def update_asset_values(asset_type, asset_filter, user_update_dict,
                        auth_level='user', multi=False):
    response_dict = {'success': False,
                     'error': None,
                     'message': None,
                     'updated_keys': {},
                     'updated_asset_ids': []}
    asset_type_info = asset_type.get_asset_type(asset_type).get('result')
    if not asset_type_info:
        response_dict.update({'error': 404,
                              'message': 'Type %s not found.' % asset_type})
        return response_dict

    # TEMP Auth check, this will Change)
    if auth_level == 'admin':
        valid_keys = set(asset_type_info.get('managed_keys') +
                         asset_type_info.get('unmanaged_keys'))
        for k, v in user_update_dict.items():
            if k.split('.')[0] in valid_keys:
                response_dict['updated_keys'][k] = v
    else:
        valid_keys = set(asset_type_info.get('unmanaged_keys'))
        for k, v in user_update_dict.items():
            if k.split('.')[0] in valid_keys:
                response_dict['updated_keys'][k] = v
    payload = model_tools.item_stringify(response_dict['updated_keys'])

    # Get abell ids of matching assets
    assets_to_update = asset_find(
                        asset_type,
                        asset_filter,
                        specified_keys={'_id': 0, 'abell_id': 1})
    assets_to_update = assets_to_update.get('result')
    if not multi:
        if len(assets_to_update) is not 1:
            response_dict.update({'error': 400,
                                  'message': 'The filter did not return '
                                             'a single asset'})
            return response_dict

    db_response = ABELLDB.update_asset(asset_type, asset_filter, payload)
    if db_response.get('success'):
        for a in assets_to_update:
            asset_id = a.get('abell_id')
            response_dict['updated_asset_ids'].append(asset_id)
        response_dict.update({'success': True,
                              'message': db_response.get('result')})
    # TODO Probably convert to a bulk find and update call
    # TODO Log updated documents
    return response_dict


def delete_assets(asset_type, asset_filter, auth_level='user', multi=False):
    response_dict = {'success': False,
                     'deleted_asset_ids': []}
    # Get abell_ids for matching assets_to_update
    assets_to_delete = asset_find(asset_type,
                                  asset_filter,
                                  specified_keys={'_id': 0, 'abell_id': 1})
    assets_to_delete = assets_to_delete.get('result')
    if not multi:
        if len(assets_to_delete) is not 1:
            response_dict.update({'error': 400,
                                  'message': 'The filter did not return '
                                             'a single asset'})
            return response_dict
    db_response = ABELLDB.delete_assets(asset_type, asset_filter)
    if db_response.get('success'):
        for a in assets_to_delete:
            asset_id = a.get('abell_id')
            response_dict['deleted_asset_ids'].append(asset_id)
        response_dict.update({'success': True})
    # TODO Probably convert to a bulk find and update call
    # TODO Log updated documents
    return response_dict


def asset_find(asset_type, params, specified_keys=None):
    return ABELLDB.asset_find(asset_type, params, specified_keys)


def distinct_asset_fields(asset_type, params, distinct_key):
    return ABELLDB.asset_distinct(asset_type, params, str(distinct_key))


def asset_count(asset_type, params):
    return ABELLDB.asset_count(asset_type, params)


class AbellAsset(object):

    def __init__(self, asset_type, abell_id, property_dict=None,
                 asset_object=None):
        if not asset_object:
            asset_object = AT.get_asset_type(asset_type)
        self.asset_object = asset_object
        self.asset_type = asset_object.asset_type
        self.abell_id = str(abell_id)
        self.fields = {}
        self.create_fields()
        if property_dict:
            self.add_property_dict(property_dict)

    def __getattr__(self, attr):
        if type(attr) == str:
            return 'None'
        raise AttributeError("%r object has no attribute %r" %
                             (self.__class__, attr))

    def get_property(self, name):
        return getattr(self, name)

    def create_fields(self):
        self.fields.update(dict.fromkeys(
                    self.asset_object.system_keys, 'None'))
        self.fields.update(dict.fromkeys(
                    self.asset_object.managed_keys, 'None'))
        self.fields.update(dict.fromkeys(
                    self.asset_object.unmanaged_keys, 'None'))

    def add_property_dict(self, property_dict):
        stringified_dict = model_tools.item_stringify(property_dict)
        for key, value in stringified_dict.items():
            if key in self.fields:
                self.fields[key] = value
        # for key, value in stringified_dict.iteritems():
            # self.add_property(key, value)
            # setattr(self, key, value)

    def stringified_attributes(self):
        return model_tools.item_stringify(self.fields)

    def __update_database(self, case, **kwargs):
        if case is 'new_asset':
            db_resp = ABELLDB.add_new_asset(self.fields)
            return db_resp
        return {'success': False}

    def create_asset(self):
        r = self.__update_database('new_asset')
        return r
        # log
        # possible hooks
