#!/usr/bin/env python3

import requests
import boto3
import json
from botocore.exceptions import ClientError

# separate file I'm using to store user access id and key for pool manger IAM
# not included in publically accessible version control
import hike_app_keys

pool_manager_id = hike_app_keys.COG_MANAGER_ID
pool_manager_key = hike_app_keys.COG_MANAGER_KEY

trail_key = hike_app_keys.TRAIL_KEY
trail_base_url = 'https://www.hikingproject.com/data/get-trails-by-id?ids='
weather_key = hike_app_keys.WEATHER_KEY
weather_base_url = "https://weatherbit-v1-mashape.p.rapidapi.com/forecast/daily"


##
# get_trail
#
# makes an API call to get name, location, and a url for
#   a specified trail
##
def get_trail(trail_id):
    # make a request based off the input ID
    req_url = trail_base_url + trail_id + '&key=' + trail_key
    resp = requests.get(req_url)

    # parse just the important data into a new dict
    trail_data = {}
    json_object = json.loads(resp.text)
    trail_data['name'] = json_object['trails'][0]['name']
    trail_data['url'] = json_object['trails'][0]['url']
    trail_data['lat'] = json_object['trails'][0]['latitude']
    trail_data['lon'] = json_object['trails'][0]['longitude']

    #print for debug
    print(json.dumps(trail_data, indent=2))

    return trail_data


##
# get_weather
#
# makes an API call to get the weather forcast for a 
#   given location and date
##
def get_weather(lat, lon, date):
    ret_data = {}

    # make query based input lat, lon
    querystring = {"units":"I","lang":"en","lat": str(lat),"lon": str(lon)}
    headers = {
            'x-rapidapi-host': "weatherbit-v1-mashape.p.rapidapi.com",
            'x-rapidapi-key': weather_key
            }
    resp = requests.request("GET", weather_base_url, headers=headers, params=querystring)
    json_object = json.loads(resp.text)

    # parse response for correct date
    for day in json_object['data']: 
        if date != day['valid_date']:
            continue
        else:
            ret_data['high_temp'] = str(day['high_temp'])
            ret_data['low_temp'] = str(day['high_temp'])
            ret_data['avg_temp'] = str(day['temp'])
            ret_data['weather'] = str(day['weather']['description'])

    return ret_data


##
# send_email
#
# sends the user an email with links and weather info
##
def send_email(username, app_data):
    # Get the recipient's user info
    cog_client = boto3.client('cognito-idp',
            aws_access_key_id=pool_manager_id,
            aws_secret_access_key=pool_manager_key)
    user = cog_client = cog_client.admin_get_user(UserPoolId=hike_app_keys.COG_POOL_ID, Username=username)
    user_fname = user['UserAttributes'][2]['Value']
    RECIPIENT = user['UserAttributes'][4]['Value']
    SENDER = "Hiker App <bens.hiker.app@gmail.com>"
    AWS_REGION = "us-east-1"
    CHARSET = "UTF-8"

    # fill in the email content with app data
    SUBJECT = "Hike Planner App - Your new hiking plan"
    BODY_TEXT = "Hi " + user_fname + ',' + "\n\n" + \
            "Here's some info on the hike you're planning:" + "\n\n" + \
            "Hike Start Date: \t\t\t\t\t" + app_data['start_date'] + "\n" + \
            "Name of the trail: \t\t\t\t\t" + app_data['trail_data']['name'] + "\n" + \
            "Link to trail maps: \t\t\t\t\t" + app_data['trail_data']['url'] + "\n" + \
            "Trail weather on " + app_data['start_date'] + ": \t\t\t" + app_data['weather_data']['weather'] + "\n" + \
            "Trail Avg temp on " + app_data['start_date'] + ": \t\t\t" + app_data['weather_data']['avg_temp'] + "\n" + \
            "Trail Low temp on " + app_data['start_date'] + ": \t\t\t" + app_data['weather_data']['low_temp'] + "\n" + \
            "Trail High temp on " + app_data['start_date'] + ": \t\t\t" + app_data['weather_data']['high_temp'] + "\n\n" + \
            "Happy Hiking!"

    client = boto3.client('ses',region_name=AWS_REGION)
    try:
        response = client.send_email(
                Destination={
                    'ToAddresses': [
                        RECIPIENT,
                        ],
                    },
                Message={
                    'Body': {
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                            },
                        },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                        },
                    },
                Source=SENDER,
                )

    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])



##
# lambda_handler
#
# wrapper for other functions, entry point for AWS lambda function
##
def lambda_handler(event, context):
    app_data = {}

    # pull date, trail, and user from event
    try: 
        user_params = json.loads(event['body'])
        start_date = user_params['StartDate']
        trail_id = user_params['TrailId']
        username = user_params['Username']
    except Exception as err:
        return {
            'statusCode': 502,
            'body': json.dumps('Error occured in request parameter processing: ' + str(err))
        }

    # make API calls
    app_data['start_date'] = start_date
    try:
        app_data['trail_data'] = get_trail(trail_id)
    except Exception as err:
        return {
            'statusCode': 502,
            'body': json.dumps('Error occured in Trail API request: ' + str(err))
        }

    try:
        app_data['weather_data'] = get_weather(app_data['trail_data']['lat'], app_data['trail_data']['lon'], start_date)
    except Exception as err:
        return {
            'statusCode': 502,
            'body': json.dumps('Error occured in Weather API request: ' + str(err))
        }

    # send final data to user
    send_email(username , app_data)

    return {
        'statusCode': 200,
        'body': json.dumps('Hike app call successful. Email should arrive shortly')
    }



