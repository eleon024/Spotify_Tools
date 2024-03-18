import streamlit as st
import pandas as pd
import spotipy
import random
from spotipy.oauth2 import SpotifyClientCredentials
from pyvis import network as net
import networkx as nx
from pathlib import Path
import streamlit.components.v1 as components


client_credentials_manager = SpotifyClientCredentials(client_id=st.secrets["CLIENT_ID"], client_secret=st.secrets["CLIENT_SECRET"])
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def extract_tracks_from_playlist(playlist_id):
    tracks = []
    offset = 0
    limit = 100  # Number of tracks to retrieve per request

    while True:
        results = sp.playlist_tracks(playlist_id, offset=offset, limit=limit)
        if not results['items']:
            break  # No more tracks to fetch

        for item in results['items']:
          try:
             track = item['track']
             artists = [{'name': artist['name']} for artist in track['artists']]
             tracks.append({'name': track['name'], 'artists': artists})
          except:
             pass

        offset += limit

    return tracks


def compare_music_taste(user1_tracks, user2_tracks):
    global user1_artists
    global user2_artists
    user1_artists = set(artist['name'] for track in user1_tracks for artist in track['artists'])
    user2_artists = set(artist['name'] for track in user2_tracks for artist in track['artists'])

    common_artists = user1_artists.intersection(user2_artists)

    return list(common_artists)

def get_song_count(user_tracks, artist_name):
    count = 0

    for track in user_tracks:
        for artist in track['artists']:
            if artist['name'] == artist_name:
                count += 1

    return count

def get_audio_features_df(playlist, spotipy_client):

    # Create an empty dataframe
    playlist_features_list = ["artist", "album", "track_name", "track_id","danceability","energy","key","loudness","mode", "speechiness","instrumentalness","liveness","valence","tempo", "duration_ms","time_signature"]
    playlist_df = pd.DataFrame(columns = playlist_features_list)

    # Loop through every track in the playlist, extract features and append the features to the playlist df
    for track in playlist["items"]:
        # Create empty dict
        playlist_features = {}
        # Get metadata
        playlist_features["artist"] = track["track"]["album"]["artists"][0]["name"]
        playlist_features["album"] = track["track"]["album"]["name"]
        playlist_features["track_name"] = track["track"]["name"]
        playlist_features["track_id"] = track["track"]["id"]

        # Get audio features
        audio_features = spotipy_client.audio_features(playlist_features["track_id"])[0]
        for feature in playlist_features_list[4:]:
            playlist_features[feature] = audio_features[feature]

        # Concat the DataFrames
        track_df = pd.DataFrame(playlist_features, index = [0])
        playlist_df = pd.concat([playlist_df, track_df], ignore_index = True)

    return playlist_df

def analyze_playlist(creator, playlist_id, spotipy_client):
    playlist_features_list = ["artist", "album", "track_name", "track_id",
                             "danceability", "energy", "key", "loudness", "mode", "speechiness",
                             "instrumentalness", "liveness", "valence", "tempo", "duration_ms", "time_signature"]
    playlist_df = pd.DataFrame(columns=playlist_features_list)

    playlist_features = {}

    playlist = spotipy_client.user_playlist_tracks(creator, playlist_id)["items"]
    for track in playlist:
        playlist_features["artist"] = track["track"]["album"]["artists"][0]["name"]
        playlist_features["album"] = track["track"]["album"]["name"]
        playlist_features["track_name"] = track["track"]["name"]
        playlist_features["track_id"] = track["track"]["id"]

        audio_features = spotipy_client.audio_features(playlist_features["track_id"])[0]
        for feature in playlist_features_list[4:]:
            playlist_features[feature] = audio_features[feature]

        track_df = pd.DataFrame(playlist_features, index=[0])
        playlist_df = pd.concat([playlist_df, track_df], ignore_index=True)

    return playlist_df

def analyze_playlist_dict(playlist_dict, spotipy_client):
    for i, (key, val) in enumerate(playlist_dict.items()):
        playlist_df = analyze_playlist(*val, spotipy_client=spotipy_client)
        playlist_df["playlist"] = key

        if i == 0:
            playlist_dict_df = playlist_df
        else:
            playlist_dict_df = pd.concat([playlist_dict_df, playlist_df], ignore_index=True)

    return playlist_dict_df

def get_all_user_tracks(username, spotipy_client):
    all_my_playlists = pd.DataFrame(spotipy_client.user_playlists(username))
    list_of_dataframes = []

    for playlist in all_my_playlists.index:
        current_playlist = pd.DataFrame(spotipy_client.user_playlist_tracks(username, all_my_playlists["items"][playlist]["id"]))
        current_playlist_audio = get_audio_features_df(current_playlist, spotipy_client)
        if all_my_playlists["items"][playlist]["name"]:
            current_playlist_audio["playlist_name"] = all_my_playlists["items"][playlist]["name"]
        else:
            current_playlist_audio["playlist_name"] = None
        list_of_dataframes.append(current_playlist_audio)

    return pd.concat(list_of_dataframes)

