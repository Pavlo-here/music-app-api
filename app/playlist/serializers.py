# Serializer for playlist API

from rest_framework import serializers
from core.models import Playlist


class PlaylistSerializer(serializers.ModelSerializer):
    # serializer for playlists
    class Meta:
        model = Playlist
        fields = ["id", "title", "time_minutes", "general_genre", "link"]
        read_only_fields = ["id"]


class PlaylistDetailSerializer(PlaylistSerializer):
    """Serializer for playlist detail view."""

    class Meta(PlaylistSerializer.Meta):
        fields = PlaylistSerializer.Meta.fields + ['description']
