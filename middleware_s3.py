#!/usr/bin/env python
"""
Generate AWS4 authentication headers for your protected files

This module is meant to plug into munki.
https://github.com/munki/munki/wiki

This is just a modified version of this
http://docs.aws.amazon.com/general/latest/gr/sigv4-signed-request-examples.html#sig-v4-examples-get-auth-header

"""
import datetime
import re
import socket
import hashlib
import hmac
# backwards compatibility for python2
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

# pylint: disable=E0611
from Foundation import CFPreferencesCopyAppValue
# pylint: enable=E0611

BUNDLE_ID = 'ManagedInstalls'
__version__ = '1.3'
METHOD = 'GET'
SERVICE = 's3'


def pref(pref_name):
    """Return a preference. See munkicommon.py for details
    """
    pref_value = CFPreferencesCopyAppValue(pref_name, BUNDLE_ID)
    return pref_value


ACCESS_KEY = pref('AccessKey')
SECRET_KEY = pref('SecretKey')
REGION = pref('Region')
S3_ENDPOINT = pref('S3Endpoint') or 's3.amazonaws.com'
# Your local server like my-munki.mycorp.com
S3_REWRITE_ENDPOINT = pref('S3RewriteEndpoint')

def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signature_key(key, datestamp, region, service):
    kdate = sign(('AWS4' + key).encode('utf-8'), datestamp)
    kregion = sign(kdate, region)
    kservice = sign(kregion, service)
    ksigning = sign(kservice, 'aws4_request')
    return ksigning


def uri_from_url(url):
    parse = urlparse(url)
    return parse.path


def host_from_url(url):
    parse = urlparse(url)
    return parse.hostname


def s3_auth_headers(url):
    """
    Returns a dict that contains all the required header information.
    Each header is unique to the url requested.
    """
    # Create a date for headers and the credential string
    time_now = datetime.datetime.utcnow()
    amzdate = time_now.strftime('%Y%m%dT%H%M%SZ')
    datestamp = time_now.strftime('%Y%m%d')  # Date w/o time, used in credential scope
    uri = uri_from_url(url)
    host = host_from_url(url)
    canonical_uri = uri
    canonical_querystring = ''
    canonical_headers = 'host:{}\nx-amz-date:{}\n'.format(host, amzdate)
    signed_headers = 'host;x-amz-date'
    payload_hash = hashlib.sha256(''.encode('utf-8')).hexdigest()
    canonical_request = '{}\n{}\n{}\n{}\n{}\n{}'.format(METHOD,
                                                        canonical_uri,
                                                        canonical_querystring,
                                                        canonical_headers,
                                                        signed_headers,
                                                        payload_hash)

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = '{}/{}/{}/aws4_request'.format(datestamp, REGION, SERVICE)
    hashed_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    string_to_sign = '{}\n{}\n{}\n{}'.format(algorithm,
                                             amzdate,
                                             credential_scope,
                                             hashed_request)

    signing_key = get_signature_key(SECRET_KEY, datestamp, REGION, SERVICE)
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    authorization_header = ("{} Credential={}/{},"
                            " SignedHeaders={}, Signature={}").format(algorithm,
                                                                      ACCESS_KEY,
                                                                      credential_scope,
                                                                      signed_headers,
                                                                      signature)

    headers = {'x-amz-date': amzdate,
               'x-amz-content-sha256': payload_hash,
               'Authorization': authorization_header}
    return headers

def check_rewrite_host():
    if not S3_REWRITE_ENDPOINT:
        return False
    try:
        socket.gethostbyname(S3_REWRITE_ENDPOINT)
        return True
    except socket.gaierror:
        return False

rewriter = None
if S3_REWRITE_ENDPOINT:
    rewriter = re.compile(r'^(http(?:s)://)(.*\.%s)' % re.escape(S3_ENDPOINT))

def rewrite_url(url):
    return rewriter.sub(r'\1%s' % S3_REWRITE_ENDPOINT, url)

def process_request_options(options):
    """Make changes to options dict and return it.
       This is the fuction that munki calls."""
    if S3_ENDPOINT in options['url']:
        if check_rewrite_host():
            options['url'] = rewrite_url(options['url'])
            print (options['url'])
        else:
            headers = s3_auth_headers(options['url'])
            options['additional_headers'].update(headers)
    return options
