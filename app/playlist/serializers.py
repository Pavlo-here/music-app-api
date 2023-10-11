# Serializer for playlist API

from rest_framework import serializers
from core.models import Playlist, Tag, Song


class SongSerializer(serializers.ModelSerializer):
    """Serializer for songs."""

    class Meta:
        model = Song
        fields = ["id", "name", "artist"]
        read_only_fields = ["id"]


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class PlaylistSerializer(serializers.ModelSerializer):
    # serializer for playlists
    tags = TagSerializer(many=True, required=False)
    songs = SongSerializer(many=True, required=False)

    class Meta:
        model = Playlist
        fields = ["id", "title", "time_minutes", "general_genre",
                  "link", "tags", "songs"]
        read_only_fields = ["id"]

    def _get_or_create_tags(self, tags, playlist):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            playlist.tags.add(tag_obj)

    def _get_or_crete_songs(self, songs, playlist):
        """Handle getting or creating songs as needed."""
        auth_user = self.context["request"].user
        for song in songs:
            song_obj, create = Song.objects.get_or_create(
                user=auth_user,
                **song,
            )
            playlist.songs.add(song_obj)

    def create(self, validated_data):
        """Create a playlist."""
        tags = validated_data.pop("tags", [])
        songs = validated_data.pop("songs", [])
        playlist = Playlist.objects.create(**validated_data)
        self._get_or_create_tags(tags, playlist)
        self._get_or_crete_songs(songs, playlist)

        return playlist

    def update(self, instance, validated_data):
        """Update playlist"""
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class PlaylistDetailSerializer(PlaylistSerializer):
    """Serializer for playlist detail view."""

    class Meta(PlaylistSerializer.Meta):
        fields = PlaylistSerializer.Meta.fields + ['description']