def createRadarElement(row, feature_cols):
    return go.Scatterpolar(
        r = row[feature_cols].values.tolist(),
        theta = feature_cols,
        mode = 'lines',
        name = row['track_name'])

def get_radar_plot(playlist_id, features_list, spotipy_client):
    current_playlist_audio_df = get_audio_features_df(pd.DataFrame(spotipy_client.playlist_items(playlist_id)))
    current_data = list(current_playlist_audio_df.apply(createRadarElement, axis=1, args=(features_list, )))
    fig = go.Figure(current_data, )
    fig.show(renderer='iframe')
    fig.write_image(playlist_id + '.png', width=1200, height=800)

def get_radar_plots(playlist_id_list, features_list):
    for item in playlist_id_list:
        get_radar_plot(item, features_list)


# Define the menu options
menu_options = ["Home", "Visualize Common Artists Between You and a Friend","Analyze Playlists"]

selected_option = st.sidebar.selectbox("Menu", menu_options, index=0)
st.session_state['current_page'] = selected_option

# Display the selected option content
if st.session_state['current_page'] == "Visualize Common Artists Between You and a Friend":
    st.title("Visualize Common Artists Between You and a Friend")
    first_username = st.text_input("Enter your spotify username")
    second_username = st.text_input("Enter your friend's spotify username")
    if first_username and second_username:
        playlists_user1 = sp.user_playlists(first_username)
        playlists_user2 = sp.user_playlists(second_username)
        user1_tracks = []
        for playlist in playlists_user1['items']:
            playlist_id = playlist['id']
            tracks = extract_tracks_from_playlist(playlist_id)
            user1_tracks.extend(tracks)

        # User 2: Extract tracks from their playlists
        user2_tracks = []
        for playlist in playlists_user2['items']:
            playlist_id = playlist['id']
            tracks = extract_tracks_from_playlist(playlist_id)
            user2_tracks.extend(tracks)
        
        common_artists = compare_music_taste(user1_tracks, user2_tracks)
        st.write("Common Artists:", common_artists)
        st.write("Number of Common Artists:", len(common_artists))

        # Find mutual songs
        mutual_songs = []
        seen_songs = set()  # A set to keep track of seen songs

        for track1 in user1_tracks:
            for track2 in user2_tracks:
                # Convert artists dictionaries to tuples for comparison
                artists1 = tuple(artist['name'] for artist in track1['artists'])
                artists2 = tuple(artist['name'] for artist in track2['artists'])
                
                if track1['name'] == track2['name'] and set(artists1) == set(artists2):
                    song_id = f"{track1['name']} - {', '.join(artists1)}"
                    if song_id not in seen_songs:
                        mutual_songs.append(track1)
                        seen_songs.add(song_id)  # Use song_id as a key instead of a dictionary
        st.write("Numer of Mutual Songs in Library:", len(mutual_songs))

        for song in mutual_songs:
            artists_str = ', '.join(artist['name'] for artist in song['artists'])
            st.write(f"Mutual Song: {song['name']} by {artists_str}")


        new_width = "2000px"
        new_height = "2000px"
        
        # Inside your if block, after comparing music tastes and before initializing the PyVis network:
        G = nx.Graph()

        # Assuming you have lists or sets of user1_artists, user2_artists, and common_artists already populated
        # First, add nodes and edges for user1, user2, and their artists to the networkx graph
        G.add_node(first_username)
        G.add_node(second_username)
        for artist in common_artists:
            G.add_node(artist)
            G.add_edge(first_username, artist, color='purple')
            G.add_edge(second_username, artist, color='purple')
        for artist in user1_artists:
            G.add_node(artist)
            G.add_edge(first_username, artist, color='blue')

        for artist in user2_artists:
            G.add_node(artist)
            G.add_edge(second_username, artist, color='red')



        # Compute the positions of each node using a layout algorithm
        pos = nx.spring_layout(G)

        # Now initialize your PyVis network, this time without enabling physics:
        playlists_network = net.Network(notebook=True, width=new_width, height=new_height, bgcolor="#222222", font_color="white")
        playlists_network.toggle_physics(False)

        # Add nodes with positions from the networkx layout
        for node, position in pos.items():
            playlists_network.add_node(node, x=position[0]*10000, y=-position[1]*10000, title=node, size = 100)

        # Add edges
        for edge in G.edges(data=True):
            source, target, data = edge
            playlists_network.add_edge(source, target, color=data['color'])

        # Your existing code to save and display the network graph remains the same
        playlists_network.save_graph("similar_artists.html")




        # playlists_network = net.Network(notebook=True, width=new_width, height=new_height)
        

        # playlists_network.add_node(first_username, color="blue")
        # playlists_network.add_node(second_username, color="red")

        # # Sample common artists (replace with the actual list of common artists)
        # common_artists = compare_music_taste(user1_tracks, user2_tracks)


        # for artist in common_artists:
        #     playlists_network.add_node(artist,color = "purple")
        #     playlists_network.add_edge(first_username, artist)
        #     playlists_network.add_edge(second_username, artist)


        # for x in user1_artists:
        #     playlists_network.add_node(x, color = "blue")
        #     playlists_network.add_edge(first_username,x)

        # for x in user2_artists:
        #     playlists_network.add_node(x, color= "red")
        #     playlists_network.add_edge(second_username,x)

        # pos = nx.spring_layout(G)

        # # # # Set the layout to 'BarnesHut' and adjust other parameters as needed
        # # playlists_network.barnes_hut(gravity=-8000, central_gravity=0.01, spring_length=200, spring_strength=0.02, damping=0.09)



        # # Show the Network Graph
        # playlists_network.save_graph("similar_artists.html")




        if Path("similar_artists.html").is_file():
            # Read the HTML file
            with open("similar_artists.html", 'r', encoding='utf-8') as f:
                html_string = f.read()
            html_string = html_string + """
            <script type="text/javascript">
                window.onload = function() {
                    var container = document.getElementById('mynetwork');
                    var canvas = container.getElementsByTagName('canvas')[0];
                    if (canvas) {
                        canvas.style.width = '100%';  // Make the canvas responsive
                        canvas.style.height = '100%'; // Make the canvas responsive
                        // If you want to explicitly set size, uncomment the following lines:
                        // canvas.width = container.offsetWidth;
                        // canvas.height = container.offsetHeight;
                    }
                };
            </script>
            """

            components.html(html_string,width=int(new_width.strip("px")),height=int(new_height.strip("px")))



            
    

