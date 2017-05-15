from flask_pymongo import PyMongo

mongo = PyMongo()


class AbellDb(object):
    def get_asset_info(self, asset_type):
        asset_info = mongo.db.assetinfo.find_one({'type': asset_type},
                                                 {'_id': False})
        return asset_info

    def update_managed_vars(self, asset_type, new_vars):
        resp = mongo.db.assetinfo.update({'type': asset_type},
                                         {'$push': {'managed_keys':
                                          {'$each': new_vars}}})
        # print resp

    def add_new_key(self, asset_type, new_vars):
        # adds new field to all assets of a given type
        response_dict = {'success': False,
                         'error': None,
                         'message': None}

        new_var_dict = dict((k, 'None') for k in new_vars)
        try:
            resp = mongo.db[asset_type].update_many({},
                                                    {'$set': new_var_dict})
            if resp.acknowledged is True:
                response_dict.update(
                    {'success': True,
                     'message': new_vars})
                return response_dict
        except Exception as e:
            response_dict.update(
                {'error': 500,
                 'message': 'Unknown db error, contact admin'})
            return response_dict

    def add_new_asset(self, payload):
        response_dict = {'success': False,
                         'error': None,
                         'message': None}
        asset_type = payload.get('type')
        abell_id = payload.get('abell_id')
        if not asset_type:
            response_dict.update(
                {'error': 400,
                 'message': 'Did not recieve asset_type for insert'})
            return response_dict
        try:
            resp = mongo.db[asset_type].insert_one(payload)
            if resp.acknowledged is True:
                response_dict.update({'success': True,
                                      'message': 'asset with abell_id: %s '
                                                 'created' % abell_id})
                return response_dict
        except Exception as e:
            if 'duplicate key error' in str(e):
                response_dict.update(
                    {'error': 400,
                     'message': 'abell_id: %s already exists in the '
                                'database' % abell_id})
            else:
                response_dict.update(
                    {'error': 500,
                     'message': 'Unknown db, contact admin'})
            return response_dict