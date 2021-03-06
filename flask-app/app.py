# Author: Tanvi P
'''
Flask server which serves as a backend for displaying the test results and give meta information about the network currently running
'''

from flask import Flask
import xmlrpc.client

app = Flask(__name__)
MONITOR_ADDRESS = "monitor-node:8000"
monitor_client =  xmlrpc.client.ServerProxy('http://' + MONITOR_ADDRESS + '/RPC2')

@app.route('/')
def hello():
    return 'Hello'

@app.route('/suspect_matrix')
def show():
    return str(monitor_client.getSuspectMatrix())


@app.route('/fault_vector')
def fault_vector():
    return str(monitor_client.getFaultVector())

@app.route('/status')
def status():
    return monitor_client.showAliveDeadNode()


@app.route('/results')
def show_results():
    return monitor_client.readFile()