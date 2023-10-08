# Serializer for playlist API

from rest_framework import serializers
from core.models import Playlist, Tag


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


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]
