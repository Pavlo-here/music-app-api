"""
Views for the playlist APIs
"""
from rest_framework import (
    viewsets,
    mixins,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Playlist,
    Tag,
    Song,
)
from playlist import serializers


class PlaylistViewSet(viewsets.ModelViewSet):
    """View for manage playlist APIs."""
    serializer_class = serializers.PlaylistDetailSerializer
    queryset = Playlist.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve playlists for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.PlaylistSerializer
        elif self.action == 'upload_image':
            return serializers.PlaylistImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new playlist."""
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload image to playlist."""
        playlist = self.get_object()
        serializer = self.get_serializer(playlist, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BasePlaylistAttrViewSet(mixins.DestroyModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    """Base viewset of playlist attrs"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagViewSet(BasePlaylistAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class SongViewSet(BasePlaylistAttrViewSet):
    """Manage songs in the database."""
    serializer_class = serializers.SongSerializer
    queryset = Song.objects.all()
