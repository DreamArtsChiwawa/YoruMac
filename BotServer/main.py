#!/usr/bin/python
# coding: UTF-8
import os
import json
import requests
import csv
# import recognize
from flask import Flask, request
import filtering2
import summary_generator

app = Flask(__name__)
env = os.environ

@app.route('/messages', methods=['POST'])
def messages():
    if is_request_valid(request):
        summary = summary_generator.summary_generator()
        print id(summary)
        body = request.get_json(silent=True)
        companyId = body['companyId']
        msgObj = body['message']
        groupId = msgObj['groupId']
        messageText = msgObj['text']
        # messages = messageText.split()
        userName = msgObj['createdUserName']
        
        print type(messageText)
        messageToSummaryGen = messageText.encode('utf-8')
        print type(messageToSummaryGen)
        
        result = summary.input_department(messageToSummaryGen)
        
        result = result.replace(" ", "")
        result = result.replace("　", "")
        result = result.replace("■課題・問題・トラブル", "\n■課題・問題・トラブル\n")
        result = result.replace("■総括", "\n■総括\n")
        result = result.replace("■Highlight", "\n■Highlight\n")
        result = result.replace("■Other Activity", "\n■Other Activity\n")
        result = result.replace("■OtherActivity", "\n■OtherActivity\n")
        result = result.replace("■AR", "\n■AR\n")
        result = result.replace("■AR (Action Required)", "\n■AR (Action Required)\n")
        result = result.replace("■次週の指針、メッセージ", "\n■次週の指針、メッセージ\n")
        
        """
        if len(messages) == 1:
            result = sfiltering2.sendMecab(str(messages[0]), None)
        else:
            result = filtering2.sendMecab(str(messages[0]), str(messages[1]))
        """

        send_message(companyId, groupId, userName + 'さん、'.decode('utf-8') + result.decode('utf-8'))
        return "OK"
    else:
        return "Request is not valid."

# Check if token is valid.
def is_request_valid(request):
    # validationToken = env['Chiwawa-Webhook-Token']
    validationToken = env['CHIWAWA_VALIDATION_TOKEN']
    requestToken = request.headers['X-Chiwawa-Webhook-Token']
    return validationToken == requestToken

# Send message to Chiwawa server
def send_message(companyId, groupId, message):
    url = 'https://{0}.chiwawa.one/api/public/v1/groups/{1}/messages'.format(companyId, groupId)
    headers = {
        'Content-Type': 'application/json',
        'X-Chiwawa-API-Token': env['CHIWAWA_API_TOKEN']
    }
    content = {
        'text': message.encode('utf-8')
    }
    requests.post(url, headers=headers, data=json.dumps(content))


if __name__ == '__main__':
    app.run(host='', port=80, debug=True)
