import alexaSkillsLambda

def test():
    requestTemplate = {
        "session": {
            "sessionId": "SessionId.0630214e-4cbf-47b1-937e-7b5d7fe576be",
            "application": {
                "applicationId": ""
            },
            "attributes": {},
            "user": {
                "userId": "amzn1.ask.account.AFFIJZHUMKMUV3AC2237G4POF7VAVGIK3VTIW7UYFEXZEMLBTLIKDCBOL725W4X7ORLPI6JMXXKWQQPTHZEPXBWIN7COWQUDQYBZSJ42XBZE27ZGRHIFKBP7PWFD5UOCHGKEYALCC5VWTXPWWCK4QIPQDGLBJVXJWL2N4FGASOQWBH4WMO2OFWFU5ABKGDJLHBVAGSVL6I72E2Y"
            },
            "new": True
        },
        "request": {
            "type": "IntentRequest",
            "requestId": "EdwRequestId.4907a565-1b3d-4da9-9e94-87e73fbdb095",
            "locale": "en-US",
            "timestamp": "2017-01-13T14:37:34Z",
            "intent": {
                "name": "",
                "slots": {}
            }
        },
        "version": "1.0"
    }

    testCases = [
        ( 'amzn1.ask.skill.a4d4a968-e240-46a6-94c0-35142f537381', 'GetConfucius' ),
        ( 'amzn1.ask.skill.b60263d7-fbcd-431c-a0db-048a9dfd9cf7', 'BeBossed' ),
        ( 'amzn1.ask.skill.adda0355-c10a-4714-b80a-3d2d0064ecb0', 'GetDown' ),
        ( 'amzn1.ask.skill.97035895-5140-4628-8b62-37e33e00d10b', 'BeRomanced' ),
        ]
    for case in testCases:
        request = requestTemplate
        request['session']['application']['applicationId'] = case[0]
        request['request']['intent']['name'] = case[1]
        print(alexaSkillsLambda.lambda_handler(request,None))
    #print(alexaSkillsLambda.get_card_data_dynamo(None, None))

if __name__ == '__main__':
    test()