elif st.session_state['current_page'] == "Home":
    st.title('Spotify Visualization Tools')

elif st.session_state['current_page'] == "Analyze Playlists":
    first_username = st.text_input("Enter your spotify username").strip()
    
    
    if first_username:
        # Creating a Network with one center Node
        new_width = "1000px"
        new_height = "600px"
        playlists_network = net.Network(notebook=True, width=new_width, height = new_height)

        playlists_network.add_node(f"{first_username} Spotify", color=f"#{random.randrange(0x1000000):06x}")

        # As we want to record both playlist names and corresponding sizes, we need a Dictionary:
        user_1_playlist_dictionary = {}
        # replace "my_username" with the Spotify user ID of your choice
        user_1s_playlists = pd.DataFrame(sp.user_playlists(f"{first_username}")["items"])

        # Iterating over the playlists and recording Names and Sizes
        for i in range(len(user_1s_playlists)):
            user_1_playlist_dictionary[user_1s_playlists.loc[i]["name"]] = user_1s_playlists["tracks"][i]["total"]
            

        for index,row in user_1s_playlists.iterrows():

            # Assuming the URI format is 'spotify:playlist:{playlist_id}'
            playlist_id = row['uri'].split(':')[-1]  # Split the URI by ':' and take the last part
            

            # Get the top 3 most played songs
            playlist_tracks = sp.playlist_tracks(playlist_id)["items"]
            top_songs = [f"{track['track']['artists'][0]['name']} - {track['track']['name']}" for track in playlist_tracks[:3]]
            top_songs_str = "\n".join(top_songs)

            total_songs = user_1_playlist_dictionary[row["name"]]                
                # Add node with total number of songs and top 3 songs as hover information
            playlists_network.add_node(row["name"]   , title=f"Total Songs: {total_songs}\nTop 3 Songs:\n{top_songs_str}", value=total_songs)
            playlists_network.add_edge(f"{first_username} Spotify", row["name"]   )





        # Showing the Network Graph
        playlists_network.save_graph("playlists_diagram.html")




        if Path("playlists_diagram.html").is_file():
            # Read the HTML file
            with open("playlists_diagram.html", 'r', encoding='utf-8') as f:
                html_string = f.read()
            html_string = html_string + """
            <script type="text/javascript">
                window.onload = function() {
                    var container = document.getElementById('mynetwork');
                    var canvas = container.getElementsByTagName('canvas')[0];
                    if (canvas) {
                        canvas.style.width = '100%';  // Make the canvas responsive
                        canvas.style.height = '100%'; // Make the canvas responsive
                        // If you want to explicitly set size, uncomment the following lines:
                        // canvas.width = container.offsetWidth;
                        // canvas.height = container.offsetHeight;
                    }
                };
            </script>
            """

            components.html(html_string,width=int(new_width.strip("px")),height=int(new_height.strip("px")))



