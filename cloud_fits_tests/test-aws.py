import requests

from cloud_fits.auth import aws

url: str = 'https://s3.us-east-1.amazonaws.com/yoko-videos/awesome.txt'
response = requests.put(url, data=b'awesome', auth=aws.AWSAuth())
import ipdb; ipdb.set_trace()
pass
