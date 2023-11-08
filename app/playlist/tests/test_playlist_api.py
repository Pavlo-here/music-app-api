# test playlist api
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

import tempfile
import os

from PIL import Image

from core.models import (
    Playlist,
    Tag,
    Song,
)

from playlist.serializers import (
    PlaylistSerializer,
    PlaylistDetailSerializer,
)

PLAYLIST_URL = reverse("playlist:playlist-list")


def detail_url(playlist_id):
    # creating and return a playlist detail URL.
    return reverse("playlist:playlist-detail", args=[playlist_id])


def image_upload_url(playlist_id):
    """Create and return image upload url"""
    return reverse("playlist:playlist-upload-image", args=[playlist_id])


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


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


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
        self.user = create_user(email='user@example.com', password='test123')
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
        other_user = create_user(email='other@example.com', password='test123')
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
            "title": "sample playlist",
            "time_minutes": 30,
            "general_genre": "rock"
        }
        res = self.client.post(PLAYLIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        playlist = Playlist.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(playlist, k), v)
        self.assertEqual(playlist.user, self.user)

    def test_partial_update(self):
        """Test partial update of a playlist."""
        original_link = 'googlelink'
        playlist = create_playlist(
            user=self.user,
            title='Sample playlist title',
            link=original_link,
        )

        payload = {'title': 'New playlist title'}
        url = detail_url(playlist.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        playlist.refresh_from_db()
        self.assertEqual(playlist.title, payload['title'])
        self.assertEqual(playlist.link, original_link)
        self.assertEqual(playlist.user, self.user)

    def test_full_update(self):
        """Test full update of playlist."""
        playlist = create_playlist(
            user=self.user,
            title='Sample playlist title',
            link='googlelink',
            description='Sample playlist description.',
        )

        payload = {
            'title': 'New playlist title',
            'link': 'https://example.com/new-playlist.pdf',
            'description': 'New playlist description',
            'time_minutes': 10,
            'general_genre': "rock",
        }
        url = detail_url(playlist.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        playlist.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(playlist, k), v)
        self.assertEqual(playlist.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the playlist user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        playlist = create_playlist(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(playlist.id)
        self.client.patch(url, payload)

        playlist.refresh_from_db()
        self.assertEqual(playlist.user, self.user)

    def test_delete_playlist(self):
        """Test deleting a playlist successful."""
        playlist = create_playlist(user=self.user)

        url = detail_url(playlist.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Playlist.objects.filter(id=playlist.id).exists())

    def test_playlist_other_users_playlist_error(self):
        """Test trying to delete another users playlist gives error."""
        new_user = create_user(email='user2@example.com', password='test123')
        playlist = create_playlist(user=new_user)

        url = detail_url(playlist.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Playlist.objects.filter(id=playlist.id).exists())

    def test_create_playlist_with_new_tags(self):
        """Test creating playlist with new tags"""
        payload = {
            "title": "Soft and gazing metal",
            "time_minutes": 20,
            "general_genre": "Prog Rock/Art Rock",
            "tags": [{"name": "Metal"}, {"name": "Emotional"}]
        }
        res = self.client.post(PLAYLIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        playlists = Playlist.objects.filter(user=self.user)
        self.assertEqual(playlists.count(), 1)
        playlist = playlists[0]
        self.assertEqual(playlist.tags.count(), 2)
        for tag in payload["tags"]:
            exists = playlist.tags.filter(
                name=tag["name"],
                user=self.user,
            )
            self.assertTrue(exists)

    def test_create_playlist_with_existing_tags(self):
        """Test creating a playlist with existing tag."""
        tag_emotional = Tag.objects.create(user=self.user, name='Emotional')
        payload = {
            "title": "Soft metal",
            "time_minutes": 20,
            "general_genre": "Prog Rock/Art Rock",
            "tags": [{"name": "Metal"}, {"name": "Emotional"}]
        }
        res = self.client.post(PLAYLIST_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        playlists = Playlist.objects.filter(user=self.user)
        self.assertEqual(playlists.count(), 1)
        playlist = playlists[0]
        self.assertEqual(playlist.tags.count(), 2)
        self.assertIn(tag_emotional, playlist.tags.all())
        for tag in payload['tags']:
            exists = playlist.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test create tag when updating a playlist."""
        playlist = create_playlist(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(playlist.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, playlist.tags.all())

    def test_update_playlist_assign_tag(self):
        """Test assigning an existing tag when updating a playlist."""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        playlist = create_playlist(user=self.user)
        playlist.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Gym')
        payload = {'tags': [{'name': 'Gym'}]}
        url = detail_url(playlist.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, playlist.tags.all())
        self.assertNotIn(tag_breakfast, playlist.tags.all())

    def test_clear_playlist_tags(self):
        """Test clearing a playlists tags."""
        tag = Tag.objects.create(user=self.user, name='Workout')
        playlist = create_playlist(user=self.user)
        playlist.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(playlist.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(playlist.tags.count(), 0)

    def test_crete_playlist_with_new_songs(self):
        """Test creating a playlist with new songs."""
        payload = {
            "title": "New-Soft metal",
            "time_minutes": 17,
            "general_genre": "Prog Rock/Art Rock",
            "songs": [{"name": "The Real", "artist": "Narrow Head"},
                      {"name": "Sunday", "artist": "Narrow Head"}]
        }
        res = self.client.post(PLAYLIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        playlists = Playlist.objects.filter(user=self.user)
        self.assertEqual(playlists.count(), 1)
        playlist = playlists[0]
        self.assertEqual(playlist.songs.count(), 2)
        for song in payload["songs"]:
            exists = playlist.songs.filter(
                name=song["name"],
                artist=song["artist"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_playlist_with_existing_song(self):
        """Test creating a new playlist with existing song."""
        song = Song.objects.create(user=self.user, name='Smells',
                                   artist="Alice in Chains")
        payload = {
            'title': 'Vietnamese Soup',
            'time_minutes': 25,
            'price': '2.55',
            "songs": [{"name": "Smells", "artist": "Alice in Chains"},
                      {"name": "Breakup Song", "artist": "Narrow Head"}],
        }
        res = self.client.post(PLAYLIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        playlists = Playlist.objects.filter(user=self.user)
        self.assertEqual(playlists.count(), 1)
        playlist = playlists[0]
        self.assertEqual(playlist.songs.count(), 2)
        self.assertIn(song, playlist.songs.all())
        for song in payload['songs']:
            exists = playlist.songs.filter(
                name=song["name"],
                artist=song["artist"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_song_on_update(self):
        """Test creating a song when updating a playlist."""
        playlist = create_playlist(user=self.user)

        payload = {"songs": [{"name": "Limes", "artist": "Chilli Peppers"}]}
        url = detail_url(playlist.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_song = Song.objects.get(user=self.user, name='Limes')
        self.assertIn(new_song, playlist.songs.all())

    def test_update_playlist_assign_song(self):
        """Test assigning an existing song when updating a playlist."""
        song1 = Song.objects.create(user=self.user, name='Smells',
                                    artist="Alice in Chains")
        playlist = create_playlist(user=self.user)
        playlist.songs.add(song1)

        song2 = Song.objects.create(user=self.user, name='Chili')
        payload = {'songs': [{'name': 'Chili'}]}
        url = detail_url(playlist.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(song2, playlist.songs.all())
        self.assertNotIn(song1, playlist.songs.all())

    def test_clear_playlist_songs(self):
        """Test clearing a playlists songs."""
        song = Song.objects.create(user=self.user, name='Smells',
                                   artist="Alice in Chains")
        playlist = create_playlist(user=self.user)
        playlist.songs.add(song)

        payload = {'songs': []}
        url = detail_url(playlist.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(playlist.songs.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering playlists by tags."""
        p1 = create_playlist(user=self.user, title="Title Fight")
        p2 = create_playlist(user=self.user, title="Ramones Punk Stories")
        tag1 = Tag.objects.create(user=self.user, name="Nostalgic")
        tag2 = Tag.objects.create(user=self.user, name="Emotional")
        p1.tags.add(tag1)
        p2.tags.add(tag2)
        p3 = create_playlist(user=self.user, title="Music for gym")

        params = {"tags": f"{tag1.id}, {tag2.id}"}
        res = self.client.get(PLAYLIST_URL, params)

        s1 = PlaylistSerializer(p1)
        s2 = PlaylistSerializer(p2)
        s3 = PlaylistSerializer(p3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_songs(self):
        """Test filtering playlists by songs."""
        plist1 = create_playlist(user=self.user, title="Amyl and the Sniffers")
        plist2 = create_playlist(user=self.user, title="HipHop essentials")
        song1 = Song.objects.create(user=self.user, name="Followed by the Angels")
        song2 = Song.objects.create(user=self.user, name="Rap God")
        plist1.songs.add(song1)
        plist2.songs.add(song2)
        plist3 = create_playlist(user=self.user, title="Dance Day")

        params = {"songs": f"{song1.id},{song2.id}"}
        res = self.client.get(PLAYLIST_URL, params)

        s1 = PlaylistSerializer(plist1)
        s2 = PlaylistSerializer(plist2)
        s3 = PlaylistSerializer(plist3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

class ImageUploadTests(TestCase):
    """Tests for the image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com",
            "password123",
        )
        self.client.force_authenticate(self.user)
        self.playlist = create_playlist(user=self.user)

    def tearDown(self):
        self.playlist.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a playlist."""
        url = image_upload_url(self.playlist.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.playlist.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.playlist.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image."""
        url = image_upload_url(self.playlist.id)
        payload = {"image": "notanimage"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
