import collections
import configparser
import hashlib
import hmac
import os
import typing

from datetime import datetime
from requests.auth import AuthBase
from urllib.parse import quote, urlparse
from requests.models import PreparedRequest

PWN: typing.TypeVar = typing.TypeVar('PWN')
ENCODING: str = 'utf-8'

AMZDATE_FORMATE: str = '%Y%m%dT%H%M%SZ'
DATESTAMP_FORMATE: str = '%Y%m%d'
QUOTE_SAFE_CHARS: str = '/-_.~'

class AWSAuth(AuthBase):
    def _load_aws_context(self: PWN) -> typing.Dict[str, str]:
        parser = configparser.ConfigParser()
        with open(os.path.expanduser('~/.aws/credentials'), 'r') as stream:
            parser.read_string(stream.read())

        aws_access_key: str = parser.get('default', 'aws_access_key_id')
        aws_secret_key: str = parser.get('default', 'aws_secret_access_key')
        aws_region: str = parser.get('default', 'region')
        aws_service: str = 's3'

        aws_context = collections.namedtuple('AWSContext', ['access_key', 'secret_key', 'region', 'service'])
        return aws_context(aws_access_key, aws_secret_key, aws_region, aws_service)

    _request_payer: bool = False
    def __init__(self: PWN, request_payer: bool = False) -> None:
        self._request_payer = request_payer

    def _get_canonical_headers(self: PWN, timestamp: datetime, host: str) -> str:
        headers: typing.Dict[str, str] = {
            'host': host,
            'x-amz-date': timestamp.strftime(AMZDATE_FORMATE)
        }
        if self._request_payer:
            headers['x-amz-request-payer'] = 'requester'

        ordered_headers: typing.List[str] = []
        ordered: typing.List[str] = []
        for key in sorted(headers.keys()):
            ordered_headers.append(key)
            ordered.append(f'{key}:{headers[key]}')

        ordered_headers: str = ';'.join(ordered_headers)
        ordered: str = '\n'.join(ordered)
        return ordered_headers, f'{ordered}\n'

    def _get_canonical_querystring(self: PWN, request: PreparedRequest) -> str:
        url_parts = urlparse(request.url)
        if url_parts.query == '':
            return ''

        # https://github.com/DavidMuller/aws-requests-auth/blob/969bc643f8386bc796c30d71e78c59af7f82f6b2/aws_requests_auth/aws_auth.py#L202
        raise NotImplementedError
        sorted_querystring: str = sorted(url_parts.query.split('&'))
        import pdb; pdb.set_trace()
        pass

    def _get_canonical_url(self: PWN, request: PreparedRequest) -> str:
        url_parts = urlparse(request.url)
        if url_parts.path:
            return quote(url_parts.path, safe=QUOTE_SAFE_CHARS)

        return quote('/', safe=QUOTE_SAFE_CHARS)

    def _get_payload_hash(self: PWN, request: 'request') -> str:
        payload_body = request.body or bytes()
        try:
            payload_body = payload_body.encode('utf-8')
        except (AttributeError, UnicodeDecodeError):
            pass

        return hashlib.sha256(payload_body).hexdigest()

    def _sign(self: PWN, key: typing.Union[str, bytes], value: str) -> bytes:
        if isinstance(key, str):
            key: bytes = key.encode(ENCODING)

        return hmac.new(key, value.encode(ENCODING), hashlib.sha256).digest()

    def _get_signature_key(self: PWN, key: str, timestamp: datetime, region: str, service: str) -> bytes:
        kDate: str = self._sign(f'AWS4{key}', timestamp.strftime(DATESTAMP_FORMATE))
        kRegion: str = self._sign(kDate, region)
        kService: str = self._sign(kRegion, service)
        kSigning: str = self._sign(kService, 'aws4_request')
        return kSigning

    def __call__(self: PWN, request: 'request') -> 'request':
        timestamp = datetime.utcnow()
        aws_context = self._load_aws_context()
        request_host: str = urlparse(request.url).netloc

        payload_hash = self._get_payload_hash(request)
        signed_headers, canonical_headers = self._get_canonical_headers(timestamp, request_host)
        canonical_request = '\n'.join([
            request.method,
            self._get_canonical_url(request),
            self._get_canonical_querystring(request),
            canonical_headers,
            signed_headers,
            payload_hash,
        ])

        algorithm: str = 'AWS4-HMAC-SHA256'
        credential_scope: str = f'{timestamp.strftime(DATESTAMP_FORMATE)}/{aws_context.region}/{aws_context.service}/aws4_request'

        hashed_request: str = hashlib.sha256(canonical_request.encode(ENCODING)).hexdigest()
        string_to_sign = f'{algorithm}\n{timestamp.strftime(AMZDATE_FORMATE)}\n{credential_scope}\n{hashed_request}'

        signing_key = self._get_signature_key(aws_context.secret_key, timestamp, aws_context.region, aws_context.service)
        signature = hmac.new(
            signing_key,
            string_to_sign.encode(ENCODING),
            hashlib.sha256).hexdigest()

        auth_header = f'{algorithm} Credential={aws_context.access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}'
        request.headers['Authorization'] = auth_header
        request.headers['x-amz-date'] = timestamp.strftime('%Y%m%dT%H%M%SZ')
        request.headers['x-amz-content-sha256'] = payload_hash
        if self._request_payer:
            request.headers['x-amz-request-payer'] = 'requester'

        return request
