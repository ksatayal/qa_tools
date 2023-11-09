import falcon
import json

# {{{ class RequireJSON(object):
class RequireJSON(object):

    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                'This API only supports responses encoded as JSON.',
                href='http://docs.examples.com/api/json')

        if req.method in ('POST'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON. but now passing {}'.format(req.content_type),
                    href='http://docs.examples.com/api/json')

# }}}

# {{{ class JSONTranslator(object):
class JSONTranslator(object):
    # NOTE: Starting with Falcon 1.3, you can simply
    # use req.media and resp.media for this instead.

    def process_request(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        # See also: PEP 3333
        if req.content_length in (None, 0):
            # Nothing to do
            return

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.context['doc'] = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

        if 'temp_file_names'not in resp.context:
            resp.context['temp_file_names'] = []

    #def process_response(self, req, resp, resource):
    def process_response(self, req, resp, resource, req_succeeded):
        if 'jsstr_result' in resp.context:
            resp.text = resp.context['jsstr_result']
            return

        if 'result' not in resp.context:
            return

        if 'temp_file_names' in resp.context:
            [ os.remove(tf) for tf in resp.context['temp_file_names'] if os.path.exists(tf) ]

        resp.text = json.dumps(resp.context['result'])
# }}}
