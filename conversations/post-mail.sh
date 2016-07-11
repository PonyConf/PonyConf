#! /bin/bash

# Usage: cat email.txt | post-mail.sh REPLY_KEY@https://example.org/conversations/recv/
# Get the value of REPLY_KEY from the django setting.

# Postfix users can set up an alias file with this content:
# reply: "|/path/to/post-mail.sh mykey@https://example.org/conversations/recv/
# don't forget to run postalias and to add the alias file to main.cf under alias_map.

curl ${@#*\@} -F key=${@%\@*} -F "email=@-"
