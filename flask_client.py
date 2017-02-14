import requests
from requests_toolbelt import MultipartEncoder

metadata_req = requests.get('http://0.0.0.0:12345/s/.blackjay/metadata')
print metadata_req.content

url = 'http://0.0.0.0:12345/s/.blackjay/update'
uploadfile = open('c2s.zip', 'rb')
print uploadfile.name
payload = MultipartEncoder({uploadfile.name: (uploadfile.name, uploadfile, 'application/x-compressed')})

update_req = requests.post(url, data=payload, headers={'Content-Type': payload.content_type})
print update_req