'''
Jon Parker Brooks - 8/13/24

This program is for simply getting some quick stats
using only the most recent nginx access.log file.

Things I'm interested in:
- IP addresses visited + frequency + total visits
- top 3 Most viewed pages + top 3 IPs visiting them
- list any and every POST that happens
- total bytes sent/recv by a user

v2: 9/2/24
- find a way to use a custom log format to make my code cleaner
  - $remote_addr "$time_iso8601" "$request" $status $bytes_sent "$http_user_agent" "$request_body"
  - ip timestamp request status bytes agent & body are the only things relevant to my service for now
  - apache probably supports this as well, need to double check tho, added README for nginx instructions

- Need to restructure project, making into a module (multiple files)
'''

# v1 -> v2 functions
# i'll use these at some point...

'''
def parse_http_request(text: str) -> dict:
    
    keys = ('method', 'route', 'proto')
    parts = text.split(' ')
    
    if len(parts) != 3:
        parts = ('-', ) * 3 # if unparsable just display -

    return dict(zip(keys, parts))


def normalize_bytes(number: int) -> str:
    
    if number > 1000000000:
        return f'{round(number / 1000000000)} GB'
    if number > 1000000:
        return f'{round(number / 1000000)} MB'
    if number > 1000:
        return f'{round(number / 1000)} KB'
'''