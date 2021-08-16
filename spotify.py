from datetime import datetime, timedelta
from numpy import setdiff1d
import time
import pytz
import configparser
import spotipy
import spotipy.oauth2 as oauth2
from spotipy.exceptions import SpotifyException
from pandas import DataFrame, read_csv
import smtplib, ssl


'''
                        CUSTOM DISCOVER WEEKLY PLAYLIST
'''


'''
                         Credentials and Spotipy Session
'''


# Retrieves user data from config.cfg file
config = configparser.ConfigParser()
config.read('config.cfg')
client_id = config.get('SPOTIFY', 'CLIENT_ID')
client_secret = config.get('SPOTIFY', 'CLIENT_SECRET')
redirect_uri = config.get('SPOTIFY', 'REDIRECT_URI')
scope = config.get('SPOTIFY', 'SCOPE')
username = config.get('SPOTIFY', 'USERNAME')
discover_uri = config.get('SPOTIFY', 'PLAYLIST')
archive_uri = config.get('SPOTIFY', 'ARCHIVE')
password = config.get('GOOGLE', 'PASSWORD')
sender = config.get('GOOGLE', 'SENDER')
receiver = config.get('GOOGLE', 'RECEIVER')


# Grants authorization to Spotify API
auth = oauth2.SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    username=username,
    scope=scope
)


# Gathers list of playlist URIs
playlists, playlist_name = (list() for _ in range(2))
with open('playlists.txt', 'r') as file:
    for line in file:
        pl = line.split('playlist/')[1].split('?si=')[0].strip()
        playlists.append('spotify:playlist:' + pl)
        playlist_name.append(line.split(':')[0])
playlist_dict = dict(zip(playlist_name, playlists))


# Opens Spotipy
sp = spotipy.Spotify(auth_manager=auth)


# SMTP Credentials & Message
port = 587  # For starttls
smtp_server = "smtp.gmail.com"


def email_message(reason, except_msg=None):
    if reason == 'exception':
        message = """\
        Subject: Spotify.py Failure

        Skye's Discover Weekly Playlist did not update on {}. Exception: {} \n This message is sent from 
        Python.""".format(datetime.now().date(), except_msg)
    else:  # update with diagnostics information
        message = """\
        Subject: Spotify.py Diagnostics

        Skye's Discover Weekly Playlist did not update on {}. Exception: {} \n This message is sent from 
        Python.""".format(datetime.now().date(), except_msg)
    return message


'''
                                    Functions 
'''


# Calculates time elapsed
def timer(start, end):
    hours, rem = divmod(end-start, 3600)
    minutes, seconds = divmod(rem, 60)
    time_elapsed = "{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds)
    return time_elapsed


# Converts from GMT to Eastern Timezone (local time)
def convert_gmt_eastern(time):
    gmt = pytz.timezone('GMT')
    eastern = pytz.timezone('US/Eastern')
    dategmt = gmt.localize(time)
    dateeastern = dategmt.astimezone(eastern)
    return dateeastern


# Get URI links - requires share link and URI type (playlist, artist, track)
def get_uri(link, uri_type):
    link = link.split('?si=')[0]
    if uri_type.lower() in ['playlist', 'artist', 'track']:
        uri = 'spotify:{}:'.format(uri_type.lower()) + str(link)[-22:]
    else:
        uri = ''
        print(' Invalid Type. Must choose from playlist, artist, or track')
    return uri


# Gets list of all tracks in a playlist, date_filter can either be None, 'recent' for songs modified in last week or
# 'old' for songs modified before the last week
def get_tracks(playlist_uri, date_filter=None):
    weekAgo = datetime.now().date() - timedelta(days=8)
    track_uris = list()
    results = sp.playlist_items(playlist_uri)
    tracks = results['items']
    while results['next']:  # workaround to add over 100 songs from playlist
        results = sp.next(results)
        tracks.extend(results['items'])
    for item in tracks:
        try:
            if date_filter:
                added = datetime.strptime(item['added_at'].split('T')[0], '%Y-%m-%d').date()
                if date_filter == 'recent':
                    if added >= weekAgo:
                        track_uris.append(item['track']['uri'])
                elif date_filter == 'old':
                    if added < weekAgo:
                        track_uris.append(item['track']['uri'])
            else:
                track_uris.append(item['track']['uri'])
        except TypeError:
            pass
    return track_uris


# Adds songs from track_list to playlist, discover = True for add_discover
def add_songs(playlist_to_add, track_list, discover=False, playlist_to_delete=None, replace=False):
    failed = []
    i = 0
    increment = 99
    while i < len(track_list) + increment:
        try:
            if len(track_list[i: i + increment]) > 0:
                print('--- Adding Next {} Songs to Playlist ---'.format(len(track_list[i: i + increment])))
            songs = track_list[i: i + increment]
            for song in songs:
                sp.playlist_add_items(playlist_to_add, [song])
                if discover:
                    archive = open('all_songs.txt', 'a')
                    archive.write(song + '\n')
                if replace:
                    sp.playlist_remove_all_occurrences_of_items(playlist_to_delete, [song])
            i += increment
        except spotipy.exceptions.SpotifyException:
            for song in track_list[i: i + increment]:
                failed.append(song)
                if discover:
                    failures = open('failed_songs.txt', 'a')
                    failures.write(song)
            print('--- Playlist Update Unsuccessful. {} Songs Could Not Copy Over ---'.format(len(failed)))


