"""
Generic AWS Lambda function to respond quotes
"""

import random
import boto3
from boto3.dynamodb.conditions import Key, Attr


ALEXA_SDK_REGION = 'us-east-1'
SKILLS_DB = 'AlexaSkillSayings'
CONFIG_DB = 'AlexaSkillConfigs'

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': getConfig()['version'],
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could add those here """

    session_attributes = {}
    card_title = "Welcome"
    usage_output = getConfig()['usageText']
    speech_output = getConfig()['spokenName'] + " " + usage_output
    reprompt_text = usage_output
    should_end_session = False
    speechlet_response = build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session)
    return build_response(session_attributes, speechlet_response)


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = getConfig()['endingText']
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))


def get_card_data_dynamo(intent, session):
    session_attributes = {}
    card_title = getConfig()['cardTitle']
    reprompt_text = ""
    should_end_session = True
    saying = random.choice(getSayings())
    speech_output = "%s" % (saying)

    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """
    Called when the session starts
    """

    print("on_session_started requestId=" + session_started_request['requestId'] + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """
    Called when the user launches the skill without specifying what they want
    """

    print("on_launch requestId=" + launch_request['requestId'] + ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """
    Called when the user specifies an intent for this skill
    """

    print("on_intent requestId=" + intent_request['requestId'] + ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    myIntent = getConfig()['intent']
    print("comparing '%s' to '%s'." % (intent_name, myIntent))
    
    # Dispatch to your skill's intent handlers
    if intent_name == myIntent:
        return get_card_data_dynamo(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """
    Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] + ", sessionId=" + session['sessionId'])
    # add cleanup logic here



_APP_ID = None # this must be set before getConfig() is called

# --------------- Main handler ------------------

def lambda_handler(event, context):
    """
    Route the incoming request based on type (LaunchRequest, IntentRequest, etc.) The JSON body of the request is provided in the event parameter.
    """
    global _APP_ID
    session = event['session']
    _APP_ID = session['application']['applicationId']
    print("event.session.application.applicationId=" + _APP_ID)

    if getConfig() is None:
        raise ValueError("Invalid Application ID")
    
    if session['new']:
        on_session_started({'requestId': event['request']['requestId']},session)
        
    request = event['request']
    if request['type'] == "LaunchRequest":
        return on_launch(request, session)
    elif request['type'] == "IntentRequest":
        return on_intent(request, session)
    elif request['type'] == "SessionEndedRequest":
        return on_session_ended(request, session)


_CONFIG = None
_SAYINGS = None
_SESSION = None

def __getSession():
    '''
    internal helper, need to switch config in test vs. production
    '''
    global _SESSION
    if _SESSION is not None:
        return _SESSION
    session = boto3.Session()
    #session = boto3.Session(region_name=ALEXA_SDK_REGION)
    #session = boto3.Session(profile_name='bob.brandt')
    _SESSION = session
    return _SESSION


def getConfig():
    '''
    return config data for this skill, will throw if the skill isn't mapped in the config
    counts on _APP_ID having already been set
    '''
    global _CONFIG
    if _CONFIG:
        return _CONFIG
    session = __getSession()
    client = session.client('dynamodb')
    response = client.scan(
        TableName=CONFIG_DB,
        AttributesToGet=['Skill','config'],
    )
    for respItem in response['Items']:
        cfg = respItem['config']['M']
        if cfg['appId']['S'] == _APP_ID:
            cleanCfg = {}
            cfgParams = [
                'spokenName',
                'usageText',
                'endingText',
                'cardTitle',
                'intent',
                'version']
            for k in cfgParams:
                cleanCfg[k] = cfg[k]['S']
            cleanCfg['skillName']  = respItem['Skill']['S']
            _CONFIG = cleanCfg
            break
    return _CONFIG

def _clearCache():
    '''
    just for testing purposes
    '''
    global _CONFIG, _SAYINGS
    _CONFIG = None
    _SAYINGS = None
    

def getSayings():
    '''
    return all sayings for the invoked skill
    '''
    global _SAYINGS
    if _SAYINGS is not None:
        return _SAYINGS
    session = __getSession()
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table(SKILLS_DB)
    response = table.query(
        KeyConditionExpression=Key('Skill').eq(getConfig()['skillName'])
    )
    
    sayingsList = []
    for respItem in response['Items']:
        saying = respItem['Saying']
        sayingsList.append(saying)
    _SAYINGS = sayingsList
    return _SAYINGS
