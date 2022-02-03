from flask import request
import requests

class DecisionPoints(object):
    
    def resource_check(self, settings, access_request, permission_info):

        grant_access = False

        subject_id = access_request['subject']['subject_id']
        action = access_request['action']

        resource_data_api = permission_info['resource']['resource_api']
        resource_data_url = settings['API_'+resource_data_api] + 'get/' + subject_id
        response = requests.get(resource_data_url).json()
        resource_value_path = permission_info['resource']['value'].strip().split('.')

        resource_val = self.get_value_to_compare(self, response, resource_value_path)
        compare_result = True if permission_info['subject']['value'] in resource_val else False

        if compare_result and action in permission_info['action']:
            grant_access = True

        return grant_access

    def subject_resource_compare(self, settings, access_request, permission_info):

        grant_access = False

        action = access_request['action']

        subject_id = access_request['subject']['subject_id']
        subject_data_api = permission_info['subject']['subject_api']
        subject_data_url = settings['API_'+subject_data_api] + 'get/' + subject_id+'?path=true'
        subject_response = requests.get(subject_data_url).json()
        subject_value_path = permission_info['subject']['value'].strip().split('.')

        subject_val = self.get_value_to_compare(self, subject_response, subject_value_path)

        resource_id = access_request['resource']['resource_id']
        resource_data_api = permission_info['resource']['resource_api']
        resource_data_url = settings['API_'+resource_data_api] + 'get/' + resource_id
        resource_response = requests.get(resource_data_url).json()
        resource_value_path = permission_info['resource']['value'].strip().split('.')     

        resource_val = self.get_value_to_compare(self, resource_response, resource_value_path)

        compare_result = True if set(subject_val) & set(resource_val) else False

        if not compare_result and permission_info['options']['recurrsive'] != {}:
            check_depth = permission_info['options']['recurrsive']
            rec_subject_val = [x for x in subject_val]
            rec_resource_val = [y for y in resource_val]

            if check_depth['subject'] != {}:
                for val in subject_val:
                    rec_subject_data_api = check_depth['subject']['subject_api']
                    rec_subject_data_url = settings['API_'+rec_subject_data_api] + 'get/' + val+'?path=true'
                    rec_subject_response = requests.get(rec_subject_data_url).json()
                    rec_subject_value_path = check_depth['subject']['value'].strip().split('.')

                    if rec_subject_data_api == 'BIM':
                        rec_subject_response = rec_subject_response[val]

                    rec_subject_val.extend(self.get_value_to_compare(self, rec_subject_response, rec_subject_value_path))

            if check_depth['resource'] != {}:
                for val in resource_val:
                    rec_resource_data_api = check_depth['resource']['resource_api']
                    rec_resource_data_url = settings['API_'+rec_resource_data_api] + 'get/' + val+'?path=true'
                    rec_resource_response = requests.get(rec_resource_data_url).json()
                    rec_resource_value_path = check_depth['resource']['value'].strip().split('.')

                    if rec_resource_data_api == 'BIM':
                        rec_resource_response = rec_resource_response[val]

                    rec_resource_val.extend(self.get_value_to_compare(self, rec_resource_response, rec_resource_value_path))

            compare_result = True if set(rec_subject_val) & set(rec_resource_val) else False               


        if compare_result and action in permission_info['action']:
            grant_access = True
                    
        return grant_access

    def get_value_to_compare(self, resource_response, attribute_value_path):        

        attribute_val = None

        if len(attribute_value_path) == 1:
            attribute_val = resource_response[attribute_value_path[0]]
            if type(attribute_val) != list:
                attribute_val = [attribute_val]
        else:
            attribute_val = resource_response[attribute_value_path[0]]

            if type(attribute_val) == list:
                for i in len(attribute_val):
                    for key in attribute_value_path[1:]:
                        attribute_val[i] = attribute_val[i][key]
            
            if type(attribute_val) == dict:
                for i in attribute_val.keys():
                    for key in attribute_value_path[1:]:
                        attribute_val[i] = attribute_val[i][key]
                attribute_val = list(attribute_val.values())                
            else:
                for key in attribute_value_path[1:]:
                    attribute_val = attribute_val[key]
                attribute_val = list(attribute_val.values())

        return attribute_val