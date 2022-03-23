#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import flask
from flask import Flask, request
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()
        
    def add_set_listener(self, listener):
        self.listeners.append( listener )

    def remove_listener(self, listener):
        self.listeners.remove(listener)

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners( entity )

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners( entity )

    def update_listeners(self, entity):
        '''update the set listeners'''
        for listener in self.listeners:
            listener.send(json.dumps({entity:self.get(entity)}))

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self):
        return self.space

myWorld = World()        

def set_listener( entity, data ):
    ''' do something with the update ! '''
    data = entity

#myWorld.add_set_listener( set_listener )
        
@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    return flask.Response(status=301, headers={"Location" : "http://localhost:8000/static/index.html", "Access-Control-Allow-Origin" : "*"})

def read_ws(ws,client):
    '''A greenlet function that reads from the websocket and updates the world'''
    # XXX: TODO IMPLEMENT ME
    return None

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    # XXX: TODO IMPLEMENT ME
    ws.send(json.dumps(myWorld.world()))
    myWorld.add_set_listener(ws)
    try:
        while True:
            msg = ws.receive()
            if msg != None:
                msg = json.loads(msg)
                myWorld.set(list(msg.keys())[0], msg[list(msg.keys())[0]])
    except Exception as e:
        myWorld.remove_listener(ws)

# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])

@app.route("/entity/<entity>", methods=['POST','PUT','OPTIONS'])
def update(entity):
    # handle pre-flight request
    if request.method == 'OPTIONS':
        response = flask.Response()
        response.access_control_allow_headers = ["content-type"]
        response.access_control_allow_origin = "*"
        return response

    '''update the entities via this interface'''
    # Get the json body
    data = flask_post_json()

    # Update the entity
    myWorld.set(entity, data)

    return flask.Response(status=200, headers={"Access-Control-Allow-Origin" : "*"}, content_type="application/json", response=json.dumps(myWorld.get(entity)))

@app.route("/world", methods=['POST','GET','OPTIONS'])    
def world():
    # handle pre-flight request
    if request.method == 'OPTIONS':
        response = flask.Response()
        response.access_control_allow_headers = ["content-type"]
        response.access_control_allow_origin = "*"
        return response

    '''you should probably return the world here'''
    response = flask.Response(status=200, content_type="application/json", response=json.dumps(myWorld.world()))
    response.access_control_allow_origin = "*"
    return response

@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    response = flask.Response(status=200, headers={"Access-Control-Allow-Origin" : "*"}, content_type="application/json", response=json.dumps(myWorld.get(entity)))
    return response

@app.route("/clear", methods=['POST','GET','OPTIONS'])
def clear():
    # handle pre-flight request
    if request.method == 'OPTIONS':
        response = flask.Response()
        response.access_control_allow_headers = ["content-type"]
        response.access_control_allow_origin = "*"
        return response

    '''Clear the world out!'''
    myWorld.clear()
    return flask.Response(status=200, headers={"Access-Control-Allow-Origin" : "*"}, content_type="application/json", response=json.dumps(myWorld.world()))



if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
