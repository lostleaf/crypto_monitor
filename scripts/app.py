from flask import Flask, jsonify, request
from flask_compress import Compress

import apis

_METHODS = ['GET', 'POST']
app = Flask(__name__)
compress = Compress()
compress.init_app(app)


@app.route('/', methods=_METHODS)
def hello_world():
    return 'Hello, World!'


# For debug usage
def print_request(req):
    print("==========req info============")
    print("HEADER:")
    print(req.headers)
    print("JSON:")
    print(req.get_json())
    print("============end===================")


@app.route('/search', methods=_METHODS)
def search():
    print_request(request)
    req = request.get_json()

    # target = req.get('target', '*')
    # if target == '':
    #     target = '*'

    # if ':' in target:
    #     finder, target = target.split(':', 1)
    # else:
    #     finder = target

    # print('finder =', finder, 'target =', target)

    # if not target or finder not in ROUTE:
    #     results = list(ROUTE.keys()) if target == '*' else []
    # else:
    #     results = list(ROUTE[finder](target))

    return jsonify([])


@app.route('/query', methods=_METHODS)
def query():
    print_request(request)
    req = request.get_json()
    results = []
    targets = req['targets']
    for t in targets:
        target = t['target']
        result = getattr(apis, target)()
        if isinstance(result, list):
            results.extend(result)
        else:
            results.append(result)
    return jsonify(results)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3003, threaded=False, debug=True)
