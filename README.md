# Spotify Playlist Analysis and Visualization

This Streamlit application demonstrates the use of several Python libraries to analyze and visualize Spotify playlists. It leverages the `streamlit`, `pandas`, `spotipy`, `pyvis`, and `networkx` libraries to perform these tasks.

## Key Features

- **Extract Tracks from Playlists:** Fetch tracks from specified Spotify playlists using the Spotipy library.
- **Compare Music Taste:** Compare tracks from two users' playlists to find common artists.
- **Analyze Playlists:** Analyze audio features of tracks in playlists.
- **Visualize Playlist Networks:** Use Pyvis to visualize the network of playlists and common artists.

## Implementation Overview

1. **Spotify Client Setup:** The application uses Spotipy, a lightweight Python library for the Spotify Web API, to authenticate and interact with Spotify. It requires setting up Spotify Developer credentials (`CLIENT_ID` and `CLIENT_SECRET`).

2. **Track Extraction and Analysis:**
    - Functions are defined to extract track details from users' playlists.
    - Analyze playlists by fetching audio features for each track.
    - Compare music tastes by identifying common artists between users.

3. **Visualization:**
    - Pyvis is utilized to create interactive network visualizations of playlists and their connections to artists and other playlists.
    - Networkx is used in some parts for graph analysis (not primarily for visualization in this case).

4. **Streamlit Interface:**
    - The Streamlit app provides an interactive sidebar for navigation between different sections: Home, Visualize Common Artists, and Analyze Playlists.
    - Users can input their Spotify usernames to fetch their playlists and perform analyses or comparisons.
