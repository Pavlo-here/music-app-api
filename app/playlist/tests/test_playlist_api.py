# test playlist api
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Playlist

from playlist.serializers import (
    PlaylistSerializer,
    PlaylistDetailSerializer,
)

PLAYLIST_URL = reverse("playlist:playlist-list")


def detail_url(playlist_id):
    # creating and return a playlist detail URL.
    return reverse("playlist:playlist-detail", args=[playlist_id])


def create_playlist(user, **params):
    # create and return sample playlist
    defaults = {
        "title": 'Sample playlist name',
        "time_minutes": 5,
        "general_genre": "Sample genre",
        "description": "Sample playlist description",
        "link": "googlelink",
    }
    defaults.update(params)

    playlist = Playlist.objects.create(user=user, **defaults)
    return playlist


class PublicPlaylistAPITests(TestCase):
    # test for unauthenticated api requests
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        # test auth required to call API
        res = self.client.get(PLAYLIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePlaylistAPITest(TestCase):
    # test for authenticated API requests
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com",
            "password123"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_playlists(self):
        # test retrieving playlists for auth user
        create_playlist(self.user)
        create_playlist(self.user)

        res = self.client.get(PLAYLIST_URL)

        playlists = Playlist.objects.all().order_by("-id")
        serializer = PlaylistSerializer(playlists, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_playlist_list_limited_to_user(self):
        # test list of playlists is limited to auth user
        other_user = get_user_model().objects.create_user(
            "other@example.com",
            "password123"
        )
        create_playlist(other_user)
        create_playlist(self.user)

        res = self.client.get(PLAYLIST_URL)

        playlists = Playlist.objects.filter(user=self.user)
        serializers = PlaylistSerializer(playlists, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(res.data, serializers.data)

    def test_get_playlist_detail(self):
        """Test get playlist detail."""
        playlist = create_playlist(user=self.user)

        url = detail_url(playlist.id)
        res = self.client.get(url)

        serializer = PlaylistDetailSerializer(playlist)
        self.assertEqual(res.data, serializer.data)

    def test_create_playlist(self):
        # test creating a playlist
        payload = {
            "title": "sample recipe",
            "time_minutes": 30,
            "general_genre": "rock"
        }
        res = self.client.post(PLAYLIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        playlist = Playlist.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(playlist, k), v)
        self.assertEqual(playlist.user, self.user)

