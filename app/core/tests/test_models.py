# tests for models
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email="user@example.com", password="password123"):
    """Create and return e new user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    # check what this test doing
    def test_create_user_with_email_successful(self):
        email = "test@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEquals(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'password123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "password123")

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            "test@example.com",
            "test123"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_playlist(self):
        # test if creating playlist is successful
        user = get_user_model().objects.create_user(
            "test@example.com",
            "test123"
        )
        playlist = models.Playlist.objects.create(
            user=user,
            title='Sample playlist name',
            time_minutes=5,
            general_genre="Sample genre",
            description="Sample playlist description",
        )

        self.assertEqual(str(playlist), playlist.title)

    def test_create_tag(self):
        """Test creating a tag is successful."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Tag1")

        self.assertEqual(str(tag), tag.name)

    def test_create_song(self):
        """Test creating song is successful"""
        user = create_user()
        song = models.Song.objects.create(
            user=user,
            name="Song1",
            artist="Artist1"
        )

        self.assertEqual(str(song), song.name)

    @patch('core.models.uuid.uuid4')
    def test_playlist_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.playlist_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/playlist/{uuid}.jpg')
