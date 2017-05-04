"""
Generic AWS Lambda function to respond quotes
"""

import random
import boto3
from boto3.dynamodb.conditions import Key, Attr


SKILL_CONFIGS = \
{
    'ConfuciusSays': {
        'spoken_name': 'Confucius Says',
        'usage_text':  'invoke me by saying say something profound',
        'ending_text': 'Confucius Says you are now more wise.',
        'card_title':  'Confucius Says these wise words',
        'intent':      'GetConfucius',
        'version':     1.1,
    },
    'BossyBoots': {
        'spoken_name': 'Bossy Boots',
        'usage_text':  "invoke me by saying tell me what's up",
        'ending_text': 'Bossy Boots says you are welcome.',
        'card_title':  "Bossy Boots tells you what's up",
        'intent':      'BeBossed',
        'version':     1.0,
    },
    'DebbieDowner': {
        'spoken_name': 'Debbie Downer',
        'usage_text':  'invoke me by saying how are you?',
        'ending_text': "Debbie Downer isn't sure how, but try to have a nice day.",
        'card_title':  'Debbie Downer feins a smile.',
        'intent':      'GetDown',
        'version':     1.0,
    },
    'RomanticRobot': {
        'spoken_name': 'Romantic Robot',
        'usage_text':  'invoke me by saying whisper sweet nothings.',
        'ending_text': 'Romantic Robot has closed the connection.',
        'card_title':  'You are now connected to Romantic Robot',
        'intent':      'BeRomanced',
        'version':     1.0,
    },
}

ALEXA_SDK_REGION = 'us-east-1'


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
    usage_output = getConfig()['usage_text']
    speech_output = getConfig()['spoken_name'] + " " + usage_output
    reprompt_text = usage_output
    should_end_session = False
    speechlet_response = build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session)
    return build_response(session_attributes, speechlet_response)


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = getConfig()['ending_text']
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))


def get_card_data_dynamo(intent, session):
    session_attributes = {}
    card_title = getConfig()['card_title']
    reprompt_text = ""
    should_end_session = True

    session = boto3.Session() ### use this one in production
    #session = boto3.Session(region_name=ALEXA_SDK_REGION)
    #session = boto3.Session(profile_name='bob.brandt') ### use this one for local testing
    dynamodb = session.resource('dynamodb')
    table = dynamodb.Table('AlexaSkillSayings')
    
    response = table.query(
        KeyConditionExpression=Key('Skill').eq(getConfig()['skill_name'])
    )
    
    sayingsList = []
    for respItem in response['Items']:
        saying = respItem['Saying']
        sayingsList.append(saying)

    saying = random.choice(sayingsList)
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

    # Dispatch to your skill's intent handlers
    if intent_name == getConfig()['intent']:
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


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """
    Route the incoming request based on type (LaunchRequest, IntentRequest, etc.) The JSON body of the request is provided in the event parameter.
    """
    global SKILL
    session = event['session']
    appID = session['application']['applicationId']
    print("event.session.application.applicationId=" + appID)

    skillsMap = {
        'amzn1.ask.skill.a4d4a968-e240-46a6-94c0-35142f537381':'ConfuciusSays',
        'amzn1.ask.skill.a4d4a968-e240-46a6-94c0-35142f537382':'BossyBoots',
        'amzn1.ask.skill.a4d4a968-e240-46a6-94c0-35142f537383':'DebbieDowner',
        'amzn1.ask.skill.a4d4a968-e240-46a6-94c0-35142f537384':'RomanticRobot',
        }
    SKILL = skillsMap.get(appID, None)
    if (SKILL is None):
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


def getConfig():
    '''
    return config data for this skill, will throw if the skill isn't mapped in the config
    '''
    cfg = SKILL_CONFIGS[SKILL]
    cfg['skill_name'] = SKILL
    return cfg
