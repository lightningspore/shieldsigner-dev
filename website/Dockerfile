FROM caddy:2.11.3-alpine
# We bind unprivileged port 8080; remove the upstream binary's port-80 file cap
# so it can execute with the existing drop-ALL container capability policy.
RUN setcap -r /usr/bin/caddy
COPY Caddyfile /etc/caddy/Caddyfile
COPY dist /srv
