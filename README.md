# A simple Python script and a systemd service for dynamically updating IP address for CloudFlare domain names.

1. Place the Python script to somewhere you recognize.
2. Modify the `update-cloudflare-dns.service` accordingly.
 - The lines `Requires=network.target`, `After=network.target` and `WantedBy=multi-user.target` must be removed to run the service at the user-level.
 - On the contrary, `WantedBy=default.target` must be removed to run the service at the system-level.
 - Be sure to modify the values of environment variables `CLOUDFLARE_EMAIL`, `CLOUDFLARE_KEY` and `CLOUDFLARE_TARGET` to your e-mail address used for logging in to CloudFlare, your global API key and comma-separated list of domains to update, respectively.
 - Finally, modify the path to the Python script.
3. Place `update-cloudflare-dns.service` and `update-cloudflare-dns.timer` at the appropriate location and install them.
 - Place at `/etc/systemd/system/` to run at the system-level and install using `systemctl enable update-cloudflare-dns.{service,timer}`.
 - Place at `$HOME/.config/systemd/user` to run at the user-level and install using `systemctl enable --user update-cloudflare-dns.{service,timer}`.
4. Check for errors.

TODO: multiple interfaces