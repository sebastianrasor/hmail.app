#!/bin/sh

read query_string
email="$(printf "$(echo "$query_string" | awk -F '&' '{print $1}' | sed -En "s/email=(.+)/\1/p" | sed -E 's/%(..)/\\x\1\\000/g')")"
user="$(echo "$email" | awk -F '@' '{print $1}' | LC_CTYPE="en_US.UTF-8" idn2 -T --quiet)"
domain="$(echo "$email" | awk -F '@' '{print $NF}' | LC_CTYPE="en_US.UTF-8" idn2 -T --quiet)"
old_password="$(printf "$(echo "$query_string" | awk -F '&' '{print $2}' | sed -En "s/old-password=(.+)/\1/p" | sed -E 's/%(..)/\\x\1\\000/g')")"
password="$(printf "$(echo "$query_string" | awk -F '&' '{print $3}' | sed -En "s/password=(.+)/\1/p" | sed -E 's/%(..)/\\x\1\\000/g')")"
confirm_password="$(printf "$(echo "$query_string" | awk -F '&' '{print $4}' | sed -En "s/confirm-password=(.+)/\1/p" | sed -E 's/%(..)/\\x\1\\000/g')")"

echo "Content-type: text/html\n"
echo "<!doctype html>"
echo "<html lang=\"en\">"
echo "<meta charset=\"utf-8\">"
echo "<link rel=\"stylesheet\" href=\"/styles.css\">"
echo "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
if [ -z "$password" ]; then
	echo "<title>Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Please enter a password.</p>"
	echo "<button type='button' onclick=\"location.href='/password.html?email=$email'\">Go Back</button>"
	echo "</form>"
elif [ -z "$confirm_password" ]; then
	echo "<title>Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Please confirm your desired password.</p>"
	echo "<button type='button' onclick=\"location.href='/password.html?email=$email'\">Go Back</button>"
	echo "</form>"
elif [ "$password" != "$confirm_password" ]; then
	echo "<title>Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Passwords do not match.</p>"
	echo "<button type='button' onclick=\"location.href='/password.html?email=$email'\">Go Back</button>"
	echo "</form>"
elif ! echo "$old_password" | checkpass "$(sqlite3 /vmail/_users.sqlite "SELECT password FROM users WHERE user='$user' AND domain='$domain'")"; then
	echo "<title>Error</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Invalid email/password combination."
	echo "<button type='button' onclick=\"location.href='/password.html?email=$email'\">Go Back</button>"
	echo "</form>"
else
	sqlite3 /vmail/_users.sqlite "UPDATE users SET password='$(echo "$password" | encrypt -b 14)' WHERE user='$user' AND domain='$domain'"
	echo "<title>Password Changed</title>"
	echo "<form>"
	echo "<p style=\"text-align:center;\">Your password has been changed."
	echo "<button type='button' onclick=\"location.href='/'\">Go Home</button>"
	echo "</form>"
fi
