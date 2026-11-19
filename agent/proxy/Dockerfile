FROM alpine:3.20
RUN apk add --no-cache tinyproxy
COPY tinyproxy.conf allowlist.txt /etc/tinyproxy/
RUN sed -i 's/\r$//' /etc/tinyproxy/tinyproxy.conf /etc/tinyproxy/allowlist.txt
CMD ["tinyproxy", "-d"]