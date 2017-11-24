# Desription
Middleware script for [Munki](https://github.com/munki/munki) designed to work in hybrid solution with nginx cache-proxy and AWS S3.

# Credits
Check the article in Munki wiki about [Middleware](https://github.com/munki/munki/wiki/Middleware).  
Check the article in waderobson/s3-auth [repo](https://github.com/waderobson/s3-auth/wiki). He is the author of original script. Many thanks for his work.
Check Rick Heil's [talk](http://rickheil.com/munkipsu2017/) at MacAdmins 2017 to learn more about hybrid setup. Many thanks for his speech.

# How it works
The script tries to resolve the name of your local munki proxy-cache server. If it can, it considers that your are in LAN and rewrites URL to your local munki proxy-cache. If it can't resolve the name, the default configuration for S3 proceeded.

# How to setup
Perform all setup according to this [article](https://github.com/waderobson/s3-auth/wiki)
and add S3RewriteEndpoint to ManagedInstalls.plist  
```
sudo defaults write /Library/Preferences/ManagedInstalls S3RewriteEndpoint  my-munki.mycorp.com
```