# Transfers Songs From Skye's Discover weekly to Discover Archived
def archive_songs(discover_pl, archive_pl):
    print('--- Archiving Songs ---')
    tracks = get_tracks(discover_pl, 'old')
    add_songs(archive_pl, tracks, False, discover_pl, True)


# Searches for new music, returns list of tracks to add, their corresponding playlists, and their playlist names
def find_new_music(playlist_dict):
    print('--- Searching Playlists for New Music ---')
    track_uri_list, playlist_list, playlist_name = (list() for _ in range(3))
    i = 0
    for playlist in list(playlist_dict.values()):
        try:
            tracks = get_tracks(playlist, 'recent')
            track_uri_list.extend(tracks)
            playlist_list.extend([playlist]*len(tracks))
            playlist_name.extend([list(playlist_dict.keys())[i]]*len(tracks))
        except SpotifyException:
            print('{} No Longer Exists'.format(playlist))
        i += 1
    return track_uri_list, playlist_list, playlist_name


# Removes duplicate songs from list of songs to add
def avoid_duplicates(playlist_dict):
    newList, playlist_list, playlist_name = find_new_music(playlist_dict)
    print('--- Filtering Songs ---')
    df = read_csv('playlists.csv')
    df2 = DataFrame({'Name': playlist_name, 'Playlist': playlist_list, 'Track': newList, 'Added': ['Pending'] *
                                                                                                  len(playlist_list)})
    all_songs = open('all_songs.txt', 'r')
    lines = [line.rstrip('\n') for line in all_songs]
    # Drop duplicate indices
    df2 = df2[~df2['Track'].isin(lines)]
    df2 = df2.drop_duplicates(subset=['Track'])
    # Appends new song information to existing data and saves as csv file
    df = df.append(df2, ignore_index=True).set_index('Name')
    df.to_csv('playlists.csv')
    return df2['Track']


# Adds songs to Skye's Discover Weekly Playlist
def add_discover(playlist_dict):
    song_list = avoid_duplicates(playlist_dict)
    print(song_list)
    with open('log.txt', 'a+') as log:
        log.write('\n{}: {} Songs Added'.format(datetime.now().date(), len(song_list)))
    print('--- Adding {} Songs to Skye\'s Discover Weekly --- '.format(len(song_list)))
    add_songs(discover_playlist, song_list, True)


'''
                            Diagnostics
'''


# Retrieve tracks from user's Spotify playlists
def get_my_tracks():
    print('--- Retrieving All Saved Songs ---')
    mytracks = []
    for i in range(len(sp.user_playlists(username)['items'])):
        playlist = get_uri(sp.user_playlists(username)['items'][i]['external_urls']['spotify'], 'playlist')
        if playlist not in [discover_uri, archive_uri]:
            mytracks.extend(get_tracks(playlist, None))
    return mytracks


# Updates playlists.csv with add/delete information
def update_csv(discover_weekly_uri):
    print('--- Preparing Diagnostics ---')
    print('--- Identifying Songs Deleted From Skye\'s Discover Weekly ---')
    # Retrieves list of songs without Add/Deleted Data
    df = read_csv('playlists.csv')
    pending = df['Track'].loc[df['Added'] == 'Pending']
    # Retrieves list of songs currently in Skye's Discover Weekly Playlist (not listened to yet)
    discover_tracks = get_tracks(discover_weekly_uri, None)
    # Retrieves songs removed from Discover Weekly
    deleted = setdiff1d(pending, discover_tracks)
    # Retrieves list of all user's Spotify playlists
    mytracks = get_my_tracks()
    for song in deleted:
        if song in mytracks:
            df['Added'].loc[df['Track'] == song] = 'Added'
        else:
            df['Added'].loc[df['Track'] == song] = 'Deleted'
    print('--- Updating playlists.csv ---')
    df = df.set_index('Name')
    df.to_csv('playlists.csv')


# Prints diagnostics reports (in progress)
def get_diagnostics():
    print('--- Getting Report ---')
    df = read_csv('playlists.csv')
    print('--- Value Counts --- ')
    print(df['Name'].value_counts().to_frame())
    # Add Percentage of Hits, Misses, Top Added, Top Removed, Top Added, Least Added
    # Style & Email Report


'''
                Sets Discover and Archive Playlists
'''

discover_playlist = get_uri(discover_uri, 'playlist')
archive_playlist = get_uri(archive_uri, 'playlist')


'''
                            Main
'''


# Runs Monday morning routine
def discoverWeekly():
    start_time = time.time()  # starts timer
    archive_songs(discover_playlist, archive_playlist)  # archives songs
    update_csv(discover_playlist)  # updates csv with add/delete information
    get_diagnostics()  # gets updated diagnostics
    try:
        add_discover(playlist_dict)  # adds songs that have been added within the last 7 days
    except Exception as e:  # emails error message upon failures
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls(context=context)
            server.login(sender, password)
            server.sendmail(sender, receiver, email_message('exception', e))
    end_time = time.time()  # ends timer
    print('--- Playlist Update Complete. Runtime: {} --- '.format(timer(start_time, end_time)))  # prints time elapsed


discoverWeekly()  # archives songs, updates csv and diagnostics, adds new songs


# get_diagnostics # prints diagnostics only
