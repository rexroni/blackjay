from flask import Flask
from flask_restful import abort, Api, Resource
import os
import sys
import json

class MetadataAPI(Resource):
    def get(self, base_dir):
        if os.path.isdir(os.path.join(base_dir, '.blackjay')):
            return json.dumps(os.path.join(base_dir, '.blackjay/metadata'))
        else:
            abort(404, message="Base Directory {} doesn't exist".format(base_dir))


def main():
    port = 12345 # default value
    host = '0.0.0.0' # externally visible server

    if len(sys.argv) > 1:
        os.chdir(sys.argv[1])
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    if len(sys.argv) > 3:
        host = sys.argv[3]


    app = Flask(__name__)
    api = Api(app)

    api.add_resource(MetadataAPI, '/<string:base_dir>/metadata')

    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    main()