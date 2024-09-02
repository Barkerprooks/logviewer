# Log Viewer
A python script for tailing and displaying useful stats for a structured log file

## Nginx
Put this in the `http` section under your config file. usually found under `/etc/nginx/nginx.conf`.
You can replace the word `website` with something more fitting to the service
``` 
http {
    ...

    log_format website escape=json '$remote_addr "$time_iso8601" '
        '"$request" $status $bytes_sent '
        '"$http_user_agent" "$request_body"';
    ...
}
```
Under the server section for the desired service
```
server {
    ...
    location / {
        ...
        access_log /var/log/nginx/website.log website
    }
}
```