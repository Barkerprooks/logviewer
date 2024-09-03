from collections.abc import Iterator
from shlex import split

def parse_log(line: bytes) -> dict:
    # input should be a line of the desired log file.
    return dict(
        zip(
            ( # > keys for values from line
                'ip', # address request "said" it came from
                'created', # timestamp
                'request', # example: GET / HTTP/1.1
                'response', # response status (200, 404, etc) 
                'bytes', # length of bytes in request 
                'user_agent', # how the user identified themselves
                'body' # POST body if there is any
            ), # > values (contents of line)
            split(line.decode('utf-8', 'replace').strip())
        )
    )


def parse_log_lines(path: str) -> Iterator[dict]:
    # utility function to read a file line by line an parse it into an iterator
    with open(path, 'rb') as file:
        for line in file.readlines():
            yield parse_log(line)