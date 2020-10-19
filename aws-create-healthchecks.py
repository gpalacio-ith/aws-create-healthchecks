#!/usr/bin/env python3

import boto3
import json
import csv
import random
import string

# apply changes or just test
# TRUE for testing
dry_run = True
file_name = 'test_new_healthchecks.csv'

def read_csv_file(file_name):
    list_of_hc = []
    try:
        with open(file_name, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                new_hc = {
                    'hc_fqdn': row[0],
                    'hc_type': row[1],
                    'hc_path': row[2],
                    'hc_ip': row[3],
                    'hc_name': row[4]
                }
                list_of_hc.append(new_hc)
        return(list_of_hc)
    except FileNotFoundError:
        print(f'>>> ERROR! File "{file_name}" could not be found...')

def read_user_input():
    yes = {'yes','y', 'ye', ''}
    no = {'no','n'}
    user_input = ''
    while user_input not in yes or user_input not in no:
        user_input = input().lower()
        if user_input in yes:
           return True
        elif user_input in no:
           return False
        else:
           print("Please respond with 'y|yes' or 'n|no':", end=' ')

def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return(result_str)

# HealthCheckConfig={
#         'IPAddress': 'string',
#         'Type': ,
#         'ResourcePath': 'string',
#         'FullyQualifiedDomainName': 'string',
#         'Inverted': False,
#         'EnableSNI': True,
#         'Regions': [
#             'us-east-1','us-west-1','us-west-2','eu-west-1',
#         ]
#     }
def create_healthchecks(healthcheck_list, client):
    caller_ref_id = 'python-3.8_script_aws-create-healthchecks.py'

    # every healthcheck on the list
    for each_hc in healthcheck_list:
        HealthCheckConfig={
            'IPAddress': each_hc['hc_ip'],
            'Type': each_hc['hc_type'],
            'ResourcePath': each_hc['hc_path'],
            'FullyQualifiedDomainName': each_hc['hc_fqdn'],
            'Inverted': False,
            'EnableSNI': True,
            'Regions': [
                'us-east-1','us-west-1','us-west-2','eu-west-1'
            ]
        }

        # adds it to route53
        caller_id = caller_ref_id + get_random_alphanumeric_string(6)
        response_new_hc = client.create_health_check(
            CallerReference=caller_id,
            HealthCheckConfig=HealthCheckConfig
        )

        # update healthcheck name using the just created id
        new_hc_id = response_new_hc['HealthCheck']['Id']
        response_new_name = client.change_tags_for_resource(
            ResourceType='healthcheck',
            ResourceId=new_hc_id,
            AddTags=[
                {
                    'Key': 'Name',
                    'Value': each_hc['hc_name']
                }
            ]
        )
        testing_hc_name = each_hc['hc_name']
        print(f'+ Healthcheck created: {new_hc_id} {testing_hc_name}')



# main code
def main():
    # reads healthcheck info from csv file
    new_hc_to_create = read_csv_file(file_name)

    # prints healthchecks that will be created for review
    print('> The following healthchecks will be created...')
    print('> please read through the following to make sure everything is okay before proceeding.\n')
    print(json.dumps(new_hc_to_create, indent=4))
    print('\n> Do you wish to proceed? [y/n]', end=' ')
    read_user_input()

    # creates aws api sessions params
    session = boto3.session.Session(profile_name='aws-prd')
    client = session.client('route53')

    dry_run = False
    # create healthchecks if not dry run
    if not dry_run:
        print('> Creating healthchecks... \n')
        create_healthchecks(new_hc_to_create, client)
        print('Healthchecks created.')

if __name__ == '__main__':
    main()