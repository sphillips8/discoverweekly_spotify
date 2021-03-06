# Custom Discover Weekly Playlist
Adds new tracks from list of playlists to user's playlist on Spotify

# Getting Authorization
Follow the instructions on https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app to set up an application and receive personal client ID and client secret
<br/> Set website = http://localhost:8888
<br/> Set callback URI = http://localhost:8888/callback/

# Setting up config.json
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;In your config.json file, input the relevant information. 
<br/>Gather your client ID and client secret from your application dashboard from https://developer.spotify.com/dashboard/login
<br/>Your redirect URI should be http://localhost:8888/callback/
<br/>Your scope should be 'user-library-read playlist-modify-public playlist-modify-private user-read-currently-playing user-modify-playback-state'
<br/>Input your Spotify username for spotify_username
<br/>Input the links for your new Discover Weekly playlist and your archive playlist for rollover songs in their respective positions
<br/>Input the email address you would like to use to send the emails for email_sender_address (Note: Must be a Gmail email address)
<br/>Input the password for the above email address for email_sender_password
<br/>Input a receiving email address for email_receiver_address (May be a Gmail or alternative email address)

# Setting up Gmail compatibility with smtplib
The code is currently set up to send emails using a Gmail email address. In order for this to work you need to enable "Allow less secure apps" option in your gmail account configuration. Otherwise you will get a "critical security alert" when gmail detects that a non-Google apps is trying to login your account. It is recommended you create a new email address, since you will be lowering your security by allowing less secure apps to access your account information.

# Setting up playlists.txt
Add playlists with the following format: 
<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;playlist name: link to playlist
<br/>Every playlist should be added on their own line. You may comment out the playlist by starting the line with '!'. 
<br/>You may name the playlist whatever you would like, but please give them all unique names. The naming convention you use in playlists.txt is how they will appear in your statistics report. 
