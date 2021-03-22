#!/bin/sh

read query_string
email="$(printf "$(echo "$query_string" | awk -F '&' '{print $1}' | sed -En "s/email=(.+)/\1/p" | sed -E 's/%(..)/\\x\1\\000/g')")"
user="$(echo "$email" | awk -F '@' '{print $1}' | LC_CTYPE="en_US.UTF-8" idn2 -T --quiet)"
domain="$(echo "$email" | awk -F '@' '{print $NF}' | LC_CTYPE="en_US.UTF-8" idn2 -T --quiet 2>&1)"
password="$(printf "$(echo "$query_string" | awk -F '&' '{print $2}' | sed -En "s/password=(.+)/\1/p" | sed -E 's/%(..)/\\x\1\\000/g')")"
confirm_password="$(printf "$(echo "$query_string" | awk -F '&' '{print $3}' | sed -En "s/confirm-password=(.+)/\1/p" | sed -E 's/%(..)/\\x\1\\000/g')")"
mx="$(dig @127.0.0.1 $domain MX +short 2>/dev/null | tr -d '\n')"

echo "Content-type: text/html\n"
echo "<!doctype html>"
echo "<html lang=\"en\">"
echo "<meta charset=\"utf-8\">"
echo "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
echo "<link rel=\"stylesheet\" href=\"/styles.css\">"
if [ -z "$password" ]; then
	echo "<title>Registration Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Please enter a password.</p>"
	echo "<button type='button' onclick=\"location.href='/register.html?email=$email'\">Go Back</button>"
	echo "</form>"
elif [ -z "$confirm_password" ]; then
	echo "<title>Registration Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Please confirm your desired password.</p>"
	echo "<button type='button' onclick=\"location.href='/register.html?email=$email'\">Go Back</button>"
	echo "</form>"
elif [ "$password" != "$confirm_password" ]; then
	echo "<title>Registration Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Passwords do not match.</p>"
	echo "<button type='button' onclick=\"location.href='/register.html?email=$email'\">Go Back</button>"
	echo "</form>"
elif ! [ "$(echo "$email" | awk -F '@' '{print NF-1}')" -eq "1" ]; then
	echo "<title>Registration Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Invalid email address.</p>"
	echo "<button type='button' onclick=\"location.href='/register.html?email=$email'\">Go Back</button>"
	echo "</form>"
elif [ -z "$(echo "$user" | grep -E '^[[:alnum:]][[:alnum:]\.-]*[[:alnum:]]$|^[[:alnum:]]$')" ]; then
	echo "<title>Registration Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Usernames are restricted to alphanumeric characters plus non-repeating periods or dashes.</p>"
	echo "<button type='button' onclick=\"location.href='/register.html?email=$email'\">Go Back</button>"
	echo "</form>"
elif [ -n "$(echo "$user" | grep -E '[\.-]{2,}')" ]; then
	echo "<title>Registration Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Usernames are restricted to alphanumeric characters plus non-repeating periods or dashes.</p>"
	echo "<button type='button' onclick=\"location.href='/register.html?email=$email'\">Go Back</button>"
	echo "</form>"
elif [ -n "$(sqlite3 /vmail/_users.sqlite "SELECT user||'@'||domain FROM users WHERE user='$user' AND domain='$domain'")" ]; then
	echo "<title>Registration Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">User already exists.</p>"
	echo "<button type='button' onclick=\"location.href='/register.html?email=$email'\">Go Back</button>"
	echo "</form>"
elif [ -z "$(echo "$mx" | grep -E "^[[:digit:]]+[[:blank:]]+hmail\.app\.$")" ]; then
	echo "<title>Registration Error</title>"
	echo "<form>"
	echo "<p>Invalid MX record, please make sure your MX record at $domain. is set to:</p>"
	echo "<code>0 hmail.app.</code>"
	echo "<p><a href='https://namebase.io/next/domain-manager/$domain/records?records=$(cat <<EOF | base64
