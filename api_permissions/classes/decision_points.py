
import requests
from datetime import date, datetime

class DecisionPoints(object):

    def resource_list_compare(self, settings, access_request, permission_info):
        grant_access = False

        action = access_request['action']

        # Check if permission is available for the requested action
        if action not in permission_info['action']:
            return grant_access

        # Check if the permission is available at the current time
        if 'time_check' in permission_info['options']:
            time_access = self.time_check(self, permission_info['options']['time_check'])
            if not time_access:
                return grant_access

        resource_id = access_request['resource']['resource_id']
        if permission_info['resource']['resource_type'] == 'url':
            resource_id = '/'.join(resource_id.split('__'))
        resource_val = permission_info['resource']['value']

        if resource_id in resource_val:
            grant_access = True

        return grant_access
    
    def resource_check(self, settings, access_request, permission_info):

        grant_access = False

        subject_id = access_request['subject']['subject_id']
        action = access_request['action']

        # Check if permission is available for the requested action
        if action not in permission_info['action']:
            return grant_access

        # Check if the permission is available at the current time
        if 'time_check' in permission_info['options']:
            time_access = self.time_check(self, permission_info['options']['time_check'])
            if not time_access:
                return grant_access

        # Get resource values to compare
        resource_data_api = permission_info['resource']['resource_api']
        resource_data_url = settings['API_'+resource_data_api] + 'get/' + subject_id
        response = requests.get(resource_data_url).json()
        resource_value_path = permission_info['resource']['value'].strip().split('.')

        if resource_data_api == 'BIM' and response != {}:
            response = response[subject_id]
            
        try:
            resource_val = self.get_value_to_compare(self, response, resource_value_path)
        except KeyError as e:
            print('KeyError: ',e)
            resource_val = []

        # Access is possible if the subject value is in resource value
        compare_result = True if permission_info['subject']['value'] in resource_val else False        

        if compare_result:
            grant_access = True

        return grant_access

    def subject_resource_compare(self, settings, access_request, permission_info):

        grant_access = False

        action = access_request['action']

        # Check if permission is available for the requested action
        if action not in permission_info['action']:
            return grant_access

        # Check if the permission is available at the current time
        if 'time_check' in permission_info['options']:
            grant_access = self.time_check(permission_info['options']['time_check'])
            if not grant_access:
                return grant_access

        # Check if resource has public access
        if 'public_access' in permission_info['options']:
            grant_access = self.public_access_check(self, permission_info, access_request)
            if grant_access:
                return grant_access        

        # Get subject values to compare
        subject_id = access_request['subject']['subject_id']
        subject_data_api = permission_info['subject']['subject_api']
        subject_data_url = settings['API_'+subject_data_api] + 'get/' + subject_id+'?path=true'
        subject_response = requests.get(subject_data_url).json()        

        subject_value_path = permission_info['subject']['value'].strip().split('.')

        try:
            subject_val = self.get_value_to_compare(self, subject_response, subject_value_path)
        except KeyError as e:
            print('KeyError: ',e)
            subject_val = []

        # Get resource values to compare
        resource_id = access_request['resource']['resource_id']
        resource_data_api = permission_info['resource']['resource_api']
        resource_data_url = settings['API_'+resource_data_api] + 'get/' + resource_id
        resource_response = requests.get(resource_data_url).json()        

        if resource_data_api == 'BIM' and resource_response != {}:
            resource_response = resource_response[resource_id]

        if 'institute_access' in permission_info['options'] and permission_info['subject']['subject_api'] == 'PEOPLE' and permission_info['resource']['resource_api'] == 'BIM':
            grant_access = self.institute_access_check(self, permission_info, subject_response, resource_id)
            if grant_access:
                return grant_access

        resource_value_path = permission_info['resource']['value'].strip().split('.')

        try:
            resource_val = self.get_value_to_compare(self, resource_response, resource_value_path)
        except KeyError as e:
            print('KeyError: ',e)
            resource_val = []

        # Access is possible if the set (subject_val & resouce_val) is not empty
        compare_result = True if set(subject_val) & set(resource_val) else False

        # Check if recurrsive check is required
        if not compare_result and 'recurrsive' in permission_info['options']:
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

                    # Append the parents to the subject_val
                    try:
                        rec_subject_val.extend(self.get_value_to_compare(self, rec_subject_response, rec_subject_value_path))
                    except KeyError as e:
                        print('KeyError: ',e)

            if check_depth['resource'] != {}:
                for val in resource_val:
                    rec_resource_data_api = check_depth['resource']['resource_api']
                    rec_resource_data_url = settings['API_'+rec_resource_data_api] + 'get/' + val+'?path=true'
                    rec_resource_response = requests.get(rec_resource_data_url).json()
                    rec_resource_value_path = check_depth['resource']['value'].strip().split('.')

                    if rec_resource_data_api == 'BIM' and rec_resource_response != {}:
                        rec_resource_response = rec_resource_response[val]
                    
                    # Append the parents to the resource_val
                    try:
                        rec_resource_val.extend(self.get_value_to_compare(self, rec_resource_response, rec_resource_value_path))
                    except KeyError as e:
                        print('KeyError: ',e)                        

            compare_result = True if set(rec_subject_val) & set(rec_resource_val) else False               
        
        if compare_result:
            grant_access = True
                    
        return grant_access



    ###########################################################################
    #
    # Support functions
    #
    ###########################################################################

    # Get the required value of an attribute
    def get_value_to_compare(self, resource_response, attribute_value_path):

        if resource_response == {}:
            return []      

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

    # Check if time-based access conditions are met
    def time_check(self, time_options):

        access_status = False

        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        now = datetime.now()

        day_list = time_options['day'] if 'day' in time_options else None

        if day_list:
            if weekdays[now.weekday()] not in day_list:
                return False
            else:
                access_status = True

        time_to_check = time_options['time'] if 'time' in time_options else None

        if time_to_check:
            time_condition = time_options['time_condition']
            dt_list = time_to_check.split(':')
            dt = datetime(now.year, now.month, now.day, int(dt_list[0]), int(dt_list[1]), int(dt_list[2]))

            if time_condition == 'equal':
                if now == dt:
                    access_status = True
                else:
                    access_status = False
            elif time_condition == 'pre':
                if now < dt:
                    access_status = True
                else:
                    access_status = False
            elif time_condition == 'post':
                if now > dt:
                    access_status = True
                else:
                    access_status = False
            else:
                access_status = False

        return access_status

    # Check if a resource is publically available
    def public_access_check(self, permission_info, access_request):

        public_access_list = permission_info['options']['public_access']

        resource_id = access_request['resource']['resource_id']

        if resource_id in public_access_list:
            return True
        
        return False

    def institute_access_check(self, permission_info, subject_response, resource_id):

        grant_access = False

        insts = subject_response['insts']

        inst_list = list(insts.keys())

        for key in insts:
            inst_list.extend(insts[key]['parents'])

        insts_to_compare = list(permission_info['options']['institute_access'].keys())

        compare_result = True if set(inst_list) & set(insts_to_compare) else False

        if compare_result:
            for inst in set(inst_list) & set(insts_to_compare):
                if resource_id in permission_info['options']['institute_access'][inst]:
                    grant_access = True
                    break
        
        return grant_access