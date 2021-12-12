Review write-up.md for howto.

## next steps

- celery or rabbitmq instead of many threads?
- set it up as static IP
    - https://pimylifeup.com/raspberry-pi-static-ip-address/
        - give dns to router somehow?
        - `ip r | grep default`
        - `default via 192.168.1.1 dev wlan0 proto dhcp src 192.168.1.16 metric 303`
        - nameserver: 192.168.1.1
- dockerization
    - docker build .
    - docker run -it (to get into the container)