[
	{
		"type": "MX",
		"host": "@",
		"value": "0 hmail.app.",
		"ttl": 3600
	},
	{
		"type": "TXT",
		"host": "@",
		"value": "v=spf1 include:hmail.app",
		"ttl": 3600
	},
	{
		"type": "TXT",
		"host": "_hmail._auth",
		"value": "$user",
		"ttl": 3600
	},
	{
		"type": "CNAME",
		"host": "autoconfig",
		"value": "autoconfig.hmail.app",
		"ttl": 3600
	}
]
EOF
)&redirect=https://hmail.app/register.html?email=$email'>Use Namebase? Set up your records instantly!</a>"
	echo "<button style=\"margin-top:20px\" type='button' onclick=\"location.href='/register.html?email=$email'\">Go Back</button>"
	echo "</form>"
elif [ -z "$(dig @127.0.0.1 $domain TXT +short | grep -E "^\"?v=spf1[[:blank:]]+include:hmail.app\"?$")" ]; then
	echo "<title>Registration Error</title>"
	echo "<form>"
	echo "<p>Invalid SPF record, please make sure that you have a TXT record at $domain. set to:</p>"
	echo "<code>"v=spf1 include:hmail.app"</code>"
	echo "<p><a href='https://namebase.io/next/domain-manager/$domain/records?records=$(cat <<EOF | base64
[
	{
		"type": "MX",
		"host": "@",
		"value": "0 hmail.app.",
		"ttl": 3600
	},
	{
		"type": "TXT",
		"host": "@",
		"value": "v=spf1 include:hmail.app",
		"ttl": 3600
	},
	{
		"type": "TXT",
		"host": "_hmail._auth",
		"value": "$user",
		"ttl": 3600
	},
	{
		"type": "CNAME",
		"host": "autoconfig",
		"value": "autoconfig.hmail.app",
		"ttl": 3600
	}
]
EOF
)&redirect=https://hmail.app/register.html?email=$email'>Use Namebase? Set up your records instantly!</a>"
	echo "<button style=\"margin-top:20px\" type='button' onclick=\"location.href='/register.html?email=$email'\">Go Back</button>"
elif [ -z "$(dig @127.0.0.1 _hmail._auth.$domain TXT +short | grep -E "^\"?$user\"?$")" ]; then
	echo "<title>Registration Error</title>"
	echo "<form>"
	echo "<p>You need to authenticate the creation of $email, you can do that by creating a record at <code>_hmail._auth.$domain</code> with the data:"
	echo "<code>\"$user\"</code>"
	echo "<p>Once your account has been created, you can delete this record."
	echo "<p><a href='https://namebase.io/next/domain-manager/$domain/records?records=$(cat <<EOF | base64
[
	{
		"type": "MX",
		"host": "@",
		"value": "0 hmail.app.",
		"ttl": 3600
	},
	{
		"type": "TXT",
		"host": "@",
		"value": "v=spf1 include:hmail.app",
		"ttl": 3600
	},
	{
		"type": "TXT",
		"host": "_hmail._auth",
		"value": "$user",
		"ttl": 3600
	},
	{
		"type": "CNAME",
		"host": "autoconfig",
		"value": "autoconfig.hmail.app",
		"ttl": 3600
	}
]
EOF
)&redirect=https://hmail.app/register.html?email=$email'>Use Namebase? Set up your records instantly!</a>"
	echo "<button type='button' onclick=\"location.href='/register.html?email=$email'\">Go Back</button>"
else
	sqlite3 /vmail/_users.sqlite "INSERT INTO users VALUES('$user','$domain','$(echo $password | encrypt -b 14)',date('now','+7 day'))"
	hsd_id="email_$(sqlite3 /vmail/_users.sqlite "SELECT ROWID FROM users WHERE user='$user' AND domain='$domain'")"
	node /hsd/bin/hsw-cli account create "$hsd_id" >/dev/null
	cat <<EOF
<title>Account created!</title>
<div class="centered">
<h1>Your account has been created!</h1>
<p>You should delete the _hmail._auth record now.
<p>You can now log in to your Hmail account by filling the following details into your preferred mail client:
<p>IMAPS:
<p>Server: <code>hmail.app</code>
<p>Port: <code>993</code>
<p>Connection: SSL/TLS
<p>Authentication: PLAIN
<br>
<p>SMTPS:
<p>Server: <code>hmail.app</code>
<p>Port: <code>465</code>
<p>Connection SSL/TLS
<p>Authentication: PLAIN
<br>
<p>Your username for each server is your email address, and your password is the one that you selected.
<p>Your account will expire in 1 week, be sure to fund your account before then!
</div>
EOF
fi
