#!/bin/sh

read query_string
email="$(printf "$(echo "$query_string" | awk -F '&' '{print $1}' | sed -En "s/email=(.+)/\1/p" | sed -E 's/%(..)/\\x\1\\000/g')")"
user="$(echo "$email" | awk -F '@' '{print $1}' | LC_CTYPE="en_US.UTF-8" idn2 -T --quiet)"
domain="$(echo "$email" | awk -F '@' '{print $NF}' | LC_CTYPE="en_US.UTF-8" idn2 -T --quiet)"
password="$(printf "$(echo "$query_string" | awk -F '&' '{print $2}' | sed -En "s/password=(.+)/\1/p" | sed -E 's/%(..)/\\x\1\\000/g')")"

echo "Content-type: text/html\n"
echo "<!doctype html>"
echo "<html lang=\"en\">"
echo "<meta charset=\"utf-8\">"
echo "<link rel=\"stylesheet\" href=\"/styles.css\">"
echo "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"

if ! echo "$password" | checkpass "$(sqlite3 /vmail/_users.sqlite "SELECT password FROM users WHERE user='$user' AND domain='$domain'")"; then
	echo "<title>Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Invalid username/password combination."
	echo "<button type='button' onclick=\"location.href='/pay.html?email=$email'\">Go Back</button>"
	echo "</form>"
else
	hsd_id="email_$(sqlite3 /vmail/_users.sqlite "SELECT ROWID FROM users WHERE user='$user' AND domain='$domain'")"
	if [ "$(node /hsd/bin/hsw-cli account get $hsd_id)" = "null" ]; then
		node /hsd/bin/hsw-cli account create "$hsd_id" > /dev/null
	fi
	if [ "$(node /bcoin/bin/bwallet-cli account get $hsd_id)" = "null" ]; then
		node /bcoin/bin/bwallet-cli account create "$hsd_id" > /dev/null
	fi

	cat <<EOF
<title>Fund Hmail account</title>
<div class="centered">
<p>To fund your Hmail account, send any amount of HNS to the following address:
<p><code>$(node /hsd/bin/hsw-cli rpc getaccountaddress $hsd_id)</code>
<p>You can also pay with Bitcoin by sending any amount of BTC to the following address:
<p><code>$(node /bcoin/bin/bwallet-cli rpc getaccountaddress $hsd_id)</code>
<p>Payments are accepted after 1 confirmation.
<p>Payments resulting in a non-integer number of days will be rounded DOWN. For example; \$1.00 USD will fund an account for 30 days, but \$0.99 USD will fund an account for 29 days.
<p>Payment addresses are permanently associated with your account.
</div>
EOF
fi
