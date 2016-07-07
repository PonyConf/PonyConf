#! /bin/bash

# Usage: cat email.txt | post-mail.sh https://example.org/conversations/recv/ /etc/ponyconf/key.txt
# The file /etc/ponyconf/key.txt should contain the value of the django setting REPLY_KEY.

url="$1"
key="$2"

curl ${url} -F 'key=<${key}' -F 'file=@-;filename="email"'
