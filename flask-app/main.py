# Author: Tanvi P
'''
Initializing the flask app to run on a specific port, making it easier to run for prod deployments in a containerized environment
'''

import app
if __name__ == '__main__':
      app.run(host='0.0.0.0', port=80)
