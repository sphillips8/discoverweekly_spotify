# Custom Discover Weekly Playlist
Adds new tracks from list of playlists to user's playlist on Spotify

# Getting Authorization
Follow the instructions on https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app to set up an application and receive personal client ID and client secret

# Setting up config.cfg
In your config.cfg file, input your personal client ID, client secret, and the redirect URI you specified in the 'Getting authorization section'.
<br/>Input your spotify username in the USERNAME spot.
<br/>Insert the link for your personal Discover Weekly playlist and an archive playlist for overflow songs 

# Setting up config.json
In your config.json file, input your client ID, client secret, and redirect URI.

# Setting up playlists.txt
Add playlists with the following format: 
<br/>&nbsp;&nbsp;&nbsp;playlist name: link to playlist
<br/>Every playlist should be added on their own line. You may comment out the playlist by starting the line with '!'. 
<br/>You may name the playlist whatever you would like, but please give them all unique names. The naming convention you use in playlists.txt is how they will appear in your statistics report. 
