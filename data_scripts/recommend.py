import pandas as pd
import boto3
import json

def recommend(username, user_speed):
    print('Recommend Start')
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    payload = {'username': username,
    'user_speed': user_speed}
    response = lambda_client.invoke(FunctionName='recommend', 
                                    InvocationType='RequestResponse',   
                                    Payload=json.dumps(payload))
    x = json.loads(json.loads(response['Payload'].read().decode('utf-8'))['body'])
    print('Recommend End')
    try:
        return pd.DataFrame(x['recommendations'])
    except:
        return None